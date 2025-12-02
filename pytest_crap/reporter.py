"""Terminal reporter using rich for CRAP scores."""

import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .calculator import FunctionScore


@dataclass
class FileSummary:
    file: str
    max_crap: float
    count_above: int


class CrapReporter:
    """Render CRAP tables for functions, files and folders."""

    def __init__(self, rootdir: str | None = None) -> None:
        """Initialize reporter.

        Args:
            rootdir: Project root directory for relative path display.
                    If None, paths will be displayed as absolute.
        """
        # Get terminal width, with minimum of 80 and reasonable maximum
        width = max(80, min(shutil.get_terminal_size().columns, 200))
        self.console = Console(width=width)
        self.rootdir = Path(rootdir).resolve() if rootdir else None

    def _color_for_crap(self, crap: float) -> str:
        if crap > 30:
            return "red"
        if crap > 15:
            return "yellow"
        return "green"

    def _relative_path(self, path: str) -> str:
        """Convert absolute path to relative path from rootdir.

        Args:
            path: Absolute file path

        Returns:
            Relative path from rootdir, or original path if rootdir not set
            or path is outside rootdir.
        """
        if not self.rootdir:
            return path

        try:
            path_obj = Path(path).resolve()
            rel_path = path_obj.relative_to(self.rootdir)
            return str(rel_path)
        except (ValueError, OSError):
            # Path is outside rootdir or cannot be resolved
            return path

    def _truncate_middle(self, text: str, max_length: int) -> str:
        """Truncate text in the middle with ellipsis if too long.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text with '...' in the middle if needed
        """
        if len(text) <= max_length:
            return text

        if max_length <= 3:
            return text[:max_length]

        # Reserve 3 chars for '...'
        available = max_length - 3
        left_size = (available + 1) // 2
        right_size = available - left_size

        return f"{text[:left_size]}...{text[-right_size:]}"

    def render_function_table(self, scores: Iterable[FunctionScore], top_n: int = 20) -> None:
        table = Table(title="CRAP by Function", expand=True)
        table.add_column("CRAP", justify="right", no_wrap=True)
        table.add_column("CC", justify="right", no_wrap=True)
        table.add_column("Coverage", justify="right", no_wrap=True)
        table.add_column("Function", no_wrap=True)
        table.add_column("File")

        rows = sorted(scores, key=lambda x: x.crap, reverse=True)
        if top_n:
            rows = rows[:top_n]

        for row in rows:
            color = self._color_for_crap(row.crap)
            coverage_str = f"{row.coverage_percent:.1f}%"
            rel_path = self._relative_path(row.file_path)

            table.add_row(
                f"[{color}]{row.crap:.2f}[/{color}]",
                str(row.cc),
                coverage_str,
                row.name,
                rel_path,
            )

        self.console.print(table)

    def render_file_summary(
        self,
        scores: Iterable[FunctionScore],
        top_n: int = 20,
        threshold: float = 30.0,
    ) -> None:
        # Aggregate by file
        by_file: dict[str, list[FunctionScore]] = {}
        for s in scores:
            by_file.setdefault(s.file_path, []).append(s)

        summaries: list[FileSummary] = []
        for file, funcs in by_file.items():
            max_crap = max(f.crap for f in funcs)
            count_above = sum(1 for f in funcs if f.crap >= threshold)
            summaries.append(FileSummary(file=file, max_crap=max_crap, count_above=count_above))

        summaries.sort(key=lambda x: x.max_crap, reverse=True)
        if top_n:
            summaries = summaries[:top_n]

        table = Table(title="CRAP by File", expand=True)
        table.add_column("CRAP (max)", justify="right", no_wrap=True)
        table.add_column("#>=thr", justify="right", no_wrap=True)
        table.add_column("File")

        for summary in summaries:
            color = self._color_for_crap(summary.max_crap)
            rel_path = self._relative_path(summary.file)

            table.add_row(
                f"[{color}]{summary.max_crap:.2f}[/{color}]",
                str(summary.count_above),
                rel_path,
            )

        self.console.print(table)

    def render_folder_summary(
        self,
        scores: Iterable[FunctionScore],
        top_n: int = 20,
        threshold: float = 30.0,
    ) -> None:
        # Aggregate by parent folder
        by_folder: dict[str, list[FunctionScore]] = {}
        for s in scores:
            folder = str(Path(s.file_path).parent)
            by_folder.setdefault(folder, []).append(s)

        summaries: list[FileSummary] = []
        for folder, funcs in by_folder.items():
            max_crap = max(f.crap for f in funcs)
            count_above = sum(1 for f in funcs if f.crap >= threshold)
            summaries.append(FileSummary(file=folder, max_crap=max_crap, count_above=count_above))

        summaries.sort(key=lambda x: x.max_crap, reverse=True)
        if top_n:
            summaries = summaries[:top_n]

        table = Table(title="CRAP by Folder", expand=True)
        table.add_column("CRAP (max)", justify="right", no_wrap=True)
        table.add_column("#>=thr", justify="right", no_wrap=True)
        table.add_column("Folder")

        for summary in summaries:
            color = self._color_for_crap(summary.max_crap)
            rel_path = self._relative_path(summary.file)

            table.add_row(
                f"[{color}]{summary.max_crap:.2f}[/{color}]",
                str(summary.count_above),
                rel_path,
            )

        self.console.print(table)
