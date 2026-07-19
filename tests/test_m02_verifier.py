import subprocess
import unittest

from scripts.m02_verify_reference_submission import EXPECTED, verify_source_ref


class SourceObjectVerificationTest(unittest.TestCase):
    def test_nonexistent_full_sha_is_rejected(self):
        self.assertEqual(verify_source_ref("f" * 40), (False, ""))

    def test_pinned_commit_is_accepted(self):
        self.assertEqual(verify_source_ref(EXPECTED["source_ref"]), (True, "commit"))

    def test_blob_is_rejected(self):
        blob = subprocess.check_output(
            ["git", "rev-parse", "HEAD:scripts/m02_verify_reference_submission.py"],
            text=True,
        ).strip()
        self.assertEqual(verify_source_ref(blob), (False, "blob"))


if __name__ == "__main__":
    unittest.main()
