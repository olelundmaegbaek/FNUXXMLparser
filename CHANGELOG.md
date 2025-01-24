# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-24

### Added
- Initial release of FNUX XML Parser
- Core FNUX (XML) parsing functionality for medical data. See MedCom for details.
- Configuration system with YAML support
- OpenAI integration for data processing
- Command-line interface via `fnuxxmlparser` command
- Comprehensive test suite with pytest
- Documentation in API.md
- Development tools setup:
  - Black for code formatting
  - isort for import sorting
  - mypy for type checking
  - flake8 for linting
  - pytest for testing with coverage reporting
  - pre-commit hooks for code quality

### Dependencies
- Python >=3.9 support
- OpenAI SDK >=1.0.0
- PyYAML >=6.0.1

[0.1.0]: https://github.com/username/fnuxxmlparser/releases/tag/v0.1.0
