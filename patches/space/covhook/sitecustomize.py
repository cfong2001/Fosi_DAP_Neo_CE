"""Loaded via PYTHONPATH by run_coverage.py: records every module 0
instruction address any Unicorn instance executes, and appends them to
$FOSI_COV_OUT at exit."""
import atexit
import os

try:
    import unicorn
except ImportError:
    unicorn = None

if unicorn is not None and os.environ.get('FOSI_COV_OUT'):
    LO, HI = 0x03050000, 0x03079C14
    hits = set()
    _init = unicorn.Uc.__init__

    def _hook(uc, address, size, user):
        hits.add(address)

    def __init__(self, *a, **k):
        _init(self, *a, **k)
        try:
            self.hook_add(unicorn.UC_HOOK_CODE, _hook, begin=LO, end=HI - 1)
        except Exception:
            pass

    unicorn.Uc.__init__ = __init__

    @atexit.register
    def _dump():
        with open(os.environ['FOSI_COV_OUT'], 'a') as f:
            f.write('\n'.join(f'{a:x}' for a in sorted(hits)) + '\n')
