"""Patch a COPY of upstream train.py so the best-dev checkpoint is written to disk immediately.

Upstream keeps the best state dict only in memory and saves it when training ends, so a
killed run loses everything. After this patch, every time dev accuracy reaches a new best,
`models/<model.name>.pth` is overwritten and `models/best_so_far.txt` records epoch and dev
accuracy. Training dynamics are unchanged (same selection rule, same early stopping).

Only ever run this on the P2 copy (run_p2.sh does), never on the baseline code.

  python patch_train_checkpoint.py /path/to/p2_copy/train.py
"""
import sys
from pathlib import Path

MARKER = "# [p2-patch] save best checkpoint immediately"
ANCHOR = "best_model = copy.deepcopy(model.state_dict())"


def patch(text):
    if MARKER in text:
        return text, False
    lines = text.splitlines(keepends=True)
    hits = [i for i, line in enumerate(lines) if line.strip() == ANCHOR]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one anchor line, found {len(hits)}; upstream train.py changed?")
    i = hits[0]
    indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
    eol = "\r\n" if lines[i].endswith("\r\n") else "\n"
    block = [
        f"{indent}{MARKER}\n",
        f"{indent}save_model(best_model, model.name)\n",
        f"{indent}with open('models/best_so_far.txt', 'w') as _f:\n",
        f"{indent}    _f.write(f'epoch={{best_epoch_number}} dev_accuracy={{best_val_accuracy:.4f}}\\n')\n",
        f"{indent}logger.info(f'[p2-patch] saved best checkpoint: epoch {{best_epoch_number}}, "
        f"dev {{best_val_accuracy:.4f}}')\n",
    ]
    block = [b[:-1] + eol for b in block]
    return "".join(lines[: i + 1] + block + lines[i + 1:]), True


def main():
    path = Path(sys.argv[1])
    text = path.read_bytes().decode("utf-8")  # keep original line endings (upstream file may be CRLF)
    if "save_model" not in text:
        raise SystemExit("train.py does not import save_model; cannot patch safely")
    new, changed = patch(text)
    if changed:
        compile(new, str(path), "exec")  # syntax check before writing
        path.write_bytes(new.encode("utf-8"))
    print(f"{path}: {'patched' if changed else 'already patched'}")


if __name__ == "__main__":
    main()
