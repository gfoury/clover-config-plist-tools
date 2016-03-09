#!/bin/bash
#
# Given an existing Clover config.plist, see what additional patches would do.
#
# Originally designed for IntelBDW HDMI hacking.

test -f makebinpatch.py && echo "You probably don't want to run this in the repository's directory" && exit 1

set -e
set -x

if [[ "$(type -p cdiff)" != "" ]]; then
    CDIFF="cdiff -c always"
else
    CDIFF="cat"
fi

oldpwd="$(pwd)"

SCRIPTHOME="$(dirname "$0")"
cd "$SCRIPTHOME"
SCRIPTHOME="$(pwd)"
cd "$oldpwd"

MAKEBINPATCH="$SCRIPTHOME/makebinpatch.py"
MERGEPLIST="$SCRIPTHOME/merge-patch.py"
CHECKKEXTPATCHES="$SCRIPTHOME/check-kext-patches.py"
KEXT="AppleIntelBDWGraphicsFramebuffer"
CONFIG="config_master.plist"

test -x "$MAKEBINPATCH"
test -x "$MERGEPLIST"
test -x "$CHECKKEXTPATCHES"
test -f "$CONFIG"

XXD="xxd -c 12"

run-bdw-patch () {
    short_name="$1"
    shift
    mkdir -p "$short_name"
    (cd "$short_name" || exit 1;
     $MAKEBINPATCH -f "$KEXT" "$@" >patch.plist;
     $MERGEPLIST ../$CONFIG patch.plist >config_patched.plist;
     $CHECKKEXTPATCHES -v --ignore-kext-dupes --output-kext "$KEXT" --output-kext-after "$KEXT-after" config_patched.plist | tee patch-info;
     diff -U 5 <($XXD ../$KEXT-after) <($XXD $KEXT-after) >diff || true;
     diff -U 5 <($XXD ../$KEXT-after) <($XXD $KEXT-after) | $CDIFF | tee color-diff;
    )
}

extend-bdw-patch () {
    short_name="$1"
    shift
    (cd "$short_name" || exit 1;
     $MAKEBINPATCH -f "$KEXT" "$@" >patch2.plist;
     $MERGEPLIST ./config_patched.plist ./patch2.plist >config_patched2.plist;
     $CHECKKEXTPATCHES -v --ignore-kext-dupes --output-kext "$KEXT" --output-kext-after "$KEXT-after2" config_patched2.plist | tee patch-info2;
     diff -U 5 <($XXD ../$KEXT-after) <($XXD $KEXT-after2) >diff || true;
     diff -U 5 <($XXD ../$KEXT-after) <($XXD $KEXT-after2) | $CDIFF | tee color-diff;
    )
}



# generate an "original" BDW kext, before our other patches

$CHECKKEXTPATCHES -v --ignore-kext-dupes --output-kext "$KEXT" --output-kext-after "$KEXT-after" "$CONFIG" | tee patch-info

run-bdw-patch 105-204 -x \
	      "0105 0900 0004 0000 0110 0000" \
	      "0204 0900 0008 0000 8200 0000" \
	      "Turn 0105 into 0204"

# Note that this adds a ff to the next entry
run-bdw-patch unused-to-hdmi-term -x \
	      "ff00 0000 0100 0000 4000 0000 0000" \
	      "0204 0900 0008 0000 8200 0000 ff00" \
	      "Turn unused into 0x0204 HDMI"

run-bdw-patch lvds-to-hdmi -x \
	      "0000 0800 0200 0000 3002 0000" \
	      "0204 0900 0008 0000 8200 0000" \
	      "Change LVDS to HDMI"

run-bdw-patch move-edp-up -x \
	      "0000 0800 0200 0000 3002 0000 0105 0900 0004 0000 0110 0000" \
	      "0105 0900 0004 0000 0110 0000 0204 0900 0008 0000 8200 0000" \
	      "Overwrite LVDS with eDP, change eDP to HDMI"

# If ff00 is the list terminator, patching the first entry in the table is trouble...
run-bdw-patch 1626-disable-lvds -x \
	      "0000 0800 0200 0000 3002 0000 0105" \
	      "ff00 0800 0200 0000 3002 0000 0105" \
	      "Disable LVDS for 0x16260006"

run-bdw-patch 161e0000-disable-edp -x \
	      "010509000400000004000000" \
	      "FF0009000400000004000000" \
	      "Disable eDP on 0x161e0000"

run-bdw-patch increase-to-3-hdmi -x \
	      "0100 1E16 0102 0202 0000" \
	      "0100 1E16 0102 0303 0000" \
	      "Change 0x161e0001 connector count from 2 to 3"
extend-bdw-patch increase-to-3-hdmi -x \
	      "ff00 0000 0100 0000 4000 0000 0000" \
	      "0204 0900 0008 0000 8200 0000 ff00" \
	      "Turn unused into 0x0204 HDMI"
