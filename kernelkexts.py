#!/usr/bin/python

import gzip
import plistlib
import os.path
import patch
import collections
import sys
import argparse

parser = argparse.ArgumentParser(description="Test if Clover kext patches would apply")
parser.add_argument("--enable-all", "-a",
                    help="Pretend all patches are enabled, but do not do replacements for disabled ones",
                    action="store_true")
parser.add_argument("--verbose", "-v", help="Be more verbose, -vv for more",
                    action="count")
parser.add_argument("config", help="path to config.plist", default="config.plist")


args = parser.parse_args()
verbose = args.verbose

identifier_kext_to_kext_path = {}
# Examples:
# identifier_kext_to_kext_path["AppleHDA.kext"] ->
#     "/System/Library/Extensions/AppleHDA.kext"
#
# I'm not sure Clover can patch the following, but I'm remembering the mapping anyway:
#
# identifier_kext_to_kext_path["AppleHDAHardwareConfigDriver.kext"] ->
#     "/System/Library/Extensions/AppleHDA.kext/Contents/PlugIns/AppleHDAHardwareConfigDriver.kext"

def read_name_translations_from(filename, directory_prefix):
    """Read the cache's KextIdentifiers list to get kext pathnames"""

    with gzip.open(filename, "rb") as f:
        zplist = f.read()

    d = plistlib.readPlistFromString(zplist)

    kextinfos = d["OSKextIdentifierCacheKextInfo"]

    for kext in kextinfos:
        path = kext["OSBundlePath"]
        basename = os.path.basename(path)
        path = directory_prefix + path

        e = identifier_kext_to_kext_path.get(basename)
        if e:
            print "*** Warning duplicate identifier {} {} {}".format(path, e, basename)
        identifier_kext_to_kext_path[basename] = path

sle_path = "/System/Library/Caches/com.apple.kext.caches/Directories/System/Library/Extensions/KextIdentifiers.plist.gz"
le_path = "/System/Library/Caches/com.apple.kext.caches/Directories/Library/Extensions/KextIdentifiers.plist.gz"

read_name_translations_from(sle_path, directory_prefix="/System/Library/Extensions/")
read_name_translations_from(le_path, directory_prefix="/Library/Extensions/")

#config_path = "../HP-ProBook-4x30s-DSDT-Patch/config_master.plist"
#config_path = "lose.plist"
config_path = args.config

config_plist = plistlib.readPlist(config_path)
#plistlib.writePlist(config_plist, sys.stdout)
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
        fn = identifier_kext_to_kext_path[self.kext_name] + "/Contents/MacOS/" + self.name
        if not os.path.exists(fn):
            # IOGraphicsFamily, for example
            fn = identifier_kext_to_kext_path[self.kext_name] + "/" + self.name
        return fn

    def load_contents(self):
        with open(self.find_filename(), "rb") as f:
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

def is_disabled(patch):
    """Do we want to treat a patch as disabled, given our cmdline arguments?

    :param patch: a Patch
    :type patch: patch.Patch
    :return: True if we should skip this patch
    :rtype: bool
    """
    if args.enable_all:
        return False
    return patch.disabled

for p in patches:
    if verbose >= 2:
        print p
    if is_disabled(p):
        continue
    try:
        contents = Bundle.get_contents(p.filename)
    except KeyError:
        print "*** No file found for {}".format(p.filename)
        continue
    count = p.count(contents)
    if count:
        times = "s"[count==1:]
        if verbose >= 1:
            print "Applied {} time{}: {}".format(count, times, p.comment)
        p.applied_count += count
        if not p.disabled:
            contents = p.apply(contents)
            Bundle.set_contents(p.filename, contents)

for p in patches:
    if is_disabled(p):
        continue
    if p.applied_count == 0:
        print "Warning, applied 0 times", p.filename, p.comment

