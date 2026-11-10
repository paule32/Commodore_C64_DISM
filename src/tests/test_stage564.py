"""Stage 564: Systemanforderungen-Persistenz und GUI-Integration (statisch)."""
import unittest
from pathlib import Path
from installer_system_requirements import (
    SYSTEM_REQUIREMENTS_SECTION, parse_system_requirements,
    encode_system_requirements, validate_system_requirements,
)

BASE = Path(__file__).parent

class SystemRequirementsTest(unittest.TestCase):
    def test_defaults(self):
        d = parse_system_requirements(None)
        self.assertEqual(d['ram_mb'], 0)
        self.assertIn('win-11', d['windows_versions'])
    def test_roundtrip(self):
        d = parse_system_requirements(None)
        d.update(ram_mb=4096, screen_width_px=1920, screen_height_px=1080,
                 color_depth_bpp=32, require_admin=True, notification='abort_setup',
                 windows_versions=['win-7', 'win-11'])
        self.assertEqual(parse_system_requirements(encode_system_requirements(d)),d)
    def test_empty_versions_permitted(self):
        d = parse_system_requirements(None)
        d['windows_versions'] = []
        self.assertEqual(parse_system_requirements(encode_system_requirements(d))['windows_versions'],[])
    def test_invalid_integer(self):
        for value in (-1, True, '10'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_system_requirements({'ram_mb': value})
    def test_invalid_version(self):
        with self.assertRaises(ValueError):
            validate_system_requirements({'windows_versions':['win-999']})
    def test_invalid_notification(self):
        with self.assertRaises(ValueError):
            validate_system_requirements({'notification': 'nothing'})
    def test_binding(self):
        model = (BASE/'software_installer_model.py').read_text(encoding='utf-8')
        ui = (BASE/'software_installer.py').read_text(encoding='utf-8')
        dialogs = (BASE/'software_installer_dialogs.py').read_text(encoding='utf-8')
        self.assertIn('"Systemanforderungen": self.edit_system_requirements',ui)
        self.assertIn('"Systemanforderungen",',model)
        self.assertNotIn('"Benötigte Resourcen",',model)
        self.assertIn('gradient_title=True',dialogs[dialogs.index('class InstallerSystemRequirementsDialog'):])
        self.assertIn('self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)',dialogs[dialogs.index('class InstallerSystemRequirementsDialog'):])
        self.assertIn('installer_themed_warning(self, "Projektname",',ui)
        self.assertIn('self.help_callback("Systemanforderungen")', dialogs)
    def test_help(self):
        for file in ('installer.hhp','installer.hhc','installer.hhk','index.html'):
            self.assertIn('systemanforderungen.html',(BASE/'help/software_installer'/file).read_text(encoding='utf-8'))
        self.assertTrue((BASE/'help/software_installer/systemanforderungen.html').is_file())

if __name__ == '__main__':
    unittest.main()
