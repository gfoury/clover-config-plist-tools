import logging

log = logging.getLogger("patch")

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
            raise ValueError

    def count(self, s):
        return s.count(self.find)

    def apply(self, s):
        rv = s.replace(self.find, self.replace)
        assert len(rv) == len(s)
        return rv

    def __repr__(self):
        return "<Patch: Find {!r} Replace {!r} Comment {!r}>".format(
            self.find, self.replace, self.comment)

    @classmethod
    def list_from_clover_config(cls, config):
        """Generate a list of Patch objects from a Clover config.plist dict.

        :param config: A parsed plist
        :type config: dict
        :return: list of DSDT Patch objects
        :rtype: list[patch.Patch]
        """
        try:
            acpi = config["ACPI"]
            acpi_dsdt = acpi["DSDT"]
            acpi_dsdt_patches = acpi_dsdt["Patches"]
            patches = map(Patch, acpi_dsdt_patches)
            return patches
        except KeyError:
            raise KeyError("config.plist file is missing ACPI/DSDT/Patches section")


class FilePatch(Patch):
    def __init__(self, p):
        assert isinstance(p, dict)
        self.filename = p["Name"]
        assert isinstance(self.filename, str)
        Patch.__init__(self, p)

    def check(self):
        if not self.filename:
            log.error("File patch is missing a name: %r", self)
            raise KeyError("File patch is missing Name")
        Patch.check(self)

    def __repr__(self):
        return "<Patch: Filename {!r} Find {!r} Replace {!r} Comment {!r}>".format(
            self.filename, self.find, self.replace, self.comment)

    @classmethod
    def list_from_clover_config(cls, config):
        """Generate a list of FilePatch objects from a Clover config.plist dict.

        :param config: A parsed plist
        :type config: dict
        :return: list of FilePatch objects
        :rtype: list[patch.FilePatch]
        """
        try:
            kexts_and_patches = config["KernelAndKextPatches"]
            kexts_to_patch = kexts_and_patches["KextsToPatch"]
            filepatches = map(FilePatch, kexts_to_patch)
            return filepatches
        except KeyError:
            raise KeyError("config.plist file is missing KernelAndKextPatches/KextToPatch section")