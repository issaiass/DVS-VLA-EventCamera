# GitHub Configuration

This directory contains GitHub-specific configuration files for the EventCamera project.

## 📁 Structure

```
.github/
├── workflows/
│   ├── tests.yml                 # Comprehensive multi-OS test suite
│   └── python-app.yml            # Quick CI pipeline for main branch
├── ISSUE_TEMPLATE/
│   ├── bug_report.md             # Bug report template
│   └── feature_request.md        # Feature request template
├── pull_request_template.md      # PR template
├── WORKFLOWS.md                  # CI/CD workflow documentation
└── README.md                     # This file
```

## 🚀 Continuous Integration Workflows

### Workflow 1: Tests (`workflows/tests.yml`)
**Comprehensive test suite across multiple platforms**

- **Triggers**: Push to `main`, `master`, `develop` + PRs
- **Matrix**: 
  - OS: Ubuntu, Windows, macOS
  - Python: 3.11, 3.12
- **Checks**:
  - Code formatting (black)
  - Type checking (mypy)
  - Unit tests (fast)
  - Integration tests
  - E2E tests
  - Coverage reporting (Codecov)
  - Coverage threshold enforcement (≥85%)

### Workflow 2: Python App (`workflows/python-app.yml`)
**Quick feedback on main branch**

- **Triggers**: Push to `main`/`master` + PRs
- **Checks**:
  - All test layers
  - Coverage reporting
  - Type and format checking

## 📋 Issue Templates

### Bug Report (`ISSUE_TEMPLATE/bug_report.md`)
- Clear bug description
- Reproduction steps
- Environment information
- Minimal reproducible example
- Checklist for issue quality

### Feature Request (`ISSUE_TEMPLATE/feature_request.md`)
- Problem description
- Proposed solution
- Use case categorization
- Implementation ideas
- Impact assessment

## 📝 Pull Request Template

The `pull_request_template.md` guides contributors to:
- Describe changes clearly
- Specify change type (bug/feature/refactor/docs)
- Reference related issues
- Verify test coverage
- Check code quality
- Update documentation
- Follow project guidelines

**Auto-fills when creating PRs on GitHub!**

## 📊 CI/CD Status Badges

Add these to your README.md to show CI status:

```markdown
[![Tests](https://github.com/yourusername/eventcamera/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/eventcamera/actions/workflows/tests.yml)
[![Python Application](https://github.com/yourusername/eventcamera/actions/workflows/python-app.yml/badge.svg)](https://github.com/yourusername/eventcamera/actions/workflows/python-app.yml)
```

## ✅ Requirements Met by CI

### Code Quality
- ✅ Black formatting enforced
- ✅ Mypy type checking
- ✅ No type errors allowed

### Testing
- ✅ 100+ tests (unit/integration/e2e)
- ✅ Multiple Python versions (3.11, 3.12)
- ✅ Multiple OS (Ubuntu, Windows, macOS)
- ✅ >90% coverage target, 85% minimum

### Reliability
- ✅ Fast unit tests for quick feedback
- ✅ Integration tests for pipeline validation
- ✅ E2E tests for real-world scenarios
- ✅ Coverage reporting with Codecov

## 🔧 Local Development

Before pushing, run locally:

```bash
# Install dependencies
uv sync

# Format code
uv run black src/ tests/

# Type check
uv run mypy src/

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Verify coverage threshold
uv run pytest tests/ --cov=src --cov-fail-under=85
```

## 📖 Documentation

See [`WORKFLOWS.md`](./WORKFLOWS.md) for:
- Detailed workflow descriptions
- Troubleshooting CI failures
- Badge configuration
- Local testing procedures
- Future workflow enhancements

## 🎯 Workflow Execution Flow

```
Push / PR Created
    ↓
[tests.yml] Multi-OS Test Matrix
    ├─ Format Check (black)
    ├─ Type Check (mypy)
    ├─ Unit Tests
    ├─ Integration Tests
    ├─ E2E Tests
    ├─ Coverage Report
    └─ Coverage Threshold Check
    ↓
[code-quality job] Strict Checks
    ├─ Format Verification (blocking)
    ├─ Type Checking (blocking)
    └─ Linting (informational)
    ↓
✅ All Green or ❌ Failures Reported
```

## 🚀 Quick Start

### 1. Push code
```bash
git commit -m "feat: add awesome feature"
git push origin feature-branch
```

### 2. GitHub Actions runs automatically
- Workflows trigger
- All checks run in parallel
- Results shown on PR/commit

### 3. Review results
- Check "Checks" tab on PR
- See detailed logs
- Coverage reports available

### 4. Fix any issues
- Address formatting: `uv run black src/`
- Fix type errors: `uv run mypy src/`
- Add tests: Create test files in `tests/`
- Push updates: `git push origin feature-branch`

### 5. Merge
- All checks pass ✅
- Review approved ✅
- Merge to main ✅

## 📞 Support

- **Issues**: Use issue templates for consistency
- **PRs**: Use PR template to guide your changes
- **Documentation**: See [`WORKFLOWS.md`](./WORKFLOWS.md) for details

## 🔗 Related

- [`pyproject.toml`](../pyproject.toml) - Project configuration
- [`tests/README.md`](../tests/README.md) - Testing documentation
- [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) - Contribution guidelines

---

**Last Updated**: 2026-09-15  
**Status**: ✅ All workflows configured and tested
