from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WorkstationGdiLinkTests(unittest.TestCase):
    def test_qmake_links_gdi32(self):
        text = (ROOT / "d64qt5" / "d64qt5_bridge.pro").read_text(encoding="utf-8")
        self.assertIn("-lgdi32", text)

    def test_smoke_test_links_gdi32(self):
        text = (ROOT / "d64qt5" / "build_workstation_smoke_test_mingw32.bat").read_text(encoding="utf-8")
        self.assertIn("-lgdi32", text)

if __name__ == "__main__":
    unittest.main()
