from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / 'd64qt5' / 'd64_workstation.cpp').read_text(encoding='utf-8')
HDR = (ROOT / 'd64qt5' / 'd64_workstation.h').read_text(encoding='utf-8')
SMOKE = (ROOT / 'd64qt5' / 'workstation_smoke_test.cpp').read_text(encoding='utf-8')


class WorkstationExitIconStage36Tests(unittest.TestCase):
    def test_exit_window_has_double_click_class(self):
        self.assertIn('CS_DBLCLKS', CPP)
        self.assertIn('WM_LBUTTONDBLCLK', CPP)

    def test_exit_never_hard_terminates_process(self):
        click = CPP.split('case WM_LBUTTONUP:', 1)[1].split('case WM_LBUTTONDBLCLK:', 1)[0]
        self.assertIn('PanelHotItem::Exit', click)
        self.assertIn('g_exit_callback();', click)
        self.assertNotIn('ExitProcess', CPP)
        self.assertNotIn('TerminateProcess', CPP)

    def test_icon_is_in_left_topmost_workstation_panel(self):
        block = CPP.split('bool create_exit_window()', 1)[1].split('void destroy_exit_window()', 1)[0]
        self.assertIn('WS_EX_TOPMOST', block)
        self.assertIn('WS_EX_NOACTIVATE', block)
        self.assertIn('HWND_TOPMOST', block)
        self.assertIn('WORKSTATION_PANEL_WIDTH', block)
        self.assertRegex(block, r'\n\s*0,\n\s*0,')
        self.assertIn('WORKSTATION_EXIT_TOP', CPP)

    def test_icon_is_created_before_desktop_switch(self):
        block = CPP.split('bool D64WorkstationActivate(HWND mainWindow)', 1)[1].split('bool D64WorkstationInstallKeyboardGuard', 1)[0]
        self.assertLess(block.index('create_exit_window()'), block.index('SwitchDesktop(g_work_desktop)'))
        self.assertIn('destroy_exit_window()', block)

    def test_icon_failure_prevents_workstation_switch(self):
        block = CPP.split('if (!create_exit_window())', 1)[1].split('/*', 1)[0]
        self.assertIn('return false;', block)

    def test_icon_destroyed_before_return_to_root_desktop(self):
        block = CPP.split('void D64WorkstationBeginLeave()', 1)[1].split('void D64WorkstationFinalizeLeave()', 1)[0]
        self.assertLess(block.index('destroy_exit_window();'), block.index('switch_to_original_input_desktop();'))

    def test_header_exposes_visibility_probe(self):
        self.assertIn('bool D64WorkstationExitIconVisible();', HDR)

    def test_smoke_test_checks_exit_icon(self):
        self.assertIn('D64WorkstationExitIconVisible()', SMOKE)


if __name__ == '__main__':
    unittest.main()
