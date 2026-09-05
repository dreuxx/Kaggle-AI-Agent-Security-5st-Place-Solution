"""
Module implementing generic communication patterns with Python in / Python out
supporting many (nested) primitives + special data science types like DataFrames
or np.ndarrays, with gRPC + protobuf as a backing implementation.
"""

import os
import sys

# Compile the protobuf / gRPC stubs against the local runtime so the gateway
# and inference server can run on different docker-python image versions without
# version-mismatch errors.
import kaggle_evaluation.core.proto_compiler as _proto_compiler

try:
    import grpc_tools
except ImportError:
    import subprocess
    import sys
    import os
    import glob
    deps_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deps')
    wheel = glob.glob(os.path.join(deps_dir, 'grpcio_tools-*.whl'))[0]
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', '--no-index', '--no-deps', wheel])

_proto_compiler.ensure_compiled()

module_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(module_dir)


__version__ = '1.7.0'


def help():
    """Print the kaggle_evaluation user guide."""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path) as f:
            print(f.read())
    else:
        print('kaggle_evaluation user guide not found.')
        print('See the competition page for submission instructions.')
