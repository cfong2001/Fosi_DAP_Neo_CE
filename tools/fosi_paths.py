"""Portable path resolution for the DAP Neo firmware tools.

No tool in this repo may hard-code a development workspace path. Every
location is resolved, in order:

  1. an explicit CLI argument (each tool's own flag),
  2. an environment variable (below),
  3. discovery: walk up from the calling script looking for the repo
     marker `tools/firmware_patch.py` — this works both in a plain
     clone (tools/ at the repo root) and in the original development
     workspace layout (a `repo/` subdirectory holding tools/).

Environment variables:
  FOSI_REPO_ROOT    directory that contains tools/ (the repo root)
  FOSI_STOCK_IMAGE  path to the stock DP3_V137.img
  FOSI_ECPATCH_DIR  directory holding the HIFIEC*.ecpatch inputs
                    (see patches/vorbis_swap/DEPENDENCY.md)
  FOSI_WORKSPACE    extraction workspace (extracted/ tree) for the
                    emulation harnesses
"""
import os
from pathlib import Path

STOCK_NAME = 'DP3_V137.img'
MARKER = Path('tools') / 'firmware_patch.py'


def find_tools_dir(start=None):
    """Locate the repo tools/ directory. `start` is the calling
    script's directory (or this file's, by default)."""
    env = os.environ.get('FOSI_REPO_ROOT')
    if env:
        cand = Path(env) / 'tools'
        if (cand / 'firmware_patch.py').exists():
            return cand
        raise FileNotFoundError(
            f'FOSI_REPO_ROOT={env} does not contain tools/firmware_patch.py')
    here = Path(start).resolve() if start else Path(__file__).resolve().parent
    for anc in (here, *here.parents):
        if (anc / 'firmware_patch.py').exists() and anc.name == 'tools':
            return anc
        for cand in (anc / 'tools', anc / 'repo' / 'tools'):
            if (cand / 'firmware_patch.py').exists():
                return cand
    raise FileNotFoundError(
        'cannot locate the repo tools/ directory; set FOSI_REPO_ROOT')


def repo_root(start=None):
    return find_tools_dir(start).parent


def stock_image_path(repo, explicit=None):
    """Stock image: explicit arg > FOSI_STOCK_IMAGE > repo root >
    repo parent (development layout keeps it next to repo/) > cwd.
    Returns the repo-root candidate even if missing, so the caller's
    error message names the expected place."""
    if explicit:
        return Path(explicit)
    env = os.environ.get('FOSI_STOCK_IMAGE')
    if env:
        return Path(env)
    for cand in (repo / STOCK_NAME, repo.parent / STOCK_NAME,
                 Path.cwd() / STOCK_NAME):
        if cand.exists():
            return cand
    return repo / STOCK_NAME


def ecpatch_dir(repo, explicit=None):
    """Directory with HIFIEC52/HIFIEC56.ecpatch: explicit arg >
    FOSI_ECPATCH_DIR > refs/echo-mini-opus/patch under the repo root
    or its parent. Returns None when not found (callers that need the
    inputs must refuse, not silently skip)."""
    if explicit:
        return Path(explicit)
    env = os.environ.get('FOSI_ECPATCH_DIR')
    if env:
        return Path(env)
    for cand in (repo / 'refs' / 'echo-mini-opus' / 'patch',
                 repo.parent / 'refs' / 'echo-mini-opus' / 'patch'):
        if (cand / 'HIFIEC56.ecpatch').exists():
            return cand
    return None
