#!/usr/bin/python

import plistlib
import plistmonkey
import argparse
import sys
import os.path
import tempfile
import subprocess

parser = argparse.ArgumentParser(description="Diff two normalized property lists",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="""Unrecognized arguments are passed to diff

Example: diff -U10 config1.plist config2.plist
Example: diff config1.plist config2.plist -U 10
""")

parser.add_argument("-s", "--short-data",
                    help="Use single-line <data> when possible",
                    action="store_true")
parser.add_argument("-n", "--normalize",
                   help="Normalize by sorting keys",
                    action="store_true")
parser.add_argument("-g", "--git-diff",
                    help="Use git diff instead of diff",
                    action="store_true")
parser.add_argument("file1", help="path to first file", nargs=1,
                    type=argparse.FileType("r"))
parser.add_argument("file2", help="path to second file", nargs=1,
                    type=argparse.FileType("r"))


def basename(f):
    name = f.name
    if name == "<stdin>":
        name = "stdin"
    fn = os.path.basename(name)
    fn = fn.replace(".plist", "")
    return fn

(args, restargs) = parser.parse_known_args()

file1 = args.file1[0]
file2 = args.file2[0]
plistmonkey.sortItems = args.normalize
plistmonkey.rehabManHouseStyle = args.short_data

file1basename = basename(file1)
file2basename = basename(file2)

plist1 = plistlib.readPlist(file1)
plist2 = plistlib.readPlist(file2)


with tempfile.NamedTemporaryFile(suffix=".plist", prefix=file1basename+".") as out1:
    with tempfile.NamedTemporaryFile(suffix=".plist", prefix=file2basename+".") as out2:
        plistlib.writePlist(plist1, out1)
        out1.flush()
        plistlib.writePlist(plist2, out2)
        out2.flush()
        if args.git_diff:
            arglist = ["git", "diff", "--no-index"]
            arglist += restargs
            arglist.append("--")
        else:
            arglist = ["diff"]
            arglist.extend(restargs)
        arglist.extend([out1.name, out2.name])
        result = subprocess.call(arglist)

sys.exit(result)
