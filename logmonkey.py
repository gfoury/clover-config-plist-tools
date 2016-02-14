import logging
import sys

# monkeypatch logging to bold WARNING and higher if on a tty

emphasis_on = "\x1b[31m"
emphasis_off = "\x1b[0m\x00"

oldemit = logging.StreamHandler.emit
def stream_emit(self, record):
    if record.levelno > 20:
        record.levelname = emphasis_on + record.levelname + emphasis_off
    else:
        record.levelname = emphasis_off + record.levelname + emphasis_off
    return oldemit(self, record)
if sys.stderr.isatty():
    logging.StreamHandler.emit = stream_emit
