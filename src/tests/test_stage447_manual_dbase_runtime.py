# -*- coding: utf-8 -*-
"""Stage 447: manual runtime DLL generation, paths, menu and project persistence."""
from pathlib import Path
import ast
import pytest

ROOT = Path(__file__).parent
SRC = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


def test_both_tools_menu_commands_exist_and_are_connected():
    assert '"dBASE Runtime PE32 DLL erstellen"' in SRC
    assert '"dBASE Runtime PE32+ DLL erstellen"' in SRC
    assert 'tools_menu.addAction(self.dbase_runtime_pe32_action)' in SRC
    assert 'tools_menu.addAction(self.dbase_runtime_pe64_action)' in SRC
    assert 'self.create_dbase_runtime_dll("pe32")' in SRC
    assert 'self.create_dbase_runtime_dll("pe64")' in SRC


def test_architecture_specific_controls_are_in_environment_and_overview():
    assert 'self.console_runtime_build_button = QPushButton("dBASE Runtime DLL erstellen"' in SRC
    assert 'self.console_runtime_directory_edit = QLineEdit(runtime_group)' in SRC
    assert 'self.console_runtime_browse_button = QPushButton("...", runtime_group)' in SRC
    assert 'f"project_windows_{target_tag}_dbase_runtime_directory"' in SRC
    assert 'input_layout.addWidget(runtime_group)' in SRC
    assert '"umgebung": (' in SRC
    assert '"Eingabe", self.environment_input_scroll' in SRC
    assert 'self.console_runtime_directory_edit.editingFinished.connect(self._console_runtime_directory_changed)' in SRC


def test_project_persists_architecture_directories_independently():
    for target in ('pe32', 'pe64'):
        assert f'"__windows_{target}_console_dll_directory__"' in SRC
    assert '"DBaseRuntimeDLLDirectory"' in SRC
    assert 'parser.get(\n                _environment_section, "DBaseRuntimeDLLDirectory", fallback=""' in SRC
    assert '_project_loaded_path(_dll_path, Path(project_path))' in SRC
    assert 'entries[_settings["console_dll_directory_key"]]' in SRC
    assert 'self.set_project_windows_console_dll_directory(' in SRC
    assert 'panel.set_console_runtime_directory(' in SRC


def test_gui_uses_real_in_process_toolchain_and_validates_exports():
    assert 'from d64dbase.runtime_builder import create_runtime_dll' in SRC
    assert 'get_exports=_pe_export_name_ordinals' in SRC
    assert 'assemble32=assemble_pe32_object_source' in SRC
    assert 'link32=link_coff32_objects' in SRC
    assert 'assemble64=assemble_pe64_object_source' in SRC
    assert 'link64=link_coff64_objects' in SRC


def test_refuses_bad_architecture_without_touching_destination(tmp_path):
    from d64dbase.runtime_builder import create_runtime_dll
    with pytest.raises(ValueError):
        create_runtime_dll('invalid', tmp_path, get_exports=None,
                           assemble32=None, coff32=None, link32=None,
                           assemble64=None, coff64=None, link64=None)


def test_export_validation_does_not_overwrite_existing_dll(tmp_path):
    from d64dbase.runtime_builder import create_runtime_dll
    from d64dbase.console_runtime import DLL_NAME
    dest = tmp_path / DLL_NAME
    dest.write_bytes(b'old-valid-dll')
    # The staging output is intentionally rejected at the machine/export check.
    def bad_link(*args, **kwargs):
        return type('Result', (), {'executable': b'bad-but-nonempty'})()
    def any_assemble(*args, **kwargs):
        return object()
    def any_coff(obj):
        return object()
    with pytest.raises(ValueError):
        create_runtime_dll('pe32', tmp_path,
                           get_exports=lambda path, machine: {},
                           assemble32=any_assemble, coff32=any_coff, link32=bad_link,
                           assemble64=any_assemble, coff64=any_coff, link64=bad_link)
    assert dest.read_bytes() == b'old-valid-dll'


def test_actual_dll_generation_for_both_targets(tmp_path):
    from d64dbase.runtime_builder import create_runtime_dll
    from d64dbase.console_runtime import DLL_NAME, EXPORTS
    from test_stage446_real_pe_link import linkers
    from test_stage446_console_dll import pe_info, get_exports
    ns = linkers()
    for target, machine in [('pe32', 0x14c), ('pe64', 0x8664)]:
        output_dir = tmp_path / target
        dll = create_runtime_dll(
            target, output_dir, get_exports=get_exports,
            assemble32=ns['assemble_pe32_object_source'],
            coff32=ns['write_coff32_object'], link32=ns['link_coff32_objects'],
            assemble64=ns['assemble_pe64_object_source'],
            coff64=ns['write_coff64_object'], link64=ns['link_coff64_objects'],
        )
        assert dll == output_dir / DLL_NAME
        detected_machine, exports = pe_info(dll)
        assert detected_machine == machine
        assert set(EXPORTS).issubset(exports)
        assert dll.read_bytes() == (ROOT / 'd64dbase' / 'bin' / target / DLL_NAME).read_bytes()
