"""Verify the frozen v1.9 import in two independent working copies."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

EXPECTED = 158
REPORTS = (
    "FORSCHUNGSRAT_1_9.json",
    "FORSCHUNGSRAT_1_9.html",
    "FORSCHUNGSRAT_1_9_AUFGABEN.csv",
)


def run_board(project):
    for name in REPORTS:
        (project / "reports" / name).unlink(missing_ok=True)
    subprocess.run([sys.executable, "research_board_v19.py"], cwd=project,
                   check=True, timeout=120)
    for name in REPORTS:
        if not (project / "reports" / name).stat().st_size:
            raise RuntimeError(f"Empty report: {name}")
    board = json.loads((project / "reports" / REPORTS[0]).read_text(encoding="utf-8"))
    if board["technical_candidate_gate"] != "PASS" or not board["baseline_unchanged"]:
        raise RuntimeError("Council failed or frozen reference changed")
    return board["technical_tests"]["tests_run"]


def check_count(count):
    if count != EXPECTED:
        raise ValueError(f"Expected {EXPECTED} tests, ran {count}")


def verify(source, output):
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        project = root / "positive"
        shutil.copytree(source, project)
        count = run_board(project)
        check_count(count)
        negative = root / "negative"
        shutil.copytree(source, negative)
        module = negative / "tests" / "test_v19.py"
        code = module.read_text(encoding="utf-8")
        marker = "def test_four_separate_roles_present("
        if code.count(marker) != 1:
            raise RuntimeError("Missing negative-control fixture")
        module.write_text(code.replace(marker, "def omitted_four_separate_roles_present("),
                          encoding="utf-8")
        reduced = run_board(negative)
        if reduced != EXPECTED - 1:
            raise RuntimeError(f"Negative control ran {reduced} tests")
        try:
            check_count(reduced)
        except ValueError as exc:
            print(f"Negative control rejected as expected: {exc}", flush=True)
        else:
            raise RuntimeError("Incomplete suite was accepted")
        output.mkdir(parents=True, exist_ok=True)
        for name in REPORTS:
            shutil.copyfile(project / "reports" / name, output / name)
        print(f"Verified {count} tests and three newly generated reports.")


if __name__ == "__main__":
    os.environ["ALI_OFFLINE_ONLY"] = "1"
    verify(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
