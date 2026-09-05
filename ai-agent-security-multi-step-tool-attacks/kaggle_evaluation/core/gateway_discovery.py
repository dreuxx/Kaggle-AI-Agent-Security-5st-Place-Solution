"""Auto-discovery of the competition gateway class.

When a submission runs on Kaggle, the competition-specific gateway ships as a
``*gateway.py`` file inside a ``kaggle_evaluation/`` directory under
``/kaggle/input``. This module locates that file, imports it, and returns the
gateway class so callers don't have to hard-code the class name.

Discovery uses ``ast`` to find class definitions that inherit from a
``*Gateway`` base such as :class:`Gateway`, :class:`GameGateway`, or
:class:`BaseGateway`.
"""

import ast
import importlib
import logging
import pathlib
import sys

import kaggle_evaluation.core.base_gateway
from kaggle_evaluation.core.base_gateway import GatewayRuntimeError, GatewayRuntimeErrorType

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_DIR = pathlib.Path('/kaggle/input')

# Files matching this glob (relative to the search dir) are scanned for gateway
# classes. The gateway ships directly inside a `kaggle_evaluation/` directory.
_GATEWAY_GLOB = '*/kaggle_evaluation/*gateway*.py'

# Fallback: the kaggle_evaluation package root (parent of core/).
# Used when DEFAULT_SEARCH_DIR doesn't exist (local development).
_PACKAGE_DIR = pathlib.Path(__file__).resolve().parent.parent

# When searching the package root directly, the gateway is a sibling of core/.
_PACKAGE_GATEWAY_GLOB = '*gateway*.py'


def _base_name(base: ast.expr) -> str | None:
    """Return the trailing identifier of a class base expression.

    Handles both bare names (``Gateway``) and dotted attribute access
    (``kaggle_evaluation.core.templates.Gateway``). Returns None for bases that
    aren't a simple name/attribute (e.g. subscripted generics).
    """
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return None


def _is_abstract(node: ast.ClassDef) -> bool:
    """Return True if the class directly inherits from abc.ABC."""
    return any(_base_name(base) == 'ABC' for base in node.bases)


def _find_gateway_class_names(source: str) -> list[str]:
    """Return the names of concrete classes in ``source`` that inherit from a *Gateway base.

    A class matches if any of its bases has a trailing identifier containing
    'Gateway' and the class is not itself abstract (inherits from abc.ABC).
    """
    tree = ast.parse(source)
    class_names = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if _is_abstract(node):
            continue
        for base in node.bases:
            name = _base_name(base)
            if name is not None and 'Gateway' in name:
                class_names.append(node.name)
                break
    return class_names


def find_gateway_class(
    search_dir: str | pathlib.Path | None = None,
    allow_standard_gateway: bool = True,
) -> type[kaggle_evaluation.core.base_gateway.BaseGateway]:
    """Discover and return the competition gateway class.

    Scans ``search_dir`` for a ``*gateway*.py`` file inside a
    ``kaggle_evaluation/`` directory, parses it to find exactly one class that
    inherits from a ``*Gateway`` base, imports the module, and returns the class.

    When no ``search_dir`` is given and the default ``/kaggle/input`` does not
    exist (local development), falls back to searching the ``kaggle_evaluation``
    package directory itself, where the deployment tooling places the gateway as
    a sibling of ``core/``.

    Args:
        search_dir: Directory to search. Defaults to ``/kaggle/input``.
        allow_standard_gateway: If True (default), falls back to a standard
            gateway from ``gateway_config.json`` when no custom gateway file is
            found. If False, raises ``FileNotFoundError`` instead.

    Returns:
        The discovered gateway class (a subclass of Gateway or GameGateway).

    Raises:
        GatewayRuntimeError: If no gateway file is found (when ``allow_standard_gateway``
            is False), or if zero or more than one gateway class is found.
    """
    if search_dir is not None:
        search_dir = pathlib.Path(search_dir)
        glob = _GATEWAY_GLOB
    elif DEFAULT_SEARCH_DIR.exists():
        search_dir = DEFAULT_SEARCH_DIR
        glob = _GATEWAY_GLOB
    else:
        search_dir = _PACKAGE_DIR
        glob = _PACKAGE_GATEWAY_GLOB

    gateway_path_candidates = sorted(search_dir.glob(glob))

    # Exclude files inside core/ (e.g. this module itself matches *gateway*).
    core_dir = _PACKAGE_DIR / 'core'
    gateway_path_candidates = [p for p in gateway_path_candidates if not p.resolve().is_relative_to(core_dir)]

    if not gateway_path_candidates:
        if not allow_standard_gateway:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                f'No gateway file matching {glob!r} found under {search_dir}',
            )
        from kaggle_evaluation.standard_gateways.standard import StandardGateway

        logger.info('No custom gateway file matching %r found under %s; falling back to %s.', glob, search_dir, StandardGateway.__name__)
        return StandardGateway

    # Collect every (path, class_name) pair so we can report ambiguity clearly.
    found: list[tuple[pathlib.Path, str]] = []
    for gateway_path in gateway_path_candidates:
        source = gateway_path.read_text()
        for class_name in _find_gateway_class_names(source):
            found.append((gateway_path, class_name))

    if not found:
        raise GatewayRuntimeError(
            GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
            f'No gateway class (subclass of a *Gateway base) found in any of: {[str(p) for p in gateway_path_candidates]}',
        )

    if len(found) != 1:
        described = [f'{name} in {path}' for path, name in found]
        raise GatewayRuntimeError(
            GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
            f'Expected exactly one gateway class but found {len(found)}: {described}',
        )

    gateway_path, gateway_class_name = found[0]

    if str(gateway_path.parent) not in sys.path:
        sys.path.insert(0, str(gateway_path.parent))
    gateway_module = importlib.import_module(gateway_path.stem)

    return getattr(gateway_module, gateway_class_name)
