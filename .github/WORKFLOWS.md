# GitHub Actions Workflows

This project uses GitHub Actions for continuous integration and testing.

## Available Workflows

### 1. **Tests** (`tests.yml`)
Comprehensive test suite across multiple platforms and Python versions.

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches

**Features:**
- ✅ Tests on multiple OS: Ubuntu, Windows, macOS
- ✅ Tests on multiple Python versions: 3.11, 3.12
- ✅ Code quality checks (black, mypy)
- ✅ Unit tests (fast feedback)
- ✅ Integration tests
- ✅ End-to-end tests
- ✅ Coverage reporting with Codecov
- ✅ Minimum coverage threshold (85%)
- ✅ Separate code-quality job

**Coverage Requirements:**
- **Unit Tests**: ≥95% coverage required
- **Integration Tests**: ≥80% coverage required
- **E2E Tests**: ≥70% coverage required
- **Overall**: ≥85% minimum, >90% target

### 2. **Python Application** (`python-app.yml`)
Quick CI pipeline for primary branch testing.

**Triggers:**
- Push to `main` or `master`
- Pull requests to `main` or `master`

**Features:**
- ✅ Fast feedback on main branch
- ✅ All test layers (unit, integration, E2E)
- ✅ Coverage reporting
- ✅ Type checking and formatting

---

## Workflow Status Badges

Add these badges to your README.md to show CI status:

### Tests Workflow
```markdown
[![Tests](https://github.com/yourusername/eventcamera/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/eventcamera/actions/workflows/tests.yml)
```

### Python Application
```markdown
[![Python Application](https://github.com/yourusername/eventcamera/actions/workflows/python-app.yml/badge.svg)](https://github.com/yourusername/eventcamera/actions/workflows/python-app.yml)
```

### Combined Status
```markdown
![CI Status](https://github.com/yourusername/eventcamera/actions/workflows/tests.yml/badge.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)
![Coverage](https://img.shields.io/badge/coverage->90%25-brightgreen)
```

---

## Local Testing Before Push

Before pushing code, run locally to catch issues early:

```bash
# Install dependencies
uv sync

# Format code
uv run black src/ tests/

# Type check
uv run mypy src/

# Run all tests with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Check coverage threshold
uv run pytest tests/ --cov=src --cov-fail-under=85
```

---

## Workflow Stages

### Stage 1: Format Check
```bash
uv run black --check src/ tests/
```
- Ensures code follows Black style guide
- Non-blocking (continues on error)

### Stage 2: Type Checking
```bash
uv run mypy src/
```
- Static type analysis
- Catches type-related bugs
- Non-blocking (continues on error)

### Stage 3: Unit Tests
```bash
uv run pytest tests/unit/ -v
```
- Fast, isolated component tests
- Provides quick feedback
- ~95% coverage target

### Stage 4: Integration Tests
```bash
uv run pytest tests/integration/ -v
```
- Cross-component pipeline tests
- Verifies components work together
- ~80% coverage target

### Stage 5: E2E Tests
```bash
uv run pytest tests/e2e/ -v
```
- Full application workflows
- Tests CLI integration
- ~70% coverage target

### Stage 6: Coverage Report
```bash
uv run pytest tests/ --cov=src --cov-report=xml
```
- Generates coverage metrics
- Uploads to Codecov
- Enforces minimum threshold (85%)

---

## Troubleshooting CI Failures

### ❌ Black formatting fails
```bash
# Auto-fix formatting locally
uv run black src/ tests/
git add .
git commit -m "style: format code with black"
git push
```

### ❌ Mypy type errors
```bash
# Check types locally
uv run mypy src/

# Add type hints as needed
# Review mypy output and fix types
```

### ❌ Test failures
```bash
# Run failing tests locally
uv run pytest tests/path/to/test.py -v

# Debug and fix
# Run full suite before push
uv run pytest tests/ -v
```

### ❌ Coverage below threshold
```bash
# Check coverage report
uv run pytest tests/ --cov=src --cov-report=html

# Add missing tests
# Aim for >90% coverage
```

---

## Future Enhancements

Planned workflow additions:
- 🔲 Automatic dependency updates (Dependabot)
- 🔲 Security scanning (CodeQL, Trivy)
- 🔲 Performance benchmarking
- 🔲 Documentation build verification
- 🔲 Docker image building
- 🔲 Release automation

---

## Configuration Files

- **`.github/workflows/tests.yml`** - Comprehensive multi-OS test suite
- **`.github/workflows/python-app.yml`** - Quick CI pipeline for main branch
- **`pyproject.toml`** - Project dependencies and test configuration
- **`pytest.ini`** - Pytest configuration (if separate)
- **`.python-version`** - Python version specification

---

## Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Codecov Documentation](https://docs.codecov.io/)

---

**Last Updated**: 2026-09-15
