"""Create a training-only independent forecasting workspace for Claude."""

from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "outputs/mlcc_v1"
OUTPUT = ROOT / "outputs/CLAUDE_FORECASTING_TRAIN_ONLY_PACK.zip"


def main() -> None:
    members = {
        "START_HERE_CLAUDE_PROMPT.md": ROOT / "outputs/CLAUDE_FORECASTING_PARALLEL_HANDOFF.md",
        "pyproject.toml": ROOT / "pyproject.toml",
        "requirements-prototype.lock": DATA / "requirements-prototype.lock",
    }
    for name in ("train_early.csv", "train_readings.csv", "train_labels.csv", "DATA_DICTIONARY.md", "SOURCES_AND_ASSUMPTIONS.md"):
        members[f"data/{name}"] = DATA / name
    for path in (ROOT / "src/sih26170").glob("*.py"):
        # Supply shared implementation references, not a generator for recreating
        # the withheld benchmark or its ground truth.
        if path.name != "mlcc_synthetic.py":
            members[str(path.relative_to(ROOT))] = path
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in members.items()}
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for name, path in members.items():
            archive.write(path, name)
        archive.writestr("SNAPSHOT.json", json.dumps({
            "scope": "Training-only forecasting development; no calibration/test/stress/demo data or existing trained artifacts",
            "input_sha256": hashes,
        }, indent=2) + "\n")
    with ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert all(not any(token in name for token in ("calibration_", "test_early", "test_labels", "test_readings", "model_bundle", "demo_", "generation_manifest")) for name in archive.namelist())
        assert len([name for name in archive.namelist() if name.endswith(".csv")]) == 3
        with tempfile.TemporaryDirectory(prefix="claude-handoff-check-") as temporary:
            archive.extractall(temporary)
            subprocess.run([
                sys.executable, "-I", "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); from sih26170.mlcc_prototype import prepare_early_features; print('Isolated source imports passed')",
                str(Path(temporary) / "src"),
            ], check=True, cwd=temporary)
    print(f"Created {OUTPUT.name}: {OUTPUT.stat().st_size:,} bytes; training-only contents verified")


if __name__ == "__main__":
    main()
