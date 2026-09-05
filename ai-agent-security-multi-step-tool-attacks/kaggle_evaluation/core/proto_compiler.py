"""Runtime compilation of the kaggle_evaluation protobuf / gRPC stubs.

The gateway and inference server can run on docker-python images built months
apart, with different Python, grpcio, and protobuf versions. The gRPC wire
protocol is stable across versions, but the generated ``*_pb2.py`` /
``*_pb2_grpc.py`` stubs must match the locally installed protobuf / grpcio
runtime. Shipping pre-generated stubs therefore risks version-mismatch errors.

Instead we compile ``kaggle_evaluation.proto`` once, at first import, into a
temp directory on ``sys.path``. This produces stubs that always match the local
runtime regardless of which image is running. A temp directory is also necessary
because the package's own directory may be on a read-only mount.
"""

import atexit
import shutil
import sys
import tempfile
import threading
from pathlib import Path

_CORE_DIR = Path(__file__).resolve().parent
_PROTO_PATH = _CORE_DIR / 'kaggle_evaluation.proto'

_compile_lock = threading.Lock()
_compiled = False


def _compile(output_dir: Path) -> None:
    import grpc_tools
    from grpc_tools import protoc

    # grpc_tools bundles the well-known protobuf types; include them so the proto
    # compiles regardless of any future imports it may gain.
    assert grpc_tools.__file__ is not None
    well_known_include = Path(grpc_tools.__file__).parent / '_proto'

    args = [
        'grpc_tools.protoc',
        f'-I{_CORE_DIR}',
        f'-I{well_known_include}',
        f'--python_out={output_dir}',
        f'--grpc_python_out={output_dir}',
        f'--pyi_out={output_dir}',
        str(_PROTO_PATH),
    ]
    exit_code = protoc.main(args)
    if exit_code != 0:
        raise RuntimeError(f'Failed to compile {_PROTO_PATH}: grpc_tools.protoc exited with code {exit_code}')


def ensure_compiled() -> None:
    """Compile the proto stubs into a temp dir and add it to ``sys.path``.

    Idempotent and thread-safe: the actual compilation runs at most once per
    process, on first call. The temp dir is cleaned up at process exit.
    """
    global _compiled
    if _compiled:
        return
    with _compile_lock:
        if _compiled:
            return
        # mkdtemp + atexit rather than TemporaryDirectory because the dir must
        # stay on sys.path for the entire process; a context manager would delete
        # too early and destructor timing is GC-dependent.
        output_dir = Path(tempfile.mkdtemp(prefix='kaggle_eval_proto_'))
        _compile(output_dir)
        sys.path.insert(0, str(output_dir))
        atexit.register(lambda: shutil.rmtree(output_dir, ignore_errors=True))
        _compiled = True
