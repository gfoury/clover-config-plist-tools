#!/usr/bin/python2.7
import argparse
import logging
import os.path
import plistlib
import sys
import patch
#import logmonkey
import plistmonkey

plistmonkey.rehabManHouseStyle = True
plistmonkey.sortItems = False

logging.basicConfig(format="%(levelname)-8s %(message)s")
log = logging.getLogger("cloverbinpatch")


def parse_config_plist(file_or_filename):
    return plistlib.readPlist(file_or_filename)


parser = argparse.ArgumentParser(
    description="Apply binary patches to DSDT/SSDT files according to a Clover config.plist.")

parser.add_argument("-c", "--config", nargs=1, default="config.plist",
                    help="The clover config file. Defaults to config.plist.",
                    type=argparse.FileType("r"))
parser.add_argument("-n", "--dry-run", help="Do not write any files", action="store_true")
parser.add_argument("-d", "--output-directory",
                    help="Directory for output files. Defaults to overwriting existing files.",
                    nargs=1)
parser.add_argument("--expected", help="Produce a new plist on stdout with Expect counts", action="store_true")
parser.add_argument('-v', '--verbose', action='count', help="Increase verbosity level")
parser.add_argument("dsdt", type=argparse.FileType("rb"), nargs='+', metavar="DSDT.aml",
                    help="One or more DSDT.aml/SSDT.aml files.")

args = parser.parse_args()
output_dir = None
if args.output_directory:
    output_dir = args.output_directory[0]
    if not os.path.isdir(output_dir):
        parser.error("-d directory '{}' is not a directory".format(output_dir))
# print repr(args)

if args.verbose == 1:
    log.setLevel(logging.INFO)
elif args.verbose >= 2:
    log.setLevel(logging.DEBUG)

config_file = args.config
if isinstance(config_file, list):
    # I don't understand.
    config_file = config_file[0]
config_plist = parse_config_plist(config_file)

patches = patch.Patch.list_from_clover_config(config_plist)

for f in args.dsdt:
    assert isinstance(f, file)
    basename = os.path.basename(f.name)
    unpatched = f.read()
    patched = unpatched
    file_count = 0
    file_patch_count = 0
    for p in patches:
        count = p.count(patched)
        patched = p.apply(patched)
        p.applied_count += count
        file_patch_count += count
        if count > 0:
            p.applied_file_count += 1
            file_count += 1
        log.debug("  file %s, patch %s applied %d times", f.name, p.comment, count)
    log.info("file %s, %s patches applied %s times", f.name, file_count, file_patch_count)
    assert len(unpatched) == len(patched)
    if file_count == 0:
        log.info("-- file %s, no patches matched", f.name)
    if not args.dry_run:
        if output_dir:
            f.close()
            output_filename = os.path.join(output_dir, basename)
            output_file = open(output_filename, "wb")
        else:
            name = f.name
            f.close()
            output_file = open(name, "wb")
        output_file.write(patched)
        output_file.close()

for p in patches:
    log.debug("patch '%s' applied %d times to %d files",
              p.comment, p.applied_count, p.applied_file_count)
    if p.applied_file_count == 0:
        log.warn("patch did not apply to any files: %r", p)
    elif p.has_expected:
        if p.expected != p.applied_count:
            matches = "s"[p.expected==1:]
            log.error("patch expected %d time%s, got %d: %r ", p.expected,
                 matches, p.applied_count, p)
    else:
        p.dict["Expect"] = p.applied_count

if args.expected:
    plistlib.writePlist(config_plist, sys.stdout)
