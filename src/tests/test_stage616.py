# -*- coding: utf-8 -*-
"""Stage 616: Qt-Lebensdauer/Schema und Agent-0003-Sprachanalyse."""
import ast
import struct
import tempfile
import unittest
from pathlib import Path

from agent_0003_language import (LanguageEngine, DBF_WORD_FIELDS, read_dbf,
                                 ensure_agent_databases)

HERE = Path(__file__).resolve().parent


class TestCompactDBF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = HERE / 'data' / 'woerter.dbf'
        cls.rows = read_dbf(cls.path)

    def test_exact_count(self):
        self.assertEqual(len(self.rows), 6348)

    def test_no_redundant_fields(self):
        cols = [f[0] for f in DBF_WORD_FIELDS]
        self.assertEqual(len(cols), 17)
        for removed in ('WORTART', 'KASUS', 'LEMMA'):
            self.assertNotIn(removed, cols)
        self.assertEqual(cols[cols.index('VERB')+1], 'ADJEKTIV')

    def test_real_header_schema(self):
        b = self.path.read_bytes()
        count, hdr, size = struct.unpack_from('<IHH', b, 4)
        self.assertEqual(count, 6348)
        self.assertEqual(size, 1+sum(sz for _,_,sz in DBF_WORD_FIELDS))
        self.assertEqual(len(b), hdr+count*size+1)
        defs = []
        for pos in range(32, hdr-1, 32):
            if b[pos] == 13: break
            field = b[pos:pos+11].split(b'\0')[0].decode('ascii')
            defs.append((field, chr(b[pos+11]), b[pos+16]))
        self.assertEqual(defs, list(DBF_WORD_FIELDS))

    def test_all_logical_columns_boolean(self):
        logical = [name for name, typ, _ in DBF_WORD_FIELDS if typ=='L']
        self.assertTrue(all(type(row[name]) is bool for row in self.rows for name in logical))
        self.assertTrue(all(row['ID']==i+1 for i,row in enumerate(self.rows)))

    def test_words_and_gender(self):
        words = {row['WORT']: row for row in self.rows}
        self.assertTrue(words['kreis']['SUBSTANTIV'])
        self.assertTrue(words['kreis']['MALE'])
        self.assertTrue(words['kreis']['DER'])
        self.assertFalse(words['kreis']['FEMALE'])
        self.assertTrue(words['rot']['ADJEKTIV'])
        self.assertFalse(words['rot']['VERB'])
        self.assertEqual(len(words), len(self.rows))

    def test_fallback_dbf_uses_new_fields(self):
        with tempfile.TemporaryDirectory() as dirname:
            words,questions = ensure_agent_databases(Path(dirname))
            row = read_dbf(words)[0]
            self.assertEqual(set(row), {name for name,_,_ in DBF_WORD_FIELDS})
            self.assertTrue(read_dbf(questions))

    def test_agent_language_uses_flags(self):
        engine = LanguageEngine(self.path, HERE/'data'/'fragen.dbf')
        _analysis,tokens,question,_ = engine.inspect('wo befindet sich der rote kreis?')
        self.assertIsNotNone(question)
        self.assertEqual(question.intent,'position')
        self.assertIn('Substantiv', next(c for _i,w,c in tokens if w.lower()=='kreis'))
        self.assertIn('Adjektiv', next(c for _i,w,c in tokens if w.lower()=='rote'))


class TestCanvasLifetime(unittest.TestCase):
    def test_old_canvas_cleared_before_detach(self):
        text = (HERE/'agent_0003.py').read_text(encoding='utf-8')
        self.assertLess(text.index('self.canvas = None'),text.index('old.setParent(None)'))
        self.assertIn('old.deleteLater()',text)

    def test_agent_0002_theme_does_not_access_removed_canvas(self):
        tree = ast.parse((HERE/'agent_0002.py').read_text(encoding='utf-8'))
        cls = next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='GermanAssociationWidget')
        fn = next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='set_dark_mode')
        # Basis-Theme isoliert ausführen, ohne Abhängigkeit von einer Qt-Installation.
        isolated = ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
        namespace = {}
        exec(compile(isolated, '<set_dark_mode>', 'exec'),namespace)
        class Viewport:
            def update(self): pass
        class Header:
            def set_dark_mode(self,_): pass
        class Table:
            def horizontalHeader(self):return Header()
            def verticalHeader(self):return Header()
            def viewport(self):return Viewport()
        class App:
            canvas = None
            token_table = Table()
            def setStyleSheet(self,stylesheet):self.stylesheet=stylesheet
        app = App()
        namespace['set_dark_mode'](app,True)
        self.assertTrue(app._dark)
        self.assertIn('#191919',app.stylesheet)
        namespace['set_dark_mode'](app,False)
        self.assertFalse(app._dark)
        self.assertIn('#f4f4f4',app.stylesheet)

    def test_existing_canvas_still_receives_theme(self):
        tree = ast.parse((HERE/'agent_0002.py').read_text(encoding='utf-8'))
        cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='GermanAssociationWidget')
        fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='set_dark_mode')
        namespace={}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<theme>','exec'),namespace)
        class Canvas:
            called=[]
            def set_dark_mode(self,dark):self.called.append(dark)
        class H:
            def set_dark_mode(self,dark):pass
        class T:
            def horizontalHeader(self):return H()
            def verticalHeader(self):return H()
            def viewport(self):return type('V',(),{'update':lambda self:None})()
        class App:
            canvas=Canvas()
            token_table=T()
            def setStyleSheet(self,style):pass
        a=App();namespace['set_dark_mode'](a,True)
        self.assertEqual(a.canvas.called,[True])


if __name__ == '__main__':
    unittest.main()
