"""pytest plugin for CRAP score reporting.

This module registers CLI options and provides basic lifecycle hooks.
Uses pytest_terminal_summary (with trylast=True) to run AFTER pytest-cov
has finalized its coverage data.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from pytest_crap import __version__

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.terminal import TerminalReporter


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("crap", f"CRAP score reporting v{__version__}")
    group.addoption(
        "--crap",
        action="store_true",
        default=False,
        help="Enable CRAP score reporting",
    )
    group.addoption(
        "--crap-threshold",
        action="store",
        default=30,
        type=int,
        help="CRAP threshold for highlighting (default: 30)",
    )
    group.addoption(
        "--crap-top-n",
        action="store",
        default=20,
        type=int,
        help="Number of top items to show (default: 20)",
    )


def pytest_configure(config: Config) -> None:
    if not config.getoption("--crap"):
        return
    # Mark that CRAP reporting is enabled
    setattr(config, "_pytest_crap_enabled", True)


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(
    terminalreporter: TerminalReporter, exitstatus: int, config: Config
) -> None:
    """Generate CRAP report after pytest-cov has finished.

    Using trylast=True ensures we run AFTER pytest-cov has:
    1. Stopped coverage collection
    2. Saved coverage data
    3. Generated its own report
    """
    if not getattr(config, "_pytest_crap_enabled", False):
        return

    tr = terminalreporter

    # Try to get coverage data from pytest-cov plugin
    cov_plugin = config.pluginmanager.getplugin("_cov")
    if cov_plugin is None:
        tr.write_line("")
        tr.write_sep("-", "pytest-crap: pytest-cov plugin not found; skipping CRAP report")
        tr.write_line("  Make sure to run with: pytest --cov=<package> --crap")
        return

    # Get the coverage controller from pytest-cov
    cov_controller = getattr(cov_plugin, "cov_controller", None)
    if cov_controller is None:
        tr.write_line("")
        tr.write_sep("-", "pytest-crap: coverage controller not initialized; skipping CRAP report")
        tr.write_line("  Make sure to run with: pytest --cov=<package> --crap")
        return

    # Get the coverage object from the controller
    coverage_obj = getattr(cov_controller, "cov", None)
    if coverage_obj is None:
        tr.write_line("")
        tr.write_sep("-", "pytest-crap: coverage object not found; skipping CRAP report")
        return

    try:
        # Get coverage data directly from the coverage object
        data = coverage_obj.get_data()

        # Build a mapping of filename -> set of covered lines
        file_lines: dict[str, set[int]] = {}
        for filename in data.measured_files():
            raw_lines = data.lines(filename) or []
            covered: set[int] = set(raw_lines)
            file_lines[filename] = covered

        if not file_lines:
            tr.write_line("")
            tr.write_sep("-", "pytest-crap: no coverage data found")
            return

        # Compute scores for files we can parse
        from .calculator import calculate_crap
        from .reporter import CrapReporter

        reporter = CrapReporter()
        all_scores = []

        for filename, lines in file_lines.items():
            # Skip test files and non-Python files
            if "test" in os.path.basename(filename).lower() or not filename.endswith(".py"):
                continue
            try:
                scores = calculate_crap(filename, lines)
                all_scores.extend(scores)
            except Exception as e:
                # Only show parse errors in verbose mode
                if config.option.verbose > 0:
                    tr.write_line(f"pytest-crap: could not parse {filename}: {e}")

        if not all_scores:
            tr.write_line("")
            tr.write_sep("-", "pytest-crap: no functions found to analyze")
            return

        top_n = config.getoption("--crap-top-n")
        threshold = float(config.getoption("--crap-threshold"))

        # Print a blank line for spacing before our report
        tr.write_line("")

        reporter.render_function_table(all_scores, top_n=top_n)
        reporter.render_file_summary(all_scores, top_n=top_n, threshold=threshold)
        reporter.render_folder_summary(all_scores, top_n=top_n, threshold=threshold)

    except Exception as e:
        tr.write_line("")
        tr.write_sep("-", f"pytest-crap: failed to generate CRAP report: {e}")
        # In verbose mode, show the full traceback
        if config.option.verbose > 0:
            import traceback

            tr.write_line(traceback.format_exc())
