#!/usr/bin/python

import gzip
import plistlib
import os.path
import patch
import argparse
import logging
import sys
import plistmonkey
import logmonkey

plistmonkey.rehabManHouseStyle = True
plistmonkey.sortItems = False

logging.basicConfig(format="%(levelname)-10s %(message)s")
log = logging.getLogger("kernelkexts")



parser = argparse.ArgumentParser(description="Test if Clover kext patches would apply")
parser.add_argument("-a", "--enable-all",
                    help="Pretend all patches are enabled, but do not do replacements for disabled ones",
                    action="store_true")
parser.add_argument("-r", "--running", help="Check against only kexts listed in running kernel caches. The default is to search all kexts in /Library/Extensions and /System/Library/Extensions",
                    action="store_true")
parser.add_argument("-v", "--verbose", help="Be more verbose, -vv for more",
                    action="count")
parser.add_argument("--expected", help="Produce a new plist on stdout with Expect counts", action="store_true")
parser.add_argument("--ignore-kext-dupes", help="Don't warn about multiple kexts with the same name", action="store_true")
output_group = parser.add_argument_group("Output kext", "Given a named kext, output the file before or after patching")
output_group.add_argument("--output-kext", help="Name of kext to write", nargs=1, metavar="KEXT_NAME")
output_group.add_argument("--output-kext-before",
                    help="File to write named kext, before patching",
                    metavar="FILE_BEFORE",
                    type=argparse.FileType("wb"))
output_group.add_argument("--output-kext-after",
                    help="File to write named kext, after patching",
                    metavar="FILE_AFTER",
                    type=argparse.FileType("wb"))
parser.add_argument("config", help="path to config.plist", default="config.plist")

args = parser.parse_args()
verbose = args.verbose

if args.verbose == 1:
    log.setLevel(logging.INFO)
elif args.verbose >= 2:
    log.setLevel(logging.DEBUG)

warn_dupes = not args.ignore_kext_dupes

# Examples:
# identifier_kext_to_kext_path["AppleHDA.kext"] ->
#     "/System/Library/Extensions/AppleHDA.kext"
#
# identifier_kext_to_kext_path["AppleHDAHardwareConfigDriver.kext"] ->
#     "/System/Library/Extensions/AppleHDA.kext/Contents/PlugIns/AppleHDAHardwareConfigDriver.kext"

identifier_kext_to_kext_path = {}

# In case the normal kext name doesn't match, try case-insensitive comparisons via
# a squashed-to-lowercase table

lcase_identifier_kext_to_kext_path = {}

def add_bundle(basename, path):
    warned = False
    e = identifier_kext_to_kext_path.get(basename)
    if warn_dupes and e and e != path:
        log.warning("duplicate kext identifier {} {}".format(path, basename))
        warned = True
    identifier_kext_to_kext_path[basename] = path
    lcase_basename = basename.lower()
    lower_e = lcase_identifier_kext_to_kext_path.get(lcase_basename)
    if warn_dupes and not warned:
        if lower_e and lower_e != path:
            log.warning("kext identifier differs only in case {} {} {}".format(path, e, basename))
    lcase_identifier_kext_to_kext_path[lcase_basename] = path


def read_name_translations_from(filename, directory_prefix):
    """Read the cache's KextIdentifiers list to get kext pathnames

    :param filename: Path of compressed KextIdentifiers.plist
    :param directory_prefix: path prefix for kexts found here
    """
    with gzip.open(filename, "rb") as f:
        plist = f.read()

    d = plistlib.readPlistFromString(plist)

    kextinfos = d["OSKextIdentifierCacheKextInfo"]

    for kext in kextinfos:
        path = kext["OSBundlePath"]
        basename = os.path.basename(path)
        path = directory_prefix + path
        add_bundle(basename, path)

def walk_for_kexts(directory_prefix):
    for root, dirs, files in os.walk('/System/Library/Extensions'):
        for d in dirs:
            if d.endswith(".kext"):
                path = root + "/" + d
                basename = d.replace(".kext", "")
                add_bundle(d, path)

if args.running:
    sle_path = "/System/Library/Caches/com.apple.kext.caches/Directories/System/Library/Extensions/KextIdentifiers.plist.gz"
    le_path = "/System/Library/Caches/com.apple.kext.caches/Directories/Library/Extensions/KextIdentifiers.plist.gz"
    read_name_translations_from(sle_path, directory_prefix="/System/Library/Extensions/")
    read_name_translations_from(le_path, directory_prefix="/Library/Extensions/")
else:
    walk_for_kexts("/System/Library/Extensions")
    walk_for_kexts("/Library/Extensions")


config_path = args.config

config_plist = plistlib.readPlist(config_path)

patches = patch.FilePatch.list_from_clover_config(config_plist)


# Contents of the binary for each kext bundle

class Bundle:
    """A named kext.

    Uses the identifier_kext_to_kext_path dict to find the base directory of the kext.
    """

    def __init__(self, name):
        self.name = name
        self.kext_name = name + ".kext"

    def find_filename(self):
        kext_path = identifier_kext_to_kext_path.get(self.kext_name)
        if not kext_path:
            lcase = self.kext_name.lower()
            kext_path = lcase_identifier_kext_to_kext_path.get(lcase)
            if kext_path:
                log.error("Filename case error %s: %r", self.kext_name, self)
        fn = kext_path + "/Contents/MacOS/" + self.name
        if not os.path.exists(fn):
            # IOGraphicsFamily, for example
            fn = identifier_kext_to_kext_path[self.kext_name] + "/" + self.name
        return fn

    def load_contents(self):
        with open(self.find_filename(), "rb") as f:
            # noinspection PyAttributeOutsideInit
            self.contents = f.read()

    # Class-wide cache for named bundles
    bundles = {}

    @classmethod
    def get_contents(cls, name):
        """Cache and return contents of the main binary file of a named kext."

        :param name: The name of the Bundle to look up, without ".kext"
        :type name: str
        :rtype: Bundle
        """
        b = cls.bundles.get(name)
        if b:
            return b.contents
        b = Bundle(name)
        b.load_contents()
        cls.bundles[name] = b
        return b.contents

    @classmethod
    def set_contents(cls, name, new_contents):
        """Replace the in-memory contents of the main binary file of a named kext

        :param name: The name of the Bundle, without ".kext"
        :type: param: str
        :param new_contents: The new binary contents
        :type new_contents: str
        """
        cls.bundles[name].contents = new_contents


def is_disabled(p):
    """Do we want to treat a patch as disabled, given our cmdline arguments?

    :param p: a Patch
    :type p: patch.Patch
    :return: True if we should skip this patch
    :rtype: bool
    """
    if args.enable_all:
        return False
    return p.disabled

if args.output_kext_before:
    before_binary = Bundle.get_contents(args.output_kext[0])
    args.output_kext_before.write(before_binary)
    args.output_kext_before.close()

for p in patches:
    log.debug("Found patch %r", p)
    if is_disabled(p):
        continue
    try:
        contents = Bundle.get_contents(p.filename)
    except KeyError:
        log.warning("No file found for %r", p)
        continue
    count = p.count(contents)
    if count:
        times = "s"[count == 1:]
        log.info("Applied %d time%s: %s", count, times, p.comment)
        p.applied_count += count
        if p.disabled:
            # Even if we are ignoring Disabled for counting, do not apply
            # the patch to our content cache
            pass
        else:
            contents = p.apply(contents)
            Bundle.set_contents(p.filename, contents)

if args.output_kext_after:
    after_binary = Bundle.get_contents(args.output_kext[0])
    args.output_kext_after.write(after_binary)
    args.output_kext_after.close()


for p in patches:
    if is_disabled(p):
        continue
    if p.has_expected:
        if p.applied_count != p.expected:
            log.error("expected %d, got %d in: %s: %s", p.expected,
                p.applied_count, p.filename, p.comment)
    elif p.applied_count == 0:
        log.warning("applied 0 times %s: %s:", p.filename,p.comment)
    else:
        p.dict["Expect"] = p.applied_count

if args.expected:
    plistlib.writePlist(config_plist, sys.stdout)