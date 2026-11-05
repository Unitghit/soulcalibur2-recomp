#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# shaderc for the Linux build (tools/release/linux.sh): libshaderc_shared.so.1 from LunarG's Vulkan SDK, which has
# glslang and SPIRV-Tools inside and needs only glibc 2.29 and libstdc++. The SDL_GPU presenter loads it at run time
# to compile its shaders; the program finds this one beside it ($ORIGIN) before the system's, so a distribution
# without shaderc (Debian and Ubuntu without libshaderc1, Arch without shaderc) still starts. Unpacked into
# private/toolchains/shaderc-linux. Needs curl and xz (on the Mac); the SDK is 330 MB, fetched once.
set -e
root=$(cd "$(dirname "$0")/../.." && pwd)
ver=1.4.328.1
sha=241e75b56c91c0d210ed07a7c638ec05a3e5b0e4c66ba9f0ba0f102d823ad6bf
out="$root/private/toolchains/shaderc-linux"
[ -f "$out/libshaderc_shared.so.1" ] && exit 0
tmp=$(mktemp -d)
curl -fsSL -o "$tmp/sdk.tar.xz" "https://sdk.lunarg.com/sdk/download/$ver/linux/vulkansdk-linux-x86_64-$ver.tar.xz"
echo "$sha  $tmp/sdk.tar.xz" | shasum -a 256 -c - >/dev/null
tar -xJf "$tmp/sdk.tar.xz" -C "$tmp" "$ver/x86_64/lib/libshaderc_shared.so.1"
mkdir -p "$out"
cp "$tmp/$ver/x86_64/lib/libshaderc_shared.so.1" "$out/"
rm -rf "$tmp"
echo "shaderc in $out"
