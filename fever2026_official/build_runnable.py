"""Stage the authors' BERT pipeline for private execution, with paper-alignment fixes.

The upstream repository stays unmodified. The generated runnable/ directory is
ignored by the public FactKG repository; copy it directly to the GPU machine.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT / "upstream"
RUNNABLE = ROOT / "runnable"
CORE_FILES = (
    "constants.py", "datasets.py", "evaluate.py", "kg.py", "models.py",
    "retrieve_subgraphs.py", "run_stuff.py", "train.py", "utils.py",
    "requirements.txt", "environment.yaml", "README.md",
)


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ValueError(f"Expected one upstream match in {path.name}: {old[:75]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def build(output=RUNNABLE):
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing {output}")
    if not UPSTREAM.is_dir():
        raise FileNotFoundError("Initialize the FEVER upstream submodule first")
    with tempfile.TemporaryDirectory(prefix="fever_bert_stage_", dir=output.parent) as temp:
        staged = Path(temp) / "runnable"
        staged.mkdir()
        _populate(staged)
        shutil.move(str(staged), str(output))
    print(f"Runnable FEVER BERT pipeline: {output}")


def _populate(output):
    hashes = {}
    for name in CORE_FILES:
        source = UPSTREAM / name
        hashes[name] = hashlib.sha256(source.read_bytes()).hexdigest()
        shutil.copy2(source, output / name)

    # Upstream currently defaults to a 10k training sample, whereas the paper's
    # full-data BERT experiment uses the official FactKG train split.
    replace_once(output / "constants.py",
                 'TRAIN_FILENAME_PICKLE = "factkg_train_10k_official_sample.pickle"',
                 'TRAIN_FILENAME_PICKLE = "factkg_train.pickle"')

    # The source imports a gitignored local settings file not included upstream.
    (output / "glocal_settings.py").write_text(
        "SMALL = False\nSMALL_SIZE = 1000\n", encoding="utf-8"
    )

    # The paper selects by validation accuracy; the public source selects by
    # validation loss and retains mutable references to the live model weights.
    replace_once(output / "train.py", "import numpy as np\nimport torch",
                 "import copy\nimport numpy as np\nimport torch")
    replace_once(output / "train.py", '''                if average_val_loss >= best_val_loss:  # Check for stagnation _before_ updating best_val_loss
                    n_stagnation += 1
                else:  # Better than best loss
                    n_stagnation = 0
                if n_stagnation == n_early_stop:  # Early stopping, abort training
                    if verbose == 0:  # No output
                        break
                    logger.info(f"Epoch [{epoch + 1} / {n_epochs}]\\n")
                    logger.info(f"Train loss: {average_train_loss:.4f}, Train Accuracy: {train_accuracy:.4f}%")
                    logger.info(f"Validation loss: {average_val_loss:.4f}, Validation Accuracy: {val_accuracy:.4f}%\\n")
                    logger.info(f"Early stopping after {n_stagnation} rounds of no validation loss improvement.\\n")
                    break

                if average_val_loss < best_val_loss:
                    best_val_loss = average_val_loss
                    best_epoch_number = epoch + 1
                    best_val_accuracy = val_accuracy
                    best_model = model.state_dict()
''', '''                best_val_loss = min(best_val_loss, average_val_loss)
                if val_accuracy > best_val_accuracy:
                    best_epoch_number = epoch + 1
                    best_val_accuracy = val_accuracy
                    best_model = copy.deepcopy(model.state_dict())
                    n_stagnation = 0
                else:
                    n_stagnation += 1
                if n_stagnation >= n_early_stop:
                    logger.info(f"Early stopping after {n_stagnation} rounds of no validation accuracy improvement.\\n")
                    break
''')

    # Do not omit the last few train/dev claims when batch_size=4. Evaluation
    # must also be deterministic to choose a best epoch by full dev accuracy.
    replace_once(output / "run_stuff.py", '''        train_loader = get_dataloader(
            "train", args.subgraph_type, subgraph_to_use=args.subgraph_to_use, batch_size=args.batch_size)
        val_loader = get_dataloader(
            "val", args.subgraph_type, subgraph_to_use=args.subgraph_to_use, batch_size=args.batch_size)
''', '''        train_loader = get_dataloader(
            "train", args.subgraph_type, subgraph_to_use=args.subgraph_to_use,
            batch_size=args.batch_size, drop_last=False)
        val_loader = get_dataloader(
            "val", args.subgraph_type, subgraph_to_use=args.subgraph_to_use,
            batch_size=args.batch_size, shuffle=False, drop_last=False)
''')

    shutil.copy2(ROOT / "eval_five.py", output / "eval_five.py")
    commit = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True
    ).strip()
    (output / "provenance.json").write_text(json.dumps({
        "upstream": "https://github.com/AnkitKUpadhyay/kg-fact-verification-semantics",
        "commit": commit,
        "upstream_file_sha256": hashes,
        "local_adjustments": ["full_train_pickle", "missing_settings_file",
                              "dev_accuracy_checkpoint", "full_train_and_dev_batches"],
    }, indent=2), encoding="utf-8")
    print(f"Upstream commit: {commit}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-evaluator", action="store_true",
                        help="Refresh only the locally written evaluator in an existing runnable folder")
    args = parser.parse_args()
    if args.refresh_evaluator:
        if not RUNNABLE.is_dir() or not (RUNNABLE / "provenance.json").is_file():
            parser.error("No staged runnable folder to refresh")
        shutil.copy2(ROOT / "eval_five.py", RUNNABLE / "eval_five.py")
        print(f"Refreshed: {RUNNABLE / 'eval_five.py'}")
    else:
        build()
