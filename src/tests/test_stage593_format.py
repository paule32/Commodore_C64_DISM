"""Stage 593: native INI-Schreibschleife und Sprach-Roundtrip."""
import configparser
from pathlib import Path
import unittest
from project_compiler_directories import LANGUAGES, settings_for

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


def code_fragment():
    start = SOURCE.index('        # Stage 593: Kein gemeinsamer Such-/Ausgabepfad')
    end = SOURCE.index('        _cache_entries = entries.get(_settings["asm_cache_key"]', start)
    snippet = SOURCE[start:end]
    return 'def write_stage593(parser, entries, project_path):\n    for _target, _settings in PROJECT_WINDOWS_TARGET_SETTINGS.items():\n' + snippet + '\n'


class FormatTests(unittest.TestCase):
    def test_write_arch_language_independently(self):
        targets = {'pe32': {'title': '32-Bit'}, 'pe64': {'title': '64-Bit'}}
        entries = {}
        for target in targets:
            for lang in LANGUAGES:
                ls = settings_for(target, lang)
                entries[ls['input_key']] = [{'path': f'/s593/{target}/{lang}/src'},
                                             {'path':f'/s593/{target}/{lang}/lib'}]
                entries[ls['output_key']] = [{'path':f'/s593/{target}/{lang}/bin'}]
                entries[ls['cache_key']] = [{'path':f'/s593/{target}/{lang}/asm'}]
                entries[ls['input_relative_key']] = [{'value':'false'}]
                entries[ls['output_relative_key']] = [{'value':'false'}]
        parser = configparser.ConfigParser()
        ns = {'PROJECT_WINDOWS_TARGET_SETTINGS': targets,
              'PROJECT_WINDOWS_COMPILER_LANGUAGES': LANGUAGES,
              '_project_compiler_directory_settings': settings_for,
              '_project_bool_entry': lambda entries,key,default:
                    str(entries.get(key,[{'value': default}])[0]['value']).lower()=='true',
              '_project_storage_path_mode':lambda value, project_path, relative:value}
        exec(compile(code_fragment(), str(ROOT/'d64_dism.py'), 'exec'), ns)
        ns['write_stage593'](parser, entries, Path('/s593/proj.pro'))
        for target in targets:
            for lang in LANGUAGES:
                ls = settings_for(target, lang)
                self.assertEqual(parser[ls['input_section']]['Path0001'], f'/s593/{target}/{lang}/src')
                self.assertEqual(parser[ls['input_section']]['Path0002'], f'/s593/{target}/{lang}/lib')
                self.assertEqual(parser[ls['output_section']]['Path'], f'/s593/{target}/{lang}/bin')
                self.assertEqual(parser[ls['output_section']]['AssemblerCache'], f'/s593/{target}/{lang}/asm')
        self.assertEqual(len(parser.sections()), 12)


if __name__=='__main__':
    unittest.main()
