"""mr_JG package

Use explicit relative imports so the package works under Python 3
(SageMath 9/10+) and when installed via setup.py.
"""

from . import minrank

# Prefer the pure-Python wavefront implementation (URL-loadable, no compilation).
from . import zero_forcing_wavefront_py as zero_forcing_wavefront

# Optional Cython-accelerated modules (may not be built in all environments)
try:
    from . import zero_forcing_64
except Exception:
    zero_forcing_64 = None

try:
    from . import Zq
except Exception:
    Zq = None