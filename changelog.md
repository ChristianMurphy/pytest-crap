# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Support for Python 3.10 through 3.14

## [0.1.0] - 2025-11-25

### Added

- Initial beta release of pytest-crap
- CRAP (Change Risk Anti-Patterns) score calculation combining cyclomatic complexity and code coverage
- Integration with pytest and pytest-cov for automated test analysis
- Three summary tables with rich formatting:
  - **CRAP by Function**: Individual functions ranked by CRAP score
  - **CRAP by File**: Files ranked by highest CRAP score with function counts
  - **CRAP by Folder**: Directories ranked by highest CRAP score
- Command-line options:
  - `--crap`: Enable CRAP score reporting
  - `--crap-threshold`: Set threshold for highlighting high-risk functions (default: 30)
  - `--crap-top-n`: Control number of functions displayed in tables (default: 20)
- Support for Python 3.13+
- Support for pytest 7.0+
- Beautiful table output using rich formatting
- Comprehensive README with:
  - CRAP metric explanation and formula
  - Score interpretation guidelines
  - Usage examples
  - CI/CD integration examples

[Unreleased]: https://github.com/ChristianMurphy/pytest-crap/compare/v0.1.0-beta...HEAD
[0.1.0]: https://github.com/ChristianMurphy/pytest-crap/releases/tag/v0.1.0