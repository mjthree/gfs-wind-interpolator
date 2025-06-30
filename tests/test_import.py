import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_compile_wind_profiler():
    py_compile.compile(str(ROOT / 'wind_profiler.py'), doraise=True)
