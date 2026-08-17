from pathlib import Path
import tempfile
import unittest

from d64prolog import KnowledgePredicate, PrologKnowledgeBase


class PrologKnowledgeModelTests(unittest.TestCase):
    def setUp(self):
        self.kb = PrologKnowledgeBase.from_source(
            '''
            apfel(gesund).
            apfel(gesund).
            apfel(rot).
            blutdruck(4711, 150, 90).
            hoher_blutdruck(P) :- blutdruck(P, S, _), S > 140.
            ''',
            filename='<test>',
        )

    def test_predicates_are_unique(self):
        names = [(p.name, p.arity) for p in self.kb.predicates]
        self.assertEqual(names.count(('apfel', 1)), 1)

    def test_duplicate_alternatives_are_removed(self):
        values = self.kb.alternatives_for_level(KnowledgePredicate('apfel', 1), ())
        self.assertEqual(values, ('gesund', 'rot'))

    def test_fact_query(self):
        value = self.kb.parse_value('gesund')
        self.assertTrue(self.kb.accepts(KnowledgePredicate('apfel', 1), (value,)))

    def test_rule_query(self):
        value = self.kb.parse_value('4711')
        self.assertTrue(self.kb.accepts(KnowledgePredicate('hoher_blutdruck', 1), (value,)))

    def test_from_files_merges_knowledge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = root / 'a.pl'; b = root / 'b.pl'
            a.write_text('farbe(rot).\n', encoding='utf-8')
            b.write_text('farbe(gruen).\n', encoding='utf-8')
            kb = PrologKnowledgeBase.from_files((a, b))
            self.assertEqual(kb.alternatives_for_level(KnowledgePredicate('farbe', 1), ()), ('gruen', 'rot'))


if __name__ == '__main__':
    unittest.main()
