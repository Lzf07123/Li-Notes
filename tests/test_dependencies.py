import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pins(path: Path) -> dict[str, str]:
    pins = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, version = line.partition("==")
        if not sep or not name or not version:
            raise AssertionError(f"依赖未精确锁定: {line}")
        pins[name.lower()] = version
    return pins


def _version(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", value)[:3])


class DependencyLockTest(unittest.TestCase):
    def test_direct_dependencies_match_runtime_lock(self):
        direct = _pins(ROOT / "requirements.txt")
        locked = _pins(ROOT / "requirements.lock")
        for name, version in direct.items():
            self.assertEqual(locked.get(name), version, name)

    def test_known_vulnerable_versions_cannot_return(self):
        locked = _pins(ROOT / "requirements.lock")
        minimums = {
            "fastapi": (0, 161, 1),
            "starlette": (1, 9, 0),
            "pillow": (13, 0, 0),
            "python-multipart": (0, 0, 32),
        }
        for name, minimum in minimums.items():
            self.assertGreaterEqual(_version(locked[name]), minimum, name)


if __name__ == "__main__":
    unittest.main()
