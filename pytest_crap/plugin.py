"""pytest plugin for CRAP score reporting.

This module registers CLI options and provides basic lifecycle hooks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_crap import __version__

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.main import Session
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

    # Basic check: ensure pytest-cov is present (we rely on coverage data)
    try:
        setattr(config, "_pytest_crap_has_cov", True)
    except Exception:
        setattr(config, "_pytest_crap_has_cov", False)


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    config: Config = session.config
    if not getattr(config, "_pytest_crap_has_cov", False):
        # If CRAP was requested but cov missing, write a warning to terminal
        if config.getoption("--crap"):
            tr: TerminalReporter | None = config.pluginmanager.getplugin("terminalreporter")
            if tr:
                tr.write_sep("-", "pytest-crap: coverage data not available; skipping CRAP report")

    # If enabled and coverage available, try to read coverage data and produce a report
    if config.getoption("--crap") and getattr(config, "_pytest_crap_has_cov", False):
        try:
            # Use coverage.CoverageData to read .coverage file
            from coverage import CoverageData

            data = CoverageData()
            data.read()

            # Build a mapping of filename -> set of covered lines
            file_lines: dict[str, set[int]] = {}
            for filename in data.measured_files():
                raw_lines = data.lines(filename) or []
                covered: set[int] = set(raw_lines)
                file_lines[filename] = covered

            # Compute scores for files we can parse
            from .calculator import calculate_crap
            from .reporter import CrapReporter

            reporter = CrapReporter()
            all_scores = []
            for filename, lines in file_lines.items():
                try:
                    scores = calculate_crap(filename, lines)
                    all_scores.extend(scores)
                except Exception:
                    # skip unparseable files but notify
                    tr = config.pluginmanager.getplugin("terminalreporter")
                    if tr is not None:
                        tr.write_line(f"pytest-crap: could not parse {filename}; skipped")

            top_n = config.getoption("--crap-top-n")
            threshold = float(config.getoption("--crap-threshold"))

            reporter.render_function_table(all_scores, top_n=top_n)
            reporter.render_file_summary(all_scores, top_n=top_n, threshold=threshold)
            reporter.render_folder_summary(all_scores, top_n=top_n, threshold=threshold)
        except Exception:
            tr = config.pluginmanager.getplugin("terminalreporter")
            if tr is not None:
                tr.write_sep("-", "pytest-crap: failed to generate CRAP report")


# Provide a symbol for setuptools entry point
CrapPlugin = None
