"""Tests for the CrapReporter rendering."""

from typing import Any

from rich.console import Console

from pytest_crap.calculator import FunctionScore
from pytest_crap.reporter import CrapReporter


def make_score(name: str, file: str, crap: float, cc: int, cov: float) -> FunctionScore:
    return FunctionScore(
        name=name,
        file_path=file,
        start_line=1,
        end_line=1,
        cc=cc,
        coverage_percent=cov,
        crap=crap,
    )


def test_function_table_renders(monkeypatch: Any) -> None:
    reporter = CrapReporter()
    # use a Console to capture output
    console = Console(record=True)
    monkeypatch.setattr(reporter, "console", console)

    scores = [
        make_score("a", "f.py", 5.0, 1, 100.0),
        make_score("b", "f.py", 20.0, 3, 50.0),
        make_score("c", "g.py", 40.0, 8, 0.0),
    ]

    reporter.render_function_table(scores, top_n=2)
    out = console.export_text()
    assert "CRAP by Function" in out
    assert "a" in out or "b" in out


def test_file_and_folder_summary(monkeypatch: Any) -> None:
    reporter = CrapReporter()
    console = Console(record=True)
    monkeypatch.setattr(reporter, "console", console)

    scores = [
        make_score("a", "pkg/f1.py", 10.0, 1, 90.0),
        make_score("b", "pkg/f1.py", 35.0, 5, 0.0),
        make_score("c", "pkg/sub/f2.py", 40.0, 7, 10.0),
    ]

    reporter.render_file_summary(scores, top_n=10, threshold=30.0)
    reporter.render_folder_summary(scores, top_n=10, threshold=30.0)

    out = console.export_text()
    assert "CRAP by File" in out
    assert "CRAP by Folder" in out
    assert "pkg/f1.py" in out or "pkg/sub/f2.py" in out


def test_render_with_no_limit(monkeypatch: Any) -> None:
    """Test rendering without top_n limit (0 or None)."""
    reporter = CrapReporter()
    console = Console(record=True)
    monkeypatch.setattr(reporter, "console", console)

    scores = [
        make_score("a", "pkg/f1.py", 10.0, 1, 90.0),
        make_score("b", "pkg/f1.py", 35.0, 5, 0.0),
        make_score("c", "pkg/sub/f2.py", 40.0, 7, 10.0),
    ]

    # Test with top_n=0 to hit the other branch
    reporter.render_function_table(scores, top_n=0)
    reporter.render_file_summary(scores, top_n=0, threshold=30.0)
    reporter.render_folder_summary(scores, top_n=0, threshold=30.0)

    out = console.export_text()
    assert "CRAP by Function" in out
