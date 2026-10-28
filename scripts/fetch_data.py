"""Download the exact public input wheel for the frozen experiment."""
from pathlib import Path
import hashlib
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
EXPECTED="76beb7a35b22cb2784df98bb20a6d9ca5803c4df761398b877db765bd6562c9a"
wheel=ROOT/'data'/'trendfollowing-1.3.1-py3-none-any.whl'
wheel.parent.mkdir(parents=True,exist_ok=True)
if not wheel.exists():
    subprocess.run([sys.executable,'-m','pip','download','--no-deps','--only-binary=:all:',
                    'trendfollowing==1.3.1','-d',str(wheel.parent)],check=True)
actual=hashlib.sha256(wheel.read_bytes()).hexdigest()
if actual!=EXPECTED:
    raise SystemExit(f"Wheel SHA256 mismatch: expected {EXPECTED}, got {actual}. Stop; do not silently use new data.")
print('Verified trendfollowing wheel SHA256:',actual)
