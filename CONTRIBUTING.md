# Contributing to Lisa Loop SDK

Thanks for your interest in contributing to the Lisa Loop SDK. Whether you're fixing bugs, adding features, or building new agents — every contribution makes Lisa smarter.

## Quick Start

```bash
git clone https://github.com/LisaLoopBot/lisaloop-sdk.git
cd lisaloop-sdk
pip install -e .
pytest
```

## How to Contribute

### Bug Reports
Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your Python version and OS

### New Agents
1. Create your agent in `lisaloop/agents/`
2. Subclass `Agent` and implement `decide()`
3. Add tests in `tests/`
4. Benchmark against built-in agents: `lisaloop benchmark your_agent.py`

### New Modules
- Follow the existing patterns in `lisaloop/core/`, `lisaloop/equity/`, etc.
- Keep modules self-contained with clear `__init__.py` exports
- Add examples in `lisaloop/examples/`

### Code Style
- Type hints on all public functions
- Docstrings on modules, classes, and public methods
- No external dependencies unless absolutely necessary (stdlib first)

## Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b my-feature`
3. Make your changes
4. Run tests: `pytest`
5. Push and open a PR

Keep PRs focused — one feature or fix per PR.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
