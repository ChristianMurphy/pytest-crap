"""Terminal reporter using rich for CRAP scores."""

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

    def __init__(self) -> None:
        self.console = Console()

    def _color_for_crap(self, crap: float) -> str:
        if crap > 30:
            return "red"
        if crap > 15:
            return "yellow"
        return "green"

    def render_function_table(self, scores: Iterable[FunctionScore], top_n: int = 20) -> None:
        table = Table(title="CRAP by Function")
        table.add_column("CRAP", justify="right")
        table.add_column("CC", justify="right")
        table.add_column("Coverage", justify="right")
        table.add_column("Function")
        table.add_column("File")

        rows = sorted(scores, key=lambda x: x.crap, reverse=True)
        if top_n:
            rows = rows[:top_n]

        for row in rows:
            color = self._color_for_crap(row.crap)
            coverage_str = f"{row.coverage_percent:.1f}%"
            table.add_row(
                f"[{color}]{row.crap:.2f}[/{color}]",
                str(row.cc),
                coverage_str,
                row.name,
                row.file_path,
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

        table = Table(title="CRAP by File")
        table.add_column("CRAP (max)", justify="right")
        table.add_column("#>=thr", justify="right")
        table.add_column("File")

        for summary in summaries:
            color = self._color_for_crap(summary.max_crap)
            table.add_row(
                f"[{color}]{summary.max_crap:.2f}[/{color}]",
                str(summary.count_above),
                summary.file,
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

        table = Table(title="CRAP by Folder")
        table.add_column("CRAP (max)", justify="right")
        table.add_column("#>=thr", justify="right")
        table.add_column("Folder")

        for summary in summaries:
            color = self._color_for_crap(summary.max_crap)
            table.add_row(
                f"[{color}]{summary.max_crap:.2f}[/{color}]",
                str(summary.count_above),
                summary.file,
            )

        self.console.print(table)
