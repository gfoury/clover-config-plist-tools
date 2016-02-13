#!/usr/bin/python2.7
import sys
import plistlib
import argparse
import plistmonkey

from io import BytesIO

def parsestr(s):
    assert isinstance(s, str)
    s = s.replace("'", "\\'")
    s = "b'" + s + "'"
    return eval(s)

def parsehex(s):
    assert isinstance(s, str)
    ba = bytearray.fromhex(s)
    return str(ba)

parser = argparse.ArgumentParser(
    description="Print plist binary patch stanzas",
    epilog="example: makebinpatch.py 'ABC\\x00' '\\x80EF\\xFF' 'Change ABC to EF'")

parser.add_argument("--hex", "-x",
                    help="Interpret arguments as hex rather than Python string syntax",
                    action="store_true")

group = parser.add_mutually_exclusive_group()
group.add_argument("--whole", "-w",
                   help="Generate a complete plist, not just a stanza",
                   action="store_true")
group.add_argument("--clover",
                   help="Generate Clover ACPI/DSDT/Patches wrapper",
                   action="store_true")
parser.add_argument("-s", "--short-data",
                    help="Use single-line <data> when possible",
                    action="store_true")
parser.add_argument("find", help="Python syntax string to find")
parser.add_argument("replace", help="Python syntax string to replace")
parser.add_argument("comment", help="Comment for patch", nargs='?' )

args = parser.parse_args()
plistmonkey.rehabManHouseStyle = args.short_data

if args.hex:
    find = parsehex(args.find)
    replace = parsehex(args.replace)
else:
    find = parsestr(args.find)
    replace = parsestr(args.replace)

d = dict(Find=plistlib.Data(find), Replace=plistlib.Data(replace)) # , Disabled=False)
if args.comment:
    d["Comment"] = args.comment

if args.clover:
    d = dict(ACPI=dict(DSDT=dict(Patches=[d])))

if args.whole or args.clover:
    plistlib.writePlist(d, sys.stdout)
else:
    f = BytesIO()
    # We don't want the stuff at the top of a full plist
    plw = plistlib.PlistWriter(f, writeHeader=False, indentLevel=4)
    plw.writeValue(d)
    sys.stdout.write(f.getvalue())

if len(find) != len(replace):
    print ("Warning: find and replace lengths do not match")
