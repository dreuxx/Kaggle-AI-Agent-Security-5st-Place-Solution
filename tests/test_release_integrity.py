"""Tests for the publication package, not agent behavior or security bypasses."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publication_verifier", ROOT / "scripts/verify_release.py")
assert spec is not None and spec.loader is not None
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class ReleaseIntegrityTests(unittest.TestCase):
    def test_file_integrity(self):
        self.assertGreater(verifier.check_file_manifest(ROOT), 0)

    def test_source_identity_and_syntax(self):
        self.assertGreater(verifier.check_sources(ROOT), 0)

    def test_selected_archived_records(self):
        self.assertEqual(verifier.check_archived_records(ROOT), 24)

    def test_recorded_arithmetic(self):
        self.assertEqual(verifier.check_arithmetic(ROOT), 9)

    def test_document_links(self):
        self.assertGreater(verifier.check_doc_links(ROOT), 0)

    def test_bounded_credential_pattern_screen(self):
        self.assertGreater(verifier.check_publication_patterns(ROOT), 0)


if __name__ == "__main__":
    unittest.main()
