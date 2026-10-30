"""Strategy 4 research check: docs in context/research/ stay groundwork-only (no forbidden terms)."""
import unittest
from orchestrator import RESEARCH, q_learning_hits


class TestResearchDocs(unittest.TestCase):
    def test_research_dir_exists(self):
        self.assertTrue(RESEARCH.is_dir(), RESEARCH)

    def test_no_forbidden_terms(self):
        for path in sorted(RESEARCH.rglob('*')):
            if path.is_file():
                with self.subTest(doc=path.relative_to(RESEARCH).as_posix()):
                    self.assertEqual(q_learning_hits(path.read_text(encoding='utf-8')), [])


if __name__ == '__main__':
    unittest.main()
