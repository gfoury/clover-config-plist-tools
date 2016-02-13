import plistlib
import collections

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

sortItems = False

class UnsortableList(list):
    def sort(self):
        return self


class MonkeyPatchOrderedDict(collections.OrderedDict):
    def items(self):
        global sortItems
        if sortItems:
            return collections.OrderedDict.items(self)
        else:
            return UnsortableList(collections.OrderedDict.items(self))

plistlib._InternalDict = MonkeyPatchOrderedDict


# This is even grosser.
# Normally <data> shows up like:
#
#    <data>
#    fOoBaR==
#    </data>
#
# RehabMan's plists express short data as:
#
#     <data>fOoBaR==</data>
#
rehabManHouseStyle = False

def writeData(self, data):
    global rehabManHouseStyle
    maxlinelength = max(16, 76 - len(self.indent.replace("\t", " " * 8) *
                             self.indentLevel))
    db64 = data.asBase64(maxlinelength)
    db64crs = db64.count("\n")
    if rehabManHouseStyle and db64crs <= 1:
        db64 = db64.rstrip()
        self.file.write(self.indent * self.indentLevel)
        self.file.write("<data>")
        self.file.write(db64)
        self.file.write("</data>\n")
    else:
        self.beginElement("data")
        self.indentLevel -= 1
        for line in db64.split("\n"):
            if line:
                self.writeln(line)
        self.indentLevel += 1
        self.endElement("data")

plistlib.PlistWriter.writeData = writeData

# end plistlib monkeypatch
