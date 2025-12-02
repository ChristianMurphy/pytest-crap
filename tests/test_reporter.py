"""Tests for the CrapReporter rendering."""

import importlib
import tempfile
from pathlib import Path
from typing import Any

from rich.console import Console

from pytest_crap import reporter as reporter_module
from pytest_crap.calculator import FunctionScore


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


class TestCrapReporterColors:
    """Test all color branches in _color_for_crap."""

    def test_color_for_crap_green(self, monkeypatch: Any) -> None:
        """Test that crap <= 15 returns green color."""
        # Reload to capture import-time code
        importlib.reload(reporter_module)

        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        # Use a single low-crap score so it's definitely rendered
        scores = [
            make_score("low_crap_func", "f.py", 5.0, 1, 100.0),
        ]

        reporter.render_function_table(scores, top_n=10)
        out = console.export_text()

        assert "low_crap_func" in out
        assert "5.00" in out

    def test_color_for_crap_yellow(self, monkeypatch: Any) -> None:
        """Test that 15 < crap <= 30 returns yellow color."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("medium_crap_func", "f.py", 20.0, 3, 50.0),
        ]

        reporter.render_function_table(scores, top_n=10)
        out = console.export_text()

        assert "medium_crap_func" in out
        assert "20.00" in out

    def test_color_for_crap_red(self, monkeypatch: Any) -> None:
        """Test that crap > 30 returns red color."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("high_crap_func", "f.py", 50.0, 10, 0.0),
        ]

        reporter.render_function_table(scores, top_n=10)
        out = console.export_text()

        assert "high_crap_func" in out
        assert "50.00" in out

    def test_all_colors_in_file_summary(self, monkeypatch: Any) -> None:
        """Test all color branches in file summary."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        # Create scores that result in different max_crap values per file
        scores = [
            make_score("a", "green_file.py", 5.0, 1, 100.0),  # max_crap=5 (green)
            make_score("b", "yellow_file.py", 20.0, 3, 50.0),  # max_crap=20 (yellow)
            make_score("c", "red_file.py", 50.0, 10, 0.0),  # max_crap=50 (red)
        ]

        reporter.render_file_summary(scores, top_n=10, threshold=30.0)
        out = console.export_text()

        assert "green_file.py" in out
        assert "yellow_file.py" in out
        assert "red_file.py" in out

    def test_all_colors_in_folder_summary(self, monkeypatch: Any) -> None:
        """Test all color branches in folder summary."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        # Create scores that result in different max_crap values per folder
        scores = [
            make_score("a", "green_pkg/f.py", 5.0, 1, 100.0),  # max_crap=5 (green)
            make_score("b", "yellow_pkg/f.py", 20.0, 3, 50.0),  # max_crap=20 (yellow)
            make_score("c", "red_pkg/f.py", 50.0, 10, 0.0),  # max_crap=50 (red)
        ]

        reporter.render_folder_summary(scores, top_n=10, threshold=30.0)
        out = console.export_text()

        assert "green_pkg" in out
        assert "yellow_pkg" in out
        assert "red_pkg" in out


class TestTopNBranches:
    """Test both branches of if top_n: conditions."""

    def test_function_table_with_top_n_zero(self, monkeypatch: Any) -> None:
        """Test render_function_table with top_n=0 (show all)."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("a", "f.py", 10.0, 2, 80.0),
            make_score("b", "f.py", 20.0, 3, 60.0),
            make_score("c", "f.py", 30.0, 4, 40.0),
        ]

        # top_n=0 should show all items (falsy branch)
        reporter.render_function_table(scores, top_n=0)
        out = console.export_text()

        # All three should be present
        assert "a" in out
        assert "b" in out
        assert "c" in out

    def test_function_table_with_top_n_limit(self, monkeypatch: Any) -> None:
        """Test render_function_table with top_n limit (truthy branch)."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("should_show", "f.py", 50.0, 10, 0.0),
            make_score("should_hide", "f.py", 5.0, 1, 100.0),
        ]

        # top_n=1 should only show the highest
        reporter.render_function_table(scores, top_n=1)
        out = console.export_text()

        assert "should_show" in out
        # The low-crap item is cut off
        assert "should_hide" not in out

    def test_file_summary_with_top_n_zero(self, monkeypatch: Any) -> None:
        """Test render_file_summary with top_n=0 (show all)."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("a", "file1.py", 10.0, 2, 80.0),
            make_score("b", "file2.py", 20.0, 3, 60.0),
            make_score("c", "file3.py", 30.0, 4, 40.0),
        ]

        reporter.render_file_summary(scores, top_n=0, threshold=25.0)
        out = console.export_text()

        assert "file1.py" in out
        assert "file2.py" in out
        assert "file3.py" in out

    def test_file_summary_with_top_n_limit(self, monkeypatch: Any) -> None:
        """Test render_file_summary with top_n limit."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("a", "high.py", 50.0, 10, 0.0),
            make_score("b", "low.py", 5.0, 1, 100.0),
        ]

        reporter.render_file_summary(scores, top_n=1, threshold=30.0)
        out = console.export_text()

        assert "high.py" in out

    def test_folder_summary_with_top_n_zero(self, monkeypatch: Any) -> None:
        """Test render_folder_summary with top_n=0 (show all)."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("a", "pkg1/f.py", 10.0, 2, 80.0),
            make_score("b", "pkg2/f.py", 20.0, 3, 60.0),
            make_score("c", "pkg3/f.py", 30.0, 4, 40.0),
        ]

        reporter.render_folder_summary(scores, top_n=0, threshold=25.0)
        out = console.export_text()

        assert "pkg1" in out
        assert "pkg2" in out
        assert "pkg3" in out

    def test_folder_summary_with_top_n_limit(self, monkeypatch: Any) -> None:
        """Test render_folder_summary with top_n limit."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("a", "high_pkg/f.py", 50.0, 10, 0.0),
            make_score("b", "low_pkg/f.py", 5.0, 1, 100.0),
        ]

        reporter.render_folder_summary(scores, top_n=1, threshold=30.0)
        out = console.export_text()

        assert "high_pkg" in out


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_crap_exactly_at_boundaries(self, monkeypatch: Any) -> None:
        """Test color boundaries: crap=15 should be green, crap=30 should be yellow."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores = [
            make_score("at_15", "f.py", 15.0, 2, 50.0),  # crap=15, should be green (not > 15)
            make_score("at_30", "f.py", 30.0, 4, 25.0),  # crap=30, should be yellow (not > 30)
            make_score("at_31", "f.py", 31.0, 5, 20.0),  # crap=31, should be red (> 30)
        ]

        reporter.render_function_table(scores, top_n=0)
        out = console.export_text()

        assert "at_15" in out
        assert "at_30" in out
        assert "at_31" in out

    def test_threshold_counting(self, monkeypatch: Any) -> None:
        """Test that count_above threshold works correctly."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        # All in same file, various crap scores
        scores = [
            make_score("below", "f.py", 25.0, 3, 50.0),  # below threshold
            make_score("at", "f.py", 30.0, 4, 40.0),  # at threshold (>= counts)
            make_score("above", "f.py", 35.0, 5, 30.0),  # above threshold
        ]

        reporter.render_file_summary(scores, top_n=0, threshold=30.0)
        out = console.export_text()

        # Should show count of 2 (at and above)
        assert "2" in out

    def test_empty_scores(self, monkeypatch: Any) -> None:
        """Test rendering with empty scores list."""
        reporter = reporter_module.CrapReporter()
        console = Console(record=True)
        monkeypatch.setattr(reporter, "console", console)

        scores: list[FunctionScore] = []

        reporter.render_function_table(scores, top_n=10)
        reporter.render_file_summary(scores, top_n=10, threshold=30.0)
        reporter.render_folder_summary(scores, top_n=10, threshold=30.0)

        out = console.export_text()
        # Should still render the table headers
        assert "CRAP by Function" in out
        assert "CRAP by File" in out
        assert "CRAP by Folder" in out


class TestRelativePaths:
    """Test relative path functionality."""

    def test_relative_path_with_rootdir(self) -> None:
        """Test that paths are made relative when rootdir is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rootdir = Path(tmpdir)
            reporter = reporter_module.CrapReporter(rootdir=str(rootdir))

            # Create a test file path inside the tmpdir
            test_file = rootdir / "src" / "module.py"

            # Should return relative path
            rel = reporter._relative_path(str(test_file))
            assert rel == "src/module.py"

    def test_relative_path_without_rootdir(self) -> None:
        """Test that absolute paths are returned when no rootdir is set."""
        reporter = reporter_module.CrapReporter(rootdir=None)

        test_path = "/absolute/path/to/file.py"
        result = reporter._relative_path(test_path)

        # Should return the original path unchanged
        assert result == test_path

    def test_relative_path_outside_rootdir(self) -> None:
        """Test that paths outside rootdir return original path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rootdir = Path(tmpdir) / "project"
            rootdir.mkdir()
            reporter = reporter_module.CrapReporter(rootdir=str(rootdir))

            # Path outside rootdir
            outside_path = "/some/other/path/file.py"
            result = reporter._relative_path(outside_path)

            # Should return original path
            assert result == outside_path

    def test_truncate_middle_short_text(self) -> None:
        """Test truncate_middle with text shorter than max_length."""
        reporter = reporter_module.CrapReporter()

        result = reporter._truncate_middle("short.py", 50)
        assert result == "short.py"

    def test_truncate_middle_long_text(self) -> None:
        """Test truncate_middle with text longer than max_length."""
        reporter = reporter_module.CrapReporter()

        long_text = "very/long/path/to/some/deeply/nested/file.py"
        result = reporter._truncate_middle(long_text, 20)

        # Should be exactly 20 characters
        assert len(result) == 20
        # Should contain ellipsis
        assert "..." in result
        # Should start with beginning and end with ending
        assert result.startswith("very/long")
        assert result.endswith("file.py")

    def test_truncate_middle_very_short_max(self) -> None:
        """Test truncate_middle with very short max_length."""
        reporter = reporter_module.CrapReporter()

        result = reporter._truncate_middle("filename.py", 3)
        # Should return first 3 chars when max <= 3
        assert result == "fil"
