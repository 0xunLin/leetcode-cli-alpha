import subprocess
from pathlib import Path
import sys

def run_tests(problem_dir: Path):
    """
    Run pytest inside the problem directory.
    """
    try:
        completed = subprocess.run([sys.executable, "-m", "pytest", "-q", str(problem_dir)], check=False)
        if completed.returncode != 0:
            print("❌ Tests failed.")
            raise SystemExit(completed.returncode)
        print("✅ Tests passed.")
    except FileNotFoundError:
        print("pytest not found. Install test requirements (pip install pytest).")