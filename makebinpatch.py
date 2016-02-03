#!/usr/bin/python2.7

import plistlib
import argparse

from io import BytesIO


def parsestr(s):
    assert isinstance(s, str)
    s = s.replace("'", "\\'")
    s = "b'" + s + "'"
    return eval(s)

parser = argparse.ArgumentParser(
    description="Print plist binary patch stanzas",
    epilog="example: makebinpatch.py 'ABC\\x00' '\\x80EF\\xFF' 'Change ABC to EF'")
parser.add_argument("find", help="Python syntax string to find")
parser.add_argument("replace", help="Python syntax string to replace")
parser.add_argument("comment", help="Comment for patch", nargs='?' )

args = parser.parse_args()

find = parsestr(args.find)
replace = parsestr(args.replace)

d = dict(Find=plistlib.Data(find), Replace=plistlib.Data(replace)) # , Disabled=False)
if args.comment:
    d["Comment"] = args.comment


f = BytesIO()

# We don't want the stuff at the top of a full plist

plw = plistlib.PlistWriter(f, writeHeader=False, indentLevel=4)
plw.writeValue(d)

print (f.getvalue())

if len(find) != len(replace):
    print ("Warning: find and replace lengths do not match")


