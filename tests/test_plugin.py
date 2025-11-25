"""Unit tests for pytest-crap plugin module.

These tests directly test the plugin functions with mocked pytest objects,
ensuring coverage is collected in-process rather than relying on subprocess
coverage collection from pytester-based integration tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from pytest_crap import plugin


class TestPytestAddoption:
    """Tests for pytest_addoption hook."""

    def test_registers_crap_group(self) -> None:
        """Verify --crap options are registered."""
        parser = MagicMock()
        group = MagicMock()
        parser.getgroup.return_value = group

        plugin.pytest_addoption(parser)

        parser.getgroup.assert_called_once()
        # Should register 3 options: --crap, --crap-threshold, --crap-top-n
        assert group.addoption.call_count == 3

    def test_crap_option_defaults(self) -> None:
        """Verify option defaults are set correctly."""
        parser = MagicMock()
        group = MagicMock()
        parser.getgroup.return_value = group

        plugin.pytest_addoption(parser)

        calls = group.addoption.call_args_list
        # Extract the kwargs from each call
        options = {call[0][0]: call[1] for call in calls}

        assert "--crap" in options
        assert options["--crap"]["default"] is False
        assert options["--crap"]["action"] == "store_true"

        assert "--crap-threshold" in options
        assert options["--crap-threshold"]["default"] == 30

        assert "--crap-top-n" in options
        assert options["--crap-top-n"]["default"] == 20


class TestPytestConfigure:
    """Tests for pytest_configure hook."""

    def test_does_nothing_when_crap_disabled(self) -> None:
        """When --crap is not set, should not set _pytest_crap_enabled."""

        # Use a real object to verify setattr isn't called
        class FakeConfig:
            def getoption(self, name: str) -> bool:
                return False

        config = FakeConfig()

        plugin.pytest_configure(config)

        # _pytest_crap_enabled should not be set when --crap is False
        assert not hasattr(config, "_pytest_crap_enabled")

    def test_sets_enabled_flag_when_crap_enabled(self) -> None:
        """When --crap is set, should set _pytest_crap_enabled = True."""
        config = MagicMock(spec=[])  # Empty spec so setattr works normally
        config.getoption = MagicMock(return_value=True)

        plugin.pytest_configure(config)

        assert getattr(config, "_pytest_crap_enabled", False) is True


class TestPytestTerminalSummary:
    """Tests for pytest_terminal_summary hook."""

    def _make_mocks(
        self,
        crap_enabled: bool = True,
        cov_plugin: Any = "present",
        cov_controller: Any = "present",
        coverage_obj: Any = "present",
        measured_files: list[str] | None = None,
        file_lines: dict[str, list[int]] | None = None,
    ) -> tuple[MagicMock, MagicMock]:
        """Create mock terminalreporter and config objects."""
        tr = MagicMock()
        config = MagicMock()

        # Set _pytest_crap_enabled attribute
        config._pytest_crap_enabled = crap_enabled

        # Configure verbose option
        config.option = MagicMock()
        config.option.verbose = 0

        # Configure getoption for threshold and top_n
        def getoption_side_effect(opt: str) -> Any:
            if opt == "--crap-top-n":
                return 20
            if opt == "--crap-threshold":
                return 30
            return None

        config.getoption = MagicMock(side_effect=getoption_side_effect)

        # Configure plugin manager
        if cov_plugin == "present":
            mock_cov_plugin = MagicMock()
            if cov_controller == "present":
                mock_controller = MagicMock()
                if coverage_obj == "present":
                    mock_cov = MagicMock()
                    mock_data = MagicMock()

                    # Default to some measured files if not specified
                    if measured_files is None:
                        measured_files = []
                    mock_data.measured_files.return_value = measured_files

                    # Setup lines() to return specified lines
                    if file_lines is None:
                        file_lines = {}

                    def lines_side_effect(filename: str) -> list[int]:
                        return file_lines.get(filename, [])

                    mock_data.lines = MagicMock(side_effect=lines_side_effect)
                    mock_cov.get_data.return_value = mock_data
                    mock_controller.cov = mock_cov
                else:
                    mock_controller.cov = None
                mock_cov_plugin.cov_controller = mock_controller
            else:
                mock_cov_plugin.cov_controller = None
            config.pluginmanager.getplugin.return_value = mock_cov_plugin
        else:
            config.pluginmanager.getplugin.return_value = None

        return tr, config

    def test_returns_early_when_crap_disabled(self) -> None:
        """When _pytest_crap_enabled is False, should return immediately."""
        tr, config = self._make_mocks(crap_enabled=False)

        plugin.pytest_terminal_summary(tr, 0, config)

        # Should not write anything
        tr.write_line.assert_not_called()
        tr.write_sep.assert_not_called()

    def test_warns_when_cov_plugin_missing(self) -> None:
        """When pytest-cov plugin is not found, should warn."""
        tr, config = self._make_mocks(cov_plugin=None)

        plugin.pytest_terminal_summary(tr, 0, config)

        # Should warn about missing plugin
        tr.write_sep.assert_called()
        call_args = tr.write_sep.call_args[0]
        assert "pytest-cov plugin not found" in call_args[1]

    def test_warns_when_cov_controller_missing(self) -> None:
        """When coverage controller is not initialized, should warn."""
        tr, config = self._make_mocks(cov_controller=None)

        plugin.pytest_terminal_summary(tr, 0, config)

        # Should warn about missing controller
        tr.write_sep.assert_called()
        call_args = tr.write_sep.call_args[0]
        assert "coverage controller not initialized" in call_args[1]

    def test_warns_when_coverage_obj_missing(self) -> None:
        """When coverage object is not found, should warn."""
        tr, config = self._make_mocks(coverage_obj=None)

        plugin.pytest_terminal_summary(tr, 0, config)

        # Should warn about missing coverage object
        tr.write_sep.assert_called()
        call_args = tr.write_sep.call_args[0]
        assert "coverage object not found" in call_args[1]

    def test_warns_when_no_coverage_data(self) -> None:
        """When no files have coverage data, should warn."""
        tr, config = self._make_mocks(measured_files=[])

        plugin.pytest_terminal_summary(tr, 0, config)

        # Should warn about no coverage data
        tr.write_sep.assert_called()
        call_args = tr.write_sep.call_args[0]
        assert "no coverage data found" in call_args[1]

    def test_skips_test_files(self) -> None:
        """Test files should be skipped from analysis."""
        tr, config = self._make_mocks(
            measured_files=["/path/to/test_something.py"],
            file_lines={"/path/to/test_something.py": [1, 2, 3]},
        )

        plugin.pytest_terminal_summary(tr, 0, config)

        # Should warn about no functions found (test files skipped)
        tr.write_sep.assert_called()
        call_args = tr.write_sep.call_args[0]
        assert "no functions found to analyze" in call_args[1]

    def test_skips_non_python_files(self) -> None:
        """Non-Python files should be skipped from analysis."""
        tr, config = self._make_mocks(
            measured_files=["/path/to/data.txt", "/path/to/config.json"],
            file_lines={
                "/path/to/data.txt": [1, 2, 3],
                "/path/to/config.json": [1, 2],
            },
        )

        plugin.pytest_terminal_summary(tr, 0, config)

        # Should warn about no functions found
        tr.write_sep.assert_called()
        call_args = tr.write_sep.call_args[0]
        assert "no functions found to analyze" in call_args[1]

    @patch("pytest_crap.calculator.calculate_crap")
    @patch("pytest_crap.reporter.CrapReporter")
    def test_successful_report_generation(
        self, mock_reporter_cls: MagicMock, mock_calculate: MagicMock
    ) -> None:
        """When everything works, should generate CRAP report."""
        import os
        import tempfile

        # Create a real temporary Python file for the test
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(): pass\n")
            temp_file = f.name

        try:
            tr, config = self._make_mocks(
                measured_files=[temp_file],
                file_lines={temp_file: [1]},
            )

            # Mock calculate_crap to return some scores
            mock_score = MagicMock()
            mock_score.crap = 5.0
            mock_calculate.return_value = [mock_score]

            # Mock the reporter
            mock_reporter = MagicMock()
            mock_reporter_cls.return_value = mock_reporter

            plugin.pytest_terminal_summary(tr, 0, config)

            # Should have called calculate_crap
            mock_calculate.assert_called()

            # Should have rendered reports
            mock_reporter.render_function_table.assert_called_once()
            mock_reporter.render_file_summary.assert_called_once()
            mock_reporter.render_folder_summary.assert_called_once()
        finally:
            os.unlink(temp_file)

    @patch("pytest_crap.calculator.calculate_crap")
    def test_handles_parse_errors_gracefully(self, mock_calculate: MagicMock) -> None:
        """Parse errors should be handled gracefully."""
        import os
        import tempfile

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(): pass\n")
            temp_file = f.name

        try:
            tr, config = self._make_mocks(
                measured_files=[temp_file],
                file_lines={temp_file: [1]},
            )

            # Make calculate_crap raise an exception
            mock_calculate.side_effect = SyntaxError("parse error")

            plugin.pytest_terminal_summary(tr, 0, config)

            # Should warn about no functions found (due to parse error)
            tr.write_sep.assert_called()
        finally:
            os.unlink(temp_file)

    @patch("pytest_crap.calculator.calculate_crap")
    def test_verbose_mode_shows_parse_errors(self, mock_calculate: MagicMock) -> None:
        """In verbose mode, parse errors should be shown."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(): pass\n")
            temp_file = f.name

        try:
            tr, config = self._make_mocks(
                measured_files=[temp_file],
                file_lines={temp_file: [1]},
            )
            config.option.verbose = 1  # Enable verbose mode

            mock_calculate.side_effect = SyntaxError("parse error")

            plugin.pytest_terminal_summary(tr, 0, config)

            # Should have written the error message
            write_line_calls = [str(call) for call in tr.write_line.call_args_list]
            assert any("could not parse" in call for call in write_line_calls)
        finally:
            os.unlink(temp_file)

    @patch("pytest_crap.calculator.calculate_crap")
    @patch("pytest_crap.reporter.CrapReporter")
    def test_exception_during_report_shows_error(
        self, mock_reporter_cls: MagicMock, mock_calculate: MagicMock
    ) -> None:
        """Exceptions during report generation should show error message."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(): pass\n")
            temp_file = f.name

        try:
            tr, config = self._make_mocks(
                measured_files=[temp_file],
                file_lines={temp_file: [1]},
            )

            mock_score = MagicMock()
            mock_score.crap = 5.0
            mock_calculate.return_value = [mock_score]

            # Make reporter raise an exception
            mock_reporter = MagicMock()
            mock_reporter.render_function_table.side_effect = RuntimeError("render failed")
            mock_reporter_cls.return_value = mock_reporter

            plugin.pytest_terminal_summary(tr, 0, config)

            # Should show error message
            tr.write_sep.assert_called()
            call_args = tr.write_sep.call_args[0]
            assert "failed to generate CRAP report" in call_args[1]
        finally:
            os.unlink(temp_file)

    @patch("pytest_crap.calculator.calculate_crap")
    @patch("pytest_crap.reporter.CrapReporter")
    def test_verbose_exception_shows_traceback(
        self, mock_reporter_cls: MagicMock, mock_calculate: MagicMock
    ) -> None:
        """In verbose mode, exceptions should show full traceback."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(): pass\n")
            temp_file = f.name

        try:
            tr, config = self._make_mocks(
                measured_files=[temp_file],
                file_lines={temp_file: [1]},
            )
            config.option.verbose = 1

            mock_score = MagicMock()
            mock_score.crap = 5.0
            mock_calculate.return_value = [mock_score]

            mock_reporter = MagicMock()
            mock_reporter.render_function_table.side_effect = RuntimeError("render failed")
            mock_reporter_cls.return_value = mock_reporter

            plugin.pytest_terminal_summary(tr, 0, config)

            # Should have written traceback
            write_line_calls = [str(call) for call in tr.write_line.call_args_list]
            assert any("Traceback" in call or "RuntimeError" in call for call in write_line_calls)
        finally:
            os.unlink(temp_file)

    @patch("pytest_crap.calculator.calculate_crap")
    @patch("pytest_crap.reporter.CrapReporter")
    def test_respects_top_n_and_threshold_options(
        self, mock_reporter_cls: MagicMock, mock_calculate: MagicMock
    ) -> None:
        """Options --crap-top-n and --crap-threshold should be passed to reporter."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(): pass\n")
            temp_file = f.name

        try:
            tr, config = self._make_mocks(
                measured_files=[temp_file],
                file_lines={temp_file: [1]},
            )

            # Custom option values
            def getoption_side_effect(opt: str) -> Any:
                if opt == "--crap-top-n":
                    return 10
                if opt == "--crap-threshold":
                    return 25
                return None

            config.getoption = MagicMock(side_effect=getoption_side_effect)

            mock_score = MagicMock()
            mock_score.crap = 5.0
            mock_calculate.return_value = [mock_score]

            mock_reporter = MagicMock()
            mock_reporter_cls.return_value = mock_reporter

            plugin.pytest_terminal_summary(tr, 0, config)

            # Check that options were passed correctly
            mock_reporter.render_function_table.assert_called_once()
            assert mock_reporter.render_function_table.call_args[1]["top_n"] == 10

            mock_reporter.render_file_summary.assert_called_once()
            call_kwargs = mock_reporter.render_file_summary.call_args[1]
            assert call_kwargs["top_n"] == 10
            assert call_kwargs["threshold"] == 25.0
        finally:
            os.unlink(temp_file)


class TestVersionImport:
    """Test version is accessible."""

    def test_version_in_plugin(self) -> None:
        """Version should be imported in plugin module."""
        from pytest_crap import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)


class TestModuleImport:
    """Test module import to capture import-time coverage."""

    def test_plugin_module_imports(self) -> None:
        """Reload plugin module to capture import-time code coverage."""
        import importlib

        import pytest_crap.plugin

        # Reload to execute import-time code while coverage is active
        importlib.reload(pytest_crap.plugin)

        # Verify expected attributes exist after reload
        assert hasattr(pytest_crap.plugin, "pytest_addoption")
        assert hasattr(pytest_crap.plugin, "pytest_configure")
        assert hasattr(pytest_crap.plugin, "pytest_terminal_summary")
