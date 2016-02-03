# clover-config-plist-tools

## cloverbinpatch.py
```
usage: cloverbinpatch.py [-h] [-c CONFIG] [-n] [-d OUTPUT_DIRECTORY] [-v]
    DSDT.aml [DSDT.aml ...]

Apply binary patches to DSDT/SSDT files according to a Clover config.plist.

positional arguments:
  DSDT.aml              One or more DSDT.aml/SSDT.aml files.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        The clover config file. Defaults to config.plist.
  -n, --dry-run         Do not write any files
  -d OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Directory for output files. Defaults to overwriting
                        existing files.
  -v, --verbose         Increase verbosity level
```
## makebinpatch.py
```
usage: makebinpatch.py [-h] find replace [comment]

Print plist binary patch stanzas

positional arguments:
  find        Python syntax string to find
  replace     Python syntax string to replace
  comment     Comment for patch

optional arguments:
  -h, --help  show this help message and exit

example: makebinpatch.py 'ABC\x00' '\x80EF\xFF' 'Change ABC to EF'
```
