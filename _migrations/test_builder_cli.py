"""Ensure migration builders request portable source paths."""

from pathlib import Path
import subprocess
import sys
import unittest


MIGRATIONS = Path(__file__).resolve().parent
BUILDERS = (
    "build_marine_phytoplankton_eml.py",
    "build_postojna_planina_lter_eml.py",
    "build_vegetation_slovenia_eml.py",
)


class MigrationBuilderCliTest(unittest.TestCase):
    def test_builders_require_a_source_path(self):
        for builder in BUILDERS:
            with self.subTest(builder=builder):
                result = subprocess.run(
                    [sys.executable, str(MIGRATIONS / builder)],
                    capture_output=True, text=True, check=False)
                self.assertEqual(2, result.returncode)
                self.assertIn("--source", result.stderr)
                self.assertIn("required", result.stderr)


if __name__ == "__main__":
    unittest.main()
