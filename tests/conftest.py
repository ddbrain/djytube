import sys
import os

# Ensure the root directory (where `installer` is located) is in the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def pytest_addoption(parser):
    parser.addoption(
        "--run-download-tests", action="store_true", default=False, help="Run download tests"
    )
