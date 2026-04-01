import importlib.util
import json
import os
import re
import sys
import types
import urllib.error
import urllib.request


_OWNER = 'hunnellm'
_REPO = 'mr_JG'
_BRANCH = 'master'

# Only allow safe GitHub identifier characters (letters, digits, hyphens, dots, underscores)
_SAFE_ID = re.compile(r'^[\w.\-]+$')


def load_all(owner=_OWNER, repo=_REPO, branch=_BRANCH, token=None):
    """Import all top-level .py files from a GitHub repository (non-recursive).

    Files are fetched from the GitHub Contents API and compiled/executed in
    fresh module objects.  ``load_all.py`` itself is excluded.  Modules that
    fail to import are silently skipped.

    .. warning::
        This function executes remote source code.  Only point it at
        repositories you trust.

    Parameters
    ----------
    owner : str
        GitHub account/organisation that owns the repository.
    repo : str
        Repository name.
    branch : str
        Branch (or tag / SHA) to read from.
    token : str or None
        Optional GitHub personal-access token.  Pass one to raise the API
        rate limit from 60 to 5 000 requests per hour.

    Returns
    -------
    dict
        Mapping of ``module_name`` -> imported module object.

    Raises
    ------
    ValueError
        If ``owner``, ``repo``, or ``branch`` contain unsafe characters.
    urllib.error.HTTPError
        If the GitHub API returns a non-2xx response (e.g. repo not found,
        rate limit exceeded).
    urllib.error.URLError
        If a network error occurs while listing repository contents.
    """
    for param_name, value in (('owner', owner), ('repo', repo), ('branch', branch)):
        if not _SAFE_ID.match(value):
            raise ValueError(
                'Invalid characters in {!r} parameter: {!r}'.format(param_name, value)
            )

    api_url = 'https://api.github.com/repos/{}/{}/contents/?ref={}'.format(
        owner, repo, branch
    )

    def _make_request(url):
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github+json')
        if token:
            req.add_header('Authorization', 'token ' + token)
        return req

    with urllib.request.urlopen(_make_request(api_url)) as response:
        entries = json.loads(response.read().decode())

    module_dict = {}
    for entry in sorted(entries, key=lambda e: e['name']):
        name = entry.get('name', '')
        if entry.get('type') != 'file' or not name.endswith('.py'):
            continue
        if name == 'load_all.py':
            continue

        raw_url = entry.get('download_url')
        if not raw_url:
            continue

        try:
            with urllib.request.urlopen(_make_request(raw_url)) as raw_response:
                source = raw_response.read().decode()

            module_name = name[:-3]
            module = types.ModuleType(module_name)
            module.__file__ = raw_url
            code = compile(source, raw_url, 'exec')
            exec(code, module.__dict__)  # noqa: S102
            sys.modules[module_name] = module
            module_dict[module_name] = module
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            print('Warning: could not fetch {!r}: {}'.format(name, exc), file=sys.stderr)
        except Exception:
            pass

    return module_dict


if __name__ == '__main__':
    loaded_modules = load_all()
    print('Loaded modules:', list(loaded_modules.keys()))
