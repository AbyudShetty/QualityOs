"""Collect actual reviewed outputs and verify preserved source integrity."""
import hashlib
import json
import shutil
from pathlib import Path

from qualityos.evaluation import run_evaluation
from qualityos.security import utcnow

root = Path(__file__).resolve().parents[1]
output = root / "docs/validation"
output.mkdir(parents=True, exist_ok=True)
manifest = json.loads((root / "docs/SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
integrity = []
for item in manifest["files"]:
    source = root.parent / item["path"]
    if not source.exists():
        integrity.append({"path": item["path"], "expected_sha256": item["sha256"], "matched": False, "status": "MISSING_LOCAL_SOURCE"})
        continue
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    integrity.append({"path": item["path"], "sha256": actual, "matched": actual == item["sha256"]})
if any(not x["matched"] and x.get("status") != "MISSING_LOCAL_SOURCE" for x in integrity):
    raise RuntimeError("A preserved source differs; investigate instead of certifying integrity")
(output / "source-integrity.json").write_text(json.dumps({"checked_at": utcnow(), "files": integrity, "all_available_matched": True, "all_manifest_files_present": all(x["matched"] for x in integrity), "matched_count": sum(x["matched"] for x in integrity), "missing_count": sum(x.get("status") == "MISSING_LOCAL_SOURCE" for x in integrity)}, indent=2), encoding="utf-8")
evaluation = run_evaluation()
if evaluation["passed"] != evaluation["total"]:
    raise RuntimeError("Independent declared corpus did not match")
(output / "evaluation-v1.json").write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
for source, destination in [("browser-report.json", "browser.json"), ("contrast-report.json", "contrast.json")]:
    report = json.loads((root / "var/browser-review" / source).read_text(encoding="utf-8"))
    if report.get("failure") or report.get("errors"):
        raise RuntimeError("Browser report contains a failure")
    if any(x.get("failures") for x in report.get("reports", [])):
        raise RuntimeError("Contrast screen contains a failure")
    (output / destination).write_text(json.dumps(report, indent=2), encoding="utf-8")
screens = output / "screenshots"
screens.mkdir(exist_ok=True)
for name in ["01-line-ready", "04-investigation", "05-qualification", "07-evidence", "390-qualification"]:
    shutil.copyfile(root / "var/browser-review" / (name + ".png"), screens / (name + ".png"))
print(f"Verified {sum(x['matched'] for x in integrity)} original source hashes; {sum(x.get('status') == 'MISSING_LOCAL_SOURCE' for x in integrity)} source file missing locally. Collected actual evaluation, browser, contrast and screenshots.")
