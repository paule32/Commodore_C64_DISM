"""Qt5-Integrationstest für Stage 568 (ohne PyQt5 automatisch übersprungen)."""
import unittest
import uuid

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QDialog
    from installer_security_settings import parse_security_settings, SECURITY_SECTION
    from software_installer_model import InstallerProject
    from software_installer_dialogs import InstallerSecurityDialog, InstallerSerialListPropertiesDialog
    HAS_QT = True
except ImportError:
    HAS_QT = False


@unittest.skipUnless(HAS_QT, 'PyQt5 nicht installiert')
class Stage568QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_serial_status_undo_and_save(self):
        dlg = InstallerSerialListPropertiesDialog(dark_mode=True)
        self.assertEqual([dlg.serial_table.horizontalHeaderItem(i).text()
                          for i in range(3)], ["Serial Nummer", "Belegt", "Reg. Count"])
        dlg._change_rows(["S1", "S2"])
        dlg.serial_table.item(0, 1).setCheckState(Qt.Checked)
        dlg.serial_table.item(0, 2).setText("7")
        dlg._sort()
        dlg._accept_changes()
        self.assertEqual(dlg.result(), QDialog.Accepted)
        self.assertEqual(dlg.result_entry["serial_details"]["S1"],
                         {"occupied": True, "reg_count": 7})
        dlg.close()

    def test_validity_roundtrip_uuid_and_enabled_states(self):
        parent = InstallerSecurityDialog(InstallerProject(), dark_mode=True)
        self.assertEqual(parent.tabs.tabText(1), "Gültigkeits-Bereich")
        self.assertTrue(parent._gradient_title)
        self.assertEqual((parent.width(), parent.height()), (620, 550))
        self.assertFalse(parent.expiry_enabled.isChecked())
        self.assertFalse(parent.absolute_date_edit.isEnabled())
        self.assertEqual(parent.days_after_creation_spin.value(), 30)
        self.assertEqual(parent.max_system_installations_spin.value(), 2)
        self.assertEqual(parent.max_user_installations_spin.value(), 1)
        parent.expiry_enabled.setChecked(True)
        self.assertTrue(parent.absolute_date_edit.isEnabled())
        parent.expiry_radios["after_creation"].setChecked(True)
        self.assertTrue(parent.days_after_creation_spin.isEnabled())
        parent.counter_enabled.setChecked(True)
        parent.contact_info_checkbox.setChecked(True)
        parent._generate_product_id()
        self.assertEqual(uuid.UUID(parent.product_id_edit.text()).version, 4)
        parent._accept_changes()
        self.assertEqual(parent.result(), QDialog.Accepted)
        section = parse_security_settings(parent.serialized)
        self.assertEqual(section["validity"]["expiry_mode"], "after_creation")
        self.assertTrue(section["validity"]["counter_enabled"])
        self.assertEqual(section["validity"]["contact_website"], "%CompanyURL%")
        restored = InstallerSecurityDialog(InstallerProject(
            sections={SECURITY_SECTION: parent.serialized}), dark_mode=True)
        self.assertEqual(restored.product_id_edit.text(), parent.product_id_edit.text())
        self.assertTrue(restored.expiry_enabled.isChecked())
        restored.close()
        parent.close()

    def test_cancel_does_not_mutate_project(self):
        project = InstallerProject()
        dialog = InstallerSecurityDialog(project, dark_mode=True)
        dialog._generate_product_id()
        dialog.reject()
        self.assertNotIn(SECURITY_SECTION, project.sections)
        dialog.close()


if __name__ == '__main__':
    unittest.main()
