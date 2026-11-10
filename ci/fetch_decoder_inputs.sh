#!/usr/bin/env bash
# Download the two decoder patch files the Vorbis and Opus transplants
# read, from a pinned commit of berettavexee/echo-mini-opus (BSD-3-Clause),
# and refuse them unless both SHA-256 hashes match.
#
# Usage: ci/fetch_decoder_inputs.sh NEW_DIRECTORY
#
# The files are build inputs only. Do not commit them to this repository.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 NEW_DIRECTORY" >&2
  exit 2
fi
dest=$1
if [[ -e $dest ]]; then
  echo "refusing to use existing path: $dest" >&2
  exit 1
fi

commit=7d727fd4f30e68fecbf6566d3c3e64213e56e7f7
base="https://raw.githubusercontent.com/berettavexee/echo-mini-opus/${commit}/patch"

mkdir -p "$dest"
for name in HIFIEC52 HIFIEC56; do
  curl -fsSL --retry 4 --retry-delay 2 -o "$dest/$name.ecpatch" "$base/$name.ecpatch"
done

(
  cd "$dest"
  sha256sum --check --strict <<'EOF'
acad5a624aacdceb3868a118b56959260f08ee9600ac5378d9f516e0872ccd03  HIFIEC52.ecpatch
8c31278ea9b6e730d913dbe2897ba3a126eaf156dc836a4eab09e87532903b2a  HIFIEC56.ecpatch
EOF
)
echo "Decoder inputs verified in $dest"
