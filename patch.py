import logging

log = logging.getLogger("patch")

class Patch:
    def __init__(self, p):
        assert isinstance(p, dict)
        self.dict = p
        try:
            self.find = p["Find"].data
            assert isinstance(self.find, str)
            self.replace = p["Replace"].data
            assert isinstance(self.replace, str)
        except KeyError:
            log.error("malformed patch %r", p)
            raise KeyError("malformed patch")
        self.comment = p.get("Comment")
        if self.comment is not None:
            assert isinstance(self.comment, str)
        self.disabled = p.get("Disabled", False)
        assert isinstance(self.disabled, bool)
        self.has_expected = False
        self.expected = p.get("Expect")
        if self.expected is not None:
            if isinstance(self.expected, str):
                self.expected = int(self.expected)
            assert isinstance(self.expected, int)
            self.has_expected = True
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
        # if self.disabled:
        #     return 0
        return s.count(self.find)

    def apply(self, s):
        # if self.disabled:
        #     return s
        rv = s.replace(self.find, self.replace)
        assert len(rv) == len(s)
        return rv

    def matches_expected(self, count):
        if not self.has_expected:
            return True
        return self.expected == count

    def _repr_list(self):
        l = ["Find", repr(self.find), "Replace", repr(self.replace),
            "Disabled", repr(self.disabled)]
        if self.has_expected:
            l += ["Expect", repr(self.expected)]
        if self.comment:
            l += ["Comment", repr(self.comment)]
        return l
    def __repr__(self):
        l = self._repr_list()
        return "<" + str(self.__class__) + ": " + " ".join(l) +">"

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
        except KeyError:
            raise KeyError("config.plist file is missing ACPI/DSDT/Patches section")
        patches = map(Patch, acpi_dsdt_patches)
        return patches


class FilePatch(Patch):
    def __init__(self, p):
        assert isinstance(p, dict)
        fn = p["Name"]
        assert isinstance(fn, str)
        if fn.startswith("disabled:"):
            fn = fn.replace("disabled:", "", 1)
            self.disabled = True
        self.filename = fn
        Patch.__init__(self, p)


    def check(self):
        if not self.filename:
            log.error("File patch is missing a name: %r", self)
            raise KeyError("File patch is missing Name")
        Patch.check(self)

    def _repr_list(self):
        l = ["Filename", repr(self.filename)]
        l.extend(Patch._repr_list(self))
        return l

    # def __repr__(self):
    #     return "<FilePatch: Filename {!r} Find {!r} Replace {!r} Comment {!r} Disabled {!r}>".format(
    #         self.filename, self.find, self.replace, self.comment, self.disabled)

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
        except KeyError:
            raise KeyError("config.plist file is missing KernelAndKextPatches/KextToPatch section")
        filepatches = map(FilePatch, kexts_to_patch)
        return filepatches
