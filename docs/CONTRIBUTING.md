# Contributing Guide

Thank you for your interest in contributing to the Event Camera Simulator! This guide explains how to contribute code, tests, and documentation.

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/eventcamera.git
cd eventcamera

# Add upstream remote
git remote add upstream https://github.com/original/eventcamera.git
```

### 2. Set Up Development Environment

```bash
# Install in development mode
pip install -e .

# Or with uv
uv sync

# Install development tools
pip install black mypy pytest pytest-cov
```

### 3. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

## 📝 Code Style & Standards

### Clean Code Principles (Uncle Bob Martin)

All code must follow these principles:

✅ **Meaningful Names**
```python
# Good
event_visualization = np.zeros((height, width, 3), dtype=np.uint8)

# Bad
viz = np.zeros((h, w, 3), dtype=np.uint8)
```

✅ **Small Functions** (max ~50 lines)
```python
# Good - focused single task
def _convert_to_log_intensity(self, grayscale_frame: np.ndarray) -> np.ndarray:
    normalized = grayscale_frame.astype(np.float32) / 255.0
    return cv2.log(normalized + self._LOG_EPSILON)

# Bad - too many responsibilities
def process_frame_and_convert_and_normalize(frame):
    # ... 200 lines ...
```

✅ **No Magic Numbers**
```python
# Good
_CLAHE_CLIP_LIMIT = 2.0
clahe = cv2.createCLAHE(clipLimit=self._CLAHE_CLIP_LIMIT)

# Bad
clahe = cv2.createCLAHE(clipLimit=2.0)
```

✅ **Comments Explain Why, Not What**
```python
# Good
# MOG2 filters static background noise to improve event quality
foreground_mask = cv2.morphologyEx(
    self.background_subtractor.apply(grayscale_frame),
    cv2.MORPH_OPEN,
    self.morphological_kernel,
)

# Bad
# Apply morphologyEx with MORPH_OPEN
foreground_mask = cv2.morphologyEx(...)
```

✅ **Full Type Hints**
```python
# Good
def process(self, frame_bgr: np.ndarray, frame_index: int = 0) -> tuple:
    ...

# Bad
def process(self, frame_bgr, frame_index=0):
    ...
```

### Formatting

Use **Black** for automatic formatting:

```bash
# Format code
black src/ tests/

# Check formatting (don't modify)
black --check src/ tests/
```

### Type Checking

Use **mypy** for static type analysis:

```bash
# Check types
mypy src/

# Strict mode
mypy --strict src/
```

## 🧪 Testing

All code changes require tests. Follow TDD principles:

### Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   └── test_component.py   # Test one component
├── integration/            # Cross-component tests
│   └── test_pipeline.py    # Test full pipeline
└── e2e/                    # End-to-end tests
    └── test_application.py # Test full application
```

### Arrange-Act-Assert Pattern

```python
def test_log_conversion_preserves_shape(self, simulator, dummy_grayscale_frame):
    """Verify log conversion maintains frame dimensions.
    
    Arrange: Grayscale frame (480, 640)
    Act: Convert to log intensity
    Assert: Output shape unchanged
    """
    # ARRANGE
    frame = dummy_grayscale_frame
    
    # ACT
    log_frame = simulator._convert_to_log_intensity(frame)
    
    # ASSERT
    assert log_frame.shape == frame.shape
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only (fast)
pytest tests/unit/ -x

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_simulator_events.py::TestEventDetection -v

# Run with output
pytest tests/ -s
```

### Coverage Requirements

- Minimum: 85% coverage
- Target: >90% coverage
- New code: 100% coverage

```bash
# Check coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## 📚 Documentation

All code must be documented:

### Docstrings (Numpy Style)

```python
def _convert_to_log_intensity(self, grayscale_frame: np.ndarray) -> np.ndarray:
    """Convert grayscale frame to log-intensity space.

    Parameters
    ----------
    grayscale_frame : np.ndarray
        Input grayscale frame of shape (height, width) with dtype uint8.

    Returns
    -------
    np.ndarray
        Log-intensity representation of shape (height, width) with dtype float32.
        Range is approximately (-inf, 0] with typical values around [-6, 0].

    Examples
    --------
    >>> import numpy as np
    >>> frame = np.array([[0, 128, 255]], dtype=np.uint8)
    >>> log_frame = simulator._convert_to_log_intensity(frame)
    >>> log_frame.shape
    (1, 3)
    >>> log_frame.dtype
    dtype('float32')
    """
    normalized_frame = grayscale_frame.astype(np.float32) / 255.0
    return cv2.log(normalized_frame + self._LOG_EPSILON)
```

### Inline Comments (Strategic)

```python
# Only explain WHY, not WHAT

# MOG2 filters static background to reduce noise artifacts
foreground_mask = cv2.morphologyEx(...)

# Don't do this:
# Apply morphology
foreground_mask = cv2.morphologyEx(...)
```

## 🔄 Git Workflow

### Commit Messages

Follow conventional commits format:

```bash
# Format: <type>: <description>
# Types: feat, fix, docs, test, refactor, perf, ci

git commit -m "feat: add CLAHE normalization for VLA"
git commit -m "fix: refractory period not updating correctly"
git commit -m "test: add 15 new tests for event detection"
git commit -m "docs: add architecture documentation"
git commit -m "refactor: simplify optical flow visualization"
```

### Pull Request Process

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request on GitHub**
   - Title: Clear, concise description
   - Description: Explain what changed and why
   - Reference issues: "Fixes #123"

3. **PR Description Template**
   ```markdown
   ## Description
   Brief explanation of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests pass
   - [ ] E2E tests pass
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Docstrings added/updated
   - [ ] Tests added
   - [ ] No breaking changes
   ```

4. **Wait for Review**
   - Address feedback
   - Push updates to same branch
   - PR auto-updates

## 🏗️ Architecture Guidelines

### Adding a New Algorithm

1. **Add method to simulator**
   ```python
   def _new_algorithm(self, input_data: np.ndarray) -> np.ndarray:
       """Docstring with examples."""
       # Implementation
       return result
   ```

2. **Add unit tests**
   ```python
   # tests/unit/test_simulator_*.py
   def test_new_algorithm_output_shape(self, simulator):
       """Test new algorithm."""
       # ...
   ```

3. **Add integration test**
   ```python
   # tests/integration/test_simulator_pipeline.py
   def test_pipeline_with_new_algorithm(self, frame_sequence):
       """Test algorithm in complete pipeline."""
       # ...
   ```

4. **Update documentation**
   - Add to `docs/ARCHITECTURE.md`
   - Add to `docs/API.md` if user-facing
   - Update docstrings

### Modifying Existing Code

1. **Preserve API compatibility** (if possible)
2. **Add deprecation warnings** (if breaking)
3. **Update all related tests**
4. **Document changes**
5. **Update CHANGELOG**

## 📋 Pre-Submission Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines (`black`, `mypy`)
- [ ] All tests pass (`pytest tests/`)
- [ ] Coverage >85% (`pytest --cov`)
- [ ] Docstrings added/updated (Numpy style)
- [ ] No magic numbers (use constants)
- [ ] Meaningful variable names
- [ ] Functions <50 lines
- [ ] Comments explain WHY not WHAT
- [ ] Git history is clean (meaningful commits)
- [ ] PR description is clear
- [ ] No unnecessary dependencies added

```bash
# Run pre-submission checks
black src/ tests/
mypy src/
pytest tests/ --cov=src --cov-fail-under=85
```

## 🚦 Review Process

### Code Review Criteria

Reviewers will check:

1. **Functionality**: Does it work correctly?
2. **Testing**: Are tests adequate and passing?
3. **Code Quality**: Does it follow principles?
4. **Documentation**: Are changes documented?
5. **Performance**: Any performance regressions?
6. **Compatibility**: Any breaking changes?

### Getting Your PR Merged

- Address all review comments
- Push updates to the same branch
- Request re-review after changes
- Wait for approval from 2+ maintainers

## 📚 Resources

### Learning Resources

- [Clean Code by Robert Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Numpy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Type Hints in Python](https://docs.python.org/3/library/typing.html)

### Project Documentation

- [Architecture Guide](ARCHITECTURE.md)
- [API Reference](API.md)
- [Parameters Guide](PARAMETERS.md)
- [Testing Guide](../tests/README.md)

## 🤝 Community

- Be respectful and constructive
- Assume good intent
- Help others learn
- Share knowledge
- Celebrate contributions

## ❓ Questions?

- Check existing issues
- Read documentation
- Ask in PR comments
- Create an issue for discussion

---

**Last Updated**: 2026-09-15  
**Version**: 1.0.0
