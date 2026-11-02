"""Offline integrity checks for the staged authors' BERT pipeline."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_runnable import CORE_FILES, UPSTREAM, build


class BuildRunnableTest(unittest.TestCase):
    def test_upstream_is_preserved_and_paper_adjustments_are_explicit(self):
        before = {name: hashlib.sha256((UPSTREAM / name).read_bytes()).hexdigest()
                  for name in CORE_FILES}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "runnable"
            build(output)
            manifest = json.loads((output / "provenance.json").read_text())
            self.assertEqual(manifest["upstream_file_sha256"], before)
            self.assertIn('TRAIN_FILENAME_PICKLE = "factkg_train.pickle"',
                          (output / "constants.py").read_text())
            self.assertIn("copy.deepcopy(model.state_dict())",
                          (output / "train.py").read_text())
            self.assertIn("if val_accuracy > best_val_accuracy:",
                          (output / "train.py").read_text())
            self.assertTrue((output / "eval_five.py").is_file())
            self.assertFalse((output / "llm_fewshot_filtered.py").exists())
            with self.assertRaises(FileExistsError):
                build(output)
        after = {name: hashlib.sha256((UPSTREAM / name).read_bytes()).hexdigest()
                 for name in CORE_FILES}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
