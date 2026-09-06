"""Package role-specific snapshots without exposing test data to EDA teammates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "outputs" / "mlcc_v1"
DELIVERABLES = ROOT / "outputs"


def archive(name: str, files: list[tuple[Path, str]]) -> dict[str, object]:
    path = DELIVERABLES / name
    destinations = [destination for _, destination in files]
    if len(destinations) != len(set(destinations)):
        raise ValueError(f"duplicate archive paths in {name}")
    missing = [str(source) for source, _ in files if not source.is_file()]
    if missing:
        raise FileNotFoundError(f"missing release inputs: {missing}")
    with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=6) as output:
        for source, destination in sorted(files, key=lambda item: item[1]):
            output.write(source, arcname=destination)
    with ZipFile(path) as output:
        bad = output.testzip()
        if bad:
            raise RuntimeError(f"invalid archive member: {bad}")
    return {
        "filename": name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "files": destinations,
    }


def tree_files(folder: Path) -> list[Path]:
    return [
        path for path in folder.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and not path.name.endswith(".pyc")
        and path.name != ".DS_Store"
        and path.name != "RELEASE_MANIFEST.json"
        and not path.name.endswith(".zip")
    ]


def main() -> None:
    common = [
        (DATA / "SOURCES_AND_ASSUMPTIONS.md", "SOURCES_AND_ASSUMPTIONS.md"),
        (DATA / "DATA_DICTIONARY.md", "DATA_DICTIONARY.md"),
    ]
    entries = []
    for number, prompt in (
        (1, "TEAMMATE_1_BLIND_EDA_PROMPT.md"),
        (2, "TEAMMATE_2_FAILURE_PATTERNS_PROMPT.md"),
    ):
        files = common + [
            (DATA / "train_readings.csv", "train_readings.csv"),
            (DATA / "train_early.csv", "train_early.csv"),
            (DATA / "handoffs" / prompt, "START_HERE_CLAUDE_PROMPT.md"),
        ]
        if number == 2:
            files.append((DATA / "train_labels.csv", "train_labels.csv"))
        assert all(
            not any(word in dest for word in ("calibration_", "test_", "model_bundle"))
            for _, dest in files
        )
        entries.append(archive(f"MLCC_TEAMMATE_{number}_PATTERN_PACK.zip", files))

    files = [
        (DATA / "handoffs" / "FRONTEND_MLCC_V1_HANDOFF.md", "START_HERE.md"),
        (DATA / "demo_early.csv", "demo_early.csv"),
        (DATA / "demo_outcomes.csv", "demo_outcomes.csv"),
        (DATA / "demo_response.json", "demo_response.json"),
    ] + common
    entries.append(archive("MLCC_FRONTEND_HANDOFF.zip", files))

    source_files = [ROOT / "README.md", ROOT / "pyproject.toml"]
    for folder in (ROOT / "src" / "sih26170", ROOT / "tests", ROOT / "scripts", ROOT / "docs", ROOT / "examples"):
        source_files.extend(tree_files(folder))
    source_files.extend(tree_files(DATA))
    root_snapshot = [(path, str(path.relative_to(ROOT))) for path in source_files]
    entries.append(archive("MLCC_PROTOTYPE_AND_BACKEND_HANDOFF.zip", root_snapshot))

    # The complete dataset is for the technical lead, not the two blind EDA tasks.
    data_files = [
        path for path in tree_files(DATA)
        if path.suffix in {".csv", ".md", ".json"}
        and "model_bundle" not in path.parts
        and "evaluation" not in path.parts
        and "handoffs" not in path.parts
        and path.name not in {"demo_response.json", "RELEASE_MANIFEST.json"}
    ]
    entries.append(archive(
        "MLCC_COMPLETE_SYNTHETIC_DATASET.zip",
        [(path, str(path.relative_to(DATA))) for path in data_files],
    ))
    manifest = {
        "release": "mlcc-v1",
        "provenance": "All bundled measurements are synthetic.",
        "files": entries,
    }
    (DATA / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps([{k: v for k, v in item.items() if k != "files"} for item in entries], indent=2))


if __name__ == "__main__":
    main()
