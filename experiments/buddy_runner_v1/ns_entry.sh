#!/bin/sh
# BR08 proof: exec in new Linux user/mount/net/pid namespaces; no fallback.
set -eu
umask 077
root="$1"
source="$2"
output="$3"
runner="$4"
mount --make-rprivate /
mount -t tmpfs -o nosuid,nodev,size=96m tmpfs "$root"
mkdir -p "$root/usr" "$root/blind" "$root/output" "$root/tool" "$root/tmp" "$root/dev"
ln -s usr/lib "$root/lib"
ln -s usr/lib64 "$root/lib64"
mount --rbind /usr "$root/usr"
mount -o remount,bind,ro "$root/usr"
mount --bind "$source" "$root/blind"
mount -o remount,bind,ro "$root/blind"
mount --bind "$output" "$root/output"
: > "$root/tool/runner.py"
mount --bind "$runner" "$root/tool/runner.py"
mount -o remount,bind,ro "$root/tool/runner.py"
: > "$root/dev/null"
mount --bind /dev/null "$root/dev/null"
# Do not mount proc/sys/dev, or host credentials.
exec chroot "$root" /usr/bin/setpriv --no-new-privs --bounding-set=-all /usr/bin/python3 -I -B /tool/runner.py
