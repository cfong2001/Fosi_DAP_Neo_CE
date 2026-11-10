#!/usr/bin/env bash
# Install the exact tested cross-tools into a new, private directory.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo 'Usage: bash ci/install_reference_toolchain.sh NEW_DIRECTORY' >&2
  exit 2
fi
target=$1
if [[ -e "$target" || -L "$target" ]]; then
  echo "Destination already exists: $target" >&2
  exit 2
fi
case "$(uname -sm)" in
  'Linux x86_64') ;;
  *) echo 'This toolchain is for Linux x86_64.' >&2; exit 2 ;;
esac
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
gcc_url='https://archive.ubuntu.com/ubuntu/pool/universe/g/gcc-arm-none-eabi/gcc-arm-none-eabi_13.2.rel1-2_amd64.deb'
binutils_url='https://deb.debian.org/debian/pool/main/b/binutils-arm-none-eabi/binutils-arm-none-eabi_2.44-3%2b23%2bb1_amd64.deb'
curl --fail --location --retry 2 --output "$scratch/gcc.deb" "$gcc_url"
curl --fail --location --retry 2 --output "$scratch/binutils.deb" "$binutils_url"
printf '%s  %s\n' \
  519a5d0e5292a4b4861f69ae96e8918149bfd1646072ca53451ccfb8c5a91948 "$scratch/gcc.deb" \
  c9c4944e54de852536b4f6a238a682c38a6243cdc2843dd1c4f587e046c0615b "$scratch/binutils.deb" | sha256sum --check --status
mkdir "$target"
dpkg-deb -x "$scratch/gcc.deb" "$target"
dpkg-deb -x "$scratch/binutils.deb" "$target"
echo "Reference toolchain installed. Prepend $target/usr/bin to PATH."
