# load_all.py
#
# Intended for URL-based loading in SageMath, e.g.:
#   load('https://raw.githubusercontent.com/hunnellm/mr_JG/refs/heads/master/load_all.py')
#
# IMPORTANT: This file must NOT import or execute setup.py (or invoke
# setuptools/distutils setup()), because doing so in a Jupyter/Sage kernel
# triggers a SystemExit due to unrecognised kernel arguments (e.g. -f).

_BASE = 'https://raw.githubusercontent.com/hunnellm/mr_JG/refs/heads/master/'

# Load only the library modules needed for interactive use.
# Prefer the pure-Python wavefront implementation (no .pyx compilation needed).
# Note: load() is a SageMath built-in; this file is not meant to be run as a
# standalone Python script.
for _f in [
    'zero_forcing_wavefront_py.py',
    'inertia.py',
    'minrank.py',
    'Zq.py',
]:
    try:
        load(_BASE + _f)
    except Exception as _e:
        print('Warning: could not load {}: {}'.format(_f, _e))
