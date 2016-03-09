#!/usr/bin/python
#
# This is a quick hack so gfoury can try a bunch of UX305FA eDP patches

import plistlib
import plistmonkey
import argparse
import sys
import patch

parser = argparse.ArgumentParser(description="Merge clover kext patches into a master")
parser.add_argument("-s", "--short-data",
                    help="Use single-line <data> when possible",
                    action="store_true")
parser.add_argument("-n", "--normalize",
                   help="Normalize by sorting keys",
                    action="store_true")
parser.add_argument("master", help="path to master plist", nargs=1,
                    type=argparse.FileType("r"))
parser.add_argument("merge", help="plist of binary patch", nargs="+",
                    type=argparse.FileType("r"))

args = parser.parse_args()
plistmonkey.rehabManHouseStyle = args.short_data
plistmonkey.sortItems = args.normalize

pl = plistlib.readPlist(args.master[0])

# Get the array of kext patches so we can mutate it
try:
    config_patch_array = pl["KernelAndKextPatches"]["KextsToPatch"]
except KeyError as e:
    raise KeyError("config.plist file is missing KernelAndKextPatches:KextToPatch section")

assert isinstance(config_patch_array, list)

for patchfile in args.merge:
    mergelist = plistlib.readPlist(patchfile)
    # Allow both arrays and single dicts as patches
    if isinstance(mergelist, dict):
        mergelist = [mergelist]
    for merge in mergelist:
        # We don't actually need a FilePatch object, we just want the sanity check
        patch.FilePatch(merge)
        config_patch_array.append(merge)

plistlib.writePlist(pl, sys.stdout)