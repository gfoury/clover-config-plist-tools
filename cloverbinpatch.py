#!/usr/bin/python2.7
import plistlib
import argparse
import os.path
import logging

logging.basicConfig(format="%(levelname)-8s %(message)s")
log = logging.getLogger("cloverbinpatch")


class Patch:
    def __init__(self, p):
        assert isinstance(p, dict)
        self.find = p["Find"].data
        assert isinstance(self.find, str)
        self.replace = p["Replace"].data
        assert isinstance(self.replace, str)
        self.comment = p.get("Comment")
        if self.comment is not None:
            assert isinstance(self.comment, str)
        self.applied_count = 0
        self.applied_file_count = 0
        self.check()
    def check(self):
        if self.comment is None:
            log.warn("Patch without comment: %r", self)
        if len(self.find) != len(self.replace):
            log.error("Patch find/replace lengths do not match in %r", self)
            log.error("This program is almost certainly broken for that case")
            exit(1)

    def count(self, s):
        return s.count(self.find)
    def apply(self, s):
        rv = s.replace(self.find, self.replace)
        assert len(rv) == len(s)
        return rv
    def __repr__(self):
        return "<Patch: Find {!r} Replace {!r} Comment {!r}>".format(
            self.find, self.replace, self.comment)


def parse_config_plist(file_or_filename):
    return plistlib.readPlist(file_or_filename)

def patchlist_from_config(config):
    """Generate a list of Patch objects from a config.plist dictionary.

    :param config: A parsed plist as dictionary
    :return: list of DSDT Patch objects
    :rtype: list[Patch]
    """
    try:
        acpi = config["ACPI"]
        acpi_dsdt = acpi["DSDT"]
        acpi_dsdt_patches = acpi_dsdt["Patches"]
        patches = map(Patch, acpi_dsdt_patches)
        return patches
    except KeyError:
        log.error("config.plist file is missing ACPI/DSDT/Patches section")
        exit(1)

parser = argparse.ArgumentParser(
    description="Apply binary patches to DSDT/SSDT files according to a Clover config.plist.")
parser.add_argument("-c", "--config", nargs=1, default="config.plist",
                    help="The clover config file. Defaults to config.plist.",
                    type=argparse.FileType("r"))
parser.add_argument("-n", "--dry-run", help="Do not write any files", action="store_true")
parser.add_argument("-d", "--output-directory", help="Directory for output files. Defaults to overwriting existing files.", nargs=1)

parser.add_argument('-v', '--verbose', action='count', help="Increase verbosity level")


parser.add_argument("dsdt", type=argparse.FileType("rb"), nargs='+', metavar="DSDT.aml",
                    help="One or more DSDT.aml/SSDT.aml files.")

args = parser.parse_args()
print args
dir = None
if args.output_directory:
    dir = args.output_directory[0]
    if not os.path.isdir(dir):
        parser.error("-d directory '{}' is not a directory".format(dir))
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

patches = patchlist_from_config(config_plist)

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
        if dir:
            f.close()
            ofilename = os.path.join(dir, basename)
            ofile = open(ofilename, "wb")
        else:
            name = f.name
            f.close()
            ofile = open(name, "wb")
        ofile.write(patched)
        ofile.close()


for p in patches:
    log.debug("patch '%s' applied %d times to %d files",
              p.comment, p.applied_count, p.applied_file_count)
    if p.applied_file_count == 0:
        log.warn("patch did not apply to any files: %r", p)

