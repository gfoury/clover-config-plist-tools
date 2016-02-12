import plistlib

# In Python 3.x, plistlib supports OrderedDict, and we will want it
# to avoid screwing up ordering in people's hand-edited config.plists.
#
# In Python 2.x we monkeypatch plistlib's internal dictionary to
#   a) be an OrderedDict
#   b) make the thing returned by items() refuse to be sorted
#
# Would it be cleaner to just copy plistlib.py into this project?
# Yes, yes it would. But much of this project is about arbitrary
# string replacement in OS binaries, so why not do the moral equivalent
# in Python?

# begin plistlib monkeypatch

class UnsortableList(list):
    def sort(self):
        return self

class MonkeyPatchOrderedDict(collections.OrderedDict):
    def items(self):
        return UnsortableList(collections.OrderedDict.items(self))

plistlib._InternalDict = MonkeyPatchOrderedDict

# end plistlib monkeypatch