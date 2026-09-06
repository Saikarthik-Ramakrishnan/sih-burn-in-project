"""Build a self-contained context pack without environments, secrets or git files."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/CLAUDE_BACKEND_VERIFICATION_FULL_PACK.zip"
files = [(ROOT / "outputs/CLAUDE_BACKEND_VERIFICATION_PROMPT.md", "START_HERE.md")]
for name in ("README.md", "pyproject.toml"):
    files.append((ROOT / name, "project/" + name))
for folder in ("src/sih26170", "tests", "scripts", "docs", "examples", "outputs/mlcc_v1"):
    for path in sorted((ROOT / folder).rglob("*")):
        if path.is_file() and not any(p.startswith('.') or p == '__pycache__' for p in path.relative_to(ROOT).parts) and path.suffix not in {'.pyc', '.zip'}:
            files.append((path, "project/" + str(path.relative_to(ROOT))))
for folder, prefix in (("outputs/cleaned_training_integration", "cleaned_integration"),
                       ("outputs/teammate_integration", "reference_pattern_attempt")):
    for path in sorted((ROOT / folder).rglob("*")):
        if path.is_file():
            files.append((path, prefix + '/' + str(path.relative_to(ROOT / folder))))
for name in ("01_cleaned_sorted_train_early.zip", "mlcc_generator.zip"):
    files.append((Path('/Users/saikarthik26/Downloads') / name, 'attachments/' + name))
files.append((Path('/Users/saikarthik26/Downloads/handoff.md'), 'attachments/cleaning_handoff.md'))
files.append((ROOT / 'outputs/ASHVITHA_BACKEND_STARTER_2026-09-05.zip', 'references/ASHVITHA_BACKEND_STARTER_2026-09-05.zip'))
assert len({name for _, name in files}) == len(files)
manifest = []
with ZipFile(OUTPUT, 'x', compression=ZIP_DEFLATED) as archive:
    for path, name in files:
        raw = path.read_bytes()
        archive.writestr(name, raw)
        manifest.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    archive.writestr('PACK_MANIFEST.json', json.dumps(manifest, indent=2))
with ZipFile(OUTPUT) as archive:
    assert archive.testzip() is None
print(json.dumps({'pack': str(OUTPUT), 'files': len(files) + 1, 'bytes': OUTPUT.stat().st_size,
                  'sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}, indent=2))
