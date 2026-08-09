from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class TargetComboUiSourceTests(unittest.TestCase):
    def test_source_target_combo_replaces_radio_buttons(self) -> None:
        self.assertIn('self.build_target_combo = QComboBox', SOURCE)
        self.assertIn('self.build_target_combo.addItems(("C= 64", "Amiga", "Windows PE32", "Windows PE64"))', SOURCE)
        self.assertNotIn('self.c64_target_button = QRadioButton', SOURCE)
        self.assertNotIn('self.amiga_target_button = QRadioButton', SOURCE)
        self.assertNotIn('self.pe32_target_button = QRadioButton', SOURCE)

    def test_generated_target_combo_is_kept_in_sync(self) -> None:
        self.assertIn('self.generated_build_target_combo = QComboBox', SOURCE)
        self.assertIn('self.generated_build_target_combo.setCurrentText(display_name)', SOURCE)

    def test_amiga_and_windows_profiles_are_exclusive(self) -> None:
        start = SOURCE.index('def _update_platform_profile_visibility')
        end = SOURCE.index('def _build_target_name', start)
        block = SOURCE[start:end]
        self.assertIn('is_amiga = self.build_target == "amiga"', block)
        self.assertIn('is_windows = self.build_target in {"pe32", "pe64"}', block)
        self.assertIn('widget.setVisible(is_amiga)', block)
        self.assertIn('widget.setVisible(is_windows)', block)

    def test_combo_targets_map_to_internal_targets(self) -> None:
        start = SOURCE.index('def set_build_target')
        end = SOURCE.index('def set_amiga_cpu_model', start)
        block = SOURCE[start:end]
        self.assertIn('"c= 64"', block)
        self.assertIn('"Windows PE32"', block)
        self.assertIn('"Windows PE64"', block)
        self.assertIn('"Amiga"', block)


if __name__ == "__main__":
    unittest.main()
