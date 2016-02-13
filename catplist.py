#!/usr/bin/python

import plistlib
import plistmonkey
import argparse
import sys

parser = argparse.ArgumentParser(description="Cat (and normalize) a property list")
parser.add_argument("-s", "--short-data",
                    help="Use single-line <data> when possible",
                    action="store_true")
parser.add_argument("-n", "--normalize",
                   help="Normalize by sorting keys",
                    action="store_true")
parser.add_argument("plist", help="path to plist", nargs=1,
                    type=argparse.FileType("r"))

args = parser.parse_args()
plistmonkey.rehabManHouseStyle = args.short_data
plistmonkey.sortItems = args.normalize

pl = plistlib.readPlist(args.plist[0])

plistlib.writePlist(pl, sys.stdout)