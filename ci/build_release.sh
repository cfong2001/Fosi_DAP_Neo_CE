#!/usr/bin/env bash
# Build the CE release set from source and refuse any image whose hash
# differs from its pin.
#
# Usage:
#   ci/build_release.sh [--minimal-only] OUTPUT_DIR
#
# Environment:
#   PYTHON            interpreter with capstone, keystone-engine and unicorn
#                     (default: python3)
#   FOSI_ECPATCH_DIR  directory with HIFIEC52/HIFIEC56.ecpatch
#                     (default: fetched with ci/fetch_decoder_inputs.sh)
#
# The standard image compiles CE payloads and needs the reference toolchain
# from ci/install_reference_toolchain.sh on PATH. --minimal-only skips it and
# builds only the minimal and recovery images, which need no compiler.
#
# OUTPUT_DIR must not exist. It receives:
#   DP3_V137_CE.img                  standard image (every composed feature)
#   DP3_V137_CE.img.report.json      its build report (byte ranges summarised)
#   DP3_V137_CE_minimal.img          minimal image (stock length)
#   DP3_V137_CE_minimal.img.report.json
#   DP3_V137_CE_recovery.img         stock bytes dated after both CE images
#   SHA256SUMS
set -euo pipefail

STANDARD_SHA=8b9b1801a91a6e885c4e366c77632b08d3515d2d5578555fc5993c1689783783
MINIMAL_SHA=0dfd10e23749f9b6c65499266f1a7a2ec038160b089ba0fc2ca68dcf2b24c986
RECOVERY_SHA=aff851b31d6eee55cbd4bb3fc0464ac79f0039ee86ae6723225ac036a157d223
STOCK_SHA=fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef

standard=1
if [[ ${1:-} == --minimal-only ]]; then
  standard=0
  shift
fi
if [[ $# -ne 1 ]]; then
  echo "usage: $0 [--minimal-only] OUTPUT_DIR" >&2
  exit 2
fi
out=$1
if [[ -e $out ]]; then
  echo "refusing to use existing path: $out" >&2
  exit 1
fi

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
py=${PYTHON:-python3}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

echo "$STOCK_SHA  $repo/DP3_V137.img" | sha256sum --check --quiet

if [[ -z ${FOSI_ECPATCH_DIR:-} ]]; then
  bash "$repo/ci/fetch_decoder_inputs.sh" "$work/ecpatch"
  export FOSI_ECPATCH_DIR=$work/ecpatch
fi

pin() {
  local file=$1 want=$2 got
  got=$(sha256sum "$file" | cut -d' ' -f1)
  if [[ $got != "$want" ]]; then
    echo "::error::$(basename "$file") is $got, expected $want" >&2
    exit 1
  fi
  echo "pinned  $(basename "$file")  $got"
}

mkdir -p "$out"
build="$repo/patches/framework/build.py"

if [[ $standard == 1 ]]; then
  "$py" "$repo/patches/full/build/build_full.py" \
    --ecpatch-dir "$FOSI_ECPATCH_DIR" \
    --output "$work/standard.img" > "$work/standard.log"
  mv "$work/standard.img" "$out/DP3_V137_CE.img"
  pin "$out/DP3_V137_CE.img" "$STANDARD_SHA"
  # The growth shifts every later byte, so the full range list is about
  # 11 MB. Keep the counts and drop the list from the published copy.
  "$py" - "$work/standard.img.report.json" "$out/DP3_V137_CE.img.report.json" <<'EOF'
import json, sys
report = json.load(open(sys.argv[1]))
diff = report['diff_vs_stock']
report['diff_vs_stock'] = {
    'bytes_changed': diff['bytes_changed'],
    'range_count': len(diff['ranges']),
    'note': 'range list omitted; rebuild with patches/full/build/build_full.py for it',
}
report['input_file'] = 'DP3_V137.img'
report['output_file'] = 'DP3_V137_CE.img'
json.dump(report, open(sys.argv[2], 'w'), indent=1)
EOF
fi

"$py" "$build" --output "$out/DP3_V137_CE_minimal.img" > "$work/minimal.log"
# Keep local checkout and scratch paths out of the published report.
"$py" - "$out/DP3_V137_CE_minimal.img.report.json" <<'EOF'
import json, sys
path = sys.argv[1]
report = json.load(open(path))
report['input_file'] = 'DP3_V137.img'
report['output_file'] = 'DP3_V137_CE_minimal.img'
open(path, 'w').write(json.dumps(report, indent=2) + '\n')
EOF
pin "$out/DP3_V137_CE_minimal.img" "$MINIMAL_SHA"

"$py" "$build" --recovery --output "$out/DP3_V137_CE_recovery.img" > "$work/recovery.log"
rm -f "$out/DP3_V137_CE_recovery.img.report.json"
pin "$out/DP3_V137_CE_recovery.img" "$RECOVERY_SHA"

(cd "$out" && sha256sum -- *.img > SHA256SUMS)
echo "Release set written to $out"
