# clover-config-plist-tools

Some tools for checking and building Clover `config.plist` binary patches.

## `Expect`

For many patches, we know exactly how many times it *should* match. These tools understand an additional `Expect` clause in patches:

```xml
<key>Comment</key>
<string>change Method(_Q91,0,N) to XQ91</string>
<key>Find</key>
<data>X1E5MQA=</data>
<key>Replace</key>
<data>WFE5MQA=</data>
<key>Expect</key>
<integer>1</integer>
```

If the match count is not the same as `Expect`, you get warnings.

The `--expected` argument will print a new config.plist with `Expect` added to each patch, for all patches that applied at least once. Use this new config.plist as a template; you may still have patches where the number of patches is not known precisely.

As of the time of writing, Clover will still apply binary patches an arbitrary number of times.

## `plist` structure

In plists, the order of keys in a dict is not significant. However, these tools will preserve existing ordering. `catplist.py` and `diffplist.py` have an option to sort keys, though.

Normally &lt;data&gt; clauses will put the base64 data on a separate line. RehabMan likes to put them on the same line, and `--expected` will do that. `makebinpatch.py`, `diffplist.py` and `catplist.py` have an option for this style.

## check-dsdt-patches.py
```
usage: check-dsdt-patches.py [-h] [-c CONFIG] [-d OUTPUT_DIRECTORY]
                             [--expected] [-v]
                             DSDT.aml [DSDT.aml ...]

Apply binary patches to DSDT/SSDT files according to a Clover config.plist.

positional arguments:
  DSDT.aml              One or more DSDT.aml/SSDT.aml files.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        The clover config file. Defaults to config.plist.
  -d OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Write patched AML files to directory
  --expected            Produce a new plist on stdout with Expect counts
  -v, --verbose         Increase verbosity level
```



## check-kext-patches.py
```
usage: check-kext-patches.py [-h] [-a] [-r] [-v] [--expected]
                             [--ignore-kext-dupes] [-c CONFIG]

Test if Clover kext patches would apply

optional arguments:
  -h, --help            show this help message and exit
  -a, --enable-all      Pretend all patches are enabled, but do not do
                        replacements for disabled ones
  -r, --running         Check against running kernel cache. The default is to
                        search all kexts in /Library/Extensions and
                        /System/Library/Extensions
  -v, --verbose         Be more verbose, -vv for more
  --expected            Produce a new plist on stdout with Expect counts
  --ignore-kext-dupes   Don't warn about multiple kexts with the same name
  -c CONFIG, --config CONFIG
                        path to config.plist
```

## makebinpatch.py
```
usage: makebinpatch.py [-h] [--hex] [--whole | --clover] [-s]
                       find replace [comment]

Print plist binary patch stanzas

positional arguments:
  find              Python syntax string to find
  replace           Python syntax string to replace
  comment           Comment for patch

optional arguments:
  -h, --help        show this help message and exit
  --hex, -x         Interpret arguments as hex rather than Python string
                    syntax
  --whole, -w       Generate a complete plist, not just a stanza
  --clover          Generate Clover ACPI/DSDT/Patches wrapper
  -s, --short-data  Use single-line <data> when possible

example: makebinpatch.py 'ABC\x00' '\x80EF\xFF' 'Change ABC to EF'
```

## diffplist.py
```
usage: diffplist.py [-h] [-s] [-n] [-g] file1 file2

Diff two normalized property lists

positional arguments:
  file1             path to first file
  file2             path to second file

optional arguments:
  -h, --help        show this help message and exit
  -s, --short-data  Use single-line <data> when possible
  -n, --normalize   Normalize by sorting keys
  -g, --git-diff    Use git diff instead of diff

Unrecognized arguments are passed to diff

Example: diff -U10 config1.plist config2.plist
Example: diff config1.plist config2.plist -U 10
```

## catplist.py
```
usage: catplist.py [-h] [-s] [-n] plist

Cat (and normalize) a property list

positional arguments:
  plist             path to plist

optional arguments:
  -h, --help        show this help message and exit
  -s, --short-data  Use single-line <data> when possible
  -n, --normalize   Normalize by sorting keys
  ```
