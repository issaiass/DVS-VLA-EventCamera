# Test Suite Organization (TDD Standards)

This test suite follows **Test-Driven Development (TDD)** best practices with clear separation of concerns.

## 📁 Test Structure

```
tests/
├── conftest.py                          # Shared fixtures (all tests)
├── README.md                            # This file
│
├── unit/                                # ⚡ Fast, isolated unit tests
│   ├── __init__.py
│   ├── test_simulator_initialization.py    # Constructor, setup, algorithms
│   ├── test_simulator_transformations.py   # Log conversion, warping, refractory
│   ├── test_simulator_events.py            # Event detection, polarity, timestamps
│   ├── test_simulator_visualizations.py    # Event, time surface, flow visualizations
│   └── test_cli_arguments.py               # Argument parsing, CLI interface
│
├── integration/                         # 🔗 Cross-component tests
│   ├── __init__.py
│   └── test_simulator_pipeline.py       # Complete pipeline, sequences, parameters
│
└── e2e/                                 # 🚀 End-to-End application tests
    ├── __init__.py
    ├── test_application_workflow.py     # Application lifecycle, CLI integration
    └── test_video_processing.py         # Video processing, output quality
```

## 🎯 Test Organization Principles

### Unit Tests (`tests/unit/`)
**Purpose**: Test individual components in isolation  
**Characteristics**:
- Fast (typically < 1ms each)
- Deterministic (same input → same output)
- No external dependencies
- No actual file I/O or video processing
- Heavily use fixtures for test data

**When to run**:
```bash
# Run all unit tests (fastest feedback loop)
pytest tests/unit/

# Run specific test class
pytest tests/unit/test_simulator_events.py::TestEventDetection

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html
```

### Integration Tests (`tests/integration/`)
**Purpose**: Test complete pipelines and component interactions  
**Characteristics**:
- Slower (may take seconds)
- Test realistic scenarios
- Verify cross-component behavior
- Use fixtures to create realistic data

**When to run**:
```bash
# After unit tests pass
pytest tests/integration/

# Run complete parameter sweep
pytest tests/integration/test_simulator_pipeline.py::TestParameterVariations -v
```

### E2E Tests (`tests/e2e/`)
**Purpose**: Test complete application workflows from CLI to output  
**Characteristics**:
- Slowest but most realistic
- Test actual application code paths
- Verify CLI argument handling
- Test error handling and edge cases
- Process complete video sequences

**When to run**:
```bash
# After unit and integration tests pass (pre-release)
pytest tests/e2e/

# Test specific workflow
pytest tests/e2e/test_application_workflow.py -v

# Test video processing quality
pytest tests/e2e/test_video_processing.py -v
```

## 📊 Test File Organization

### `test_simulator_initialization.py`
Tests the **constructor and setup** phase.

| Test Class | Purpose |
|-----------|---------|
| `TestSimulatorInitialization` | Parameter storage and validation |
| `TestAlgorithmInitialization` | Algorithm instance creation |
| `TestInitialState` | State variables set to None initially |

### `test_simulator_transformations.py`
Tests **individual transformation methods** (data processing units).

| Test Class | Purpose |
|-----------|---------|
| `TestLogIntensityConversion` | Log-domain intensity conversion |
| `TestReactoryPeriodApplication` | Refractory period suppression logic |
| `TestTimeSurfaceUpdate` | Time surface tracking |

### `test_simulator_events.py`
Tests **event detection and classification**.

| Test Class | Purpose |
|-----------|---------|
| `TestFirstFrameProcessing` | Initial frame handling |
| `TestEventDetection` | Event generation triggers |
| `TestEventPolarity` | ON (polarity=1) vs OFF (polarity=-1) events |
| `TestEventTimestamps` | Event timing and ordering |

### `test_simulator_visualizations.py`
Tests **output visualization generation**.

| Test Class | Purpose |
|-----------|---------|
| `TestEventVisualization` | Event rendering (red/blue pixels) |
| `TestTimeSurfaceVisualization` | Event decay heatmap (JET colormap) |
| `TestOpticalFlowVisualization` | Motion vector arrows |
| `TestVisualizationPersistence` | Event latching (persistence) |

### `test_cli_arguments.py`
Tests **command-line interface**.

| Test Class | Purpose |
|-----------|---------|
| `TestArgumentParser` | Argument parsing, defaults, custom values |
| `TestVideoSourceParsing` | Camera index vs file path detection |

### `test_simulator_pipeline.py` (Integration)
Tests **complete end-to-end workflow**.

| Test Class | Purpose |
|-----------|---------|
| `TestCompleteSimulatorPipeline` | Full frame sequence processing |
| `TestParameterVariations` | Behavior across parameter ranges (parametrized) |
| `TestEndToEndPipelineQuality` | Output quality and consistency |

## 🧪 Running Tests

### Quick Development (Unit Tests Only)
```bash
# Fastest feedback loop (< 5 seconds)
pytest tests/unit/ -x --tb=short
# -x: Stop on first failure
# --tb=short: Shorter traceback
```

### Full Test Suite
```bash
# Run all tests with coverage (entire pyramid)
pytest tests/ --cov=src --cov-report=term-missing
```

### By Testing Layer
```bash
# Unit tests only (fastest)
pytest tests/unit/ -v

# Unit + Integration (comprehensive)
pytest tests/unit/ tests/integration/ -v

# Unit + Integration + E2E (complete)
pytest tests/ -v

# E2E tests only (slowest, most realistic)
pytest tests/e2e/ -v
```

### Specific Scenarios
```bash
# Test event detection only
pytest tests/unit/test_simulator_events.py -v

# Test parameter sensitivity
pytest tests/integration/test_simulator_pipeline.py::TestParameterVariations -v

# Test application workflows
pytest tests/e2e/test_application_workflow.py -v

# Test video processing quality
pytest tests/e2e/test_video_processing.py -v

# Test with live output
pytest tests/ -s
```

### With Coverage Report
```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Coverage by layer
pytest tests/unit/ --cov=src --cov-report=term-missing -q
pytest tests/integration/ --cov=src --cov-report=term-missing -q
pytest tests/e2e/ --cov=src --cov-report=term-missing -q
```

## 📐 TDD Test Design Pattern: Arrange-Act-Assert

Each test follows the **AAA pattern** for clarity:

```python
def test_brightness_increase_generates_on_events(self, simulator):
    """Verify brightness increase (ON events) polarity = 1.
    
    Arrange: Dark frame followed by brighter frame
    Act: Process sequence to generate events
    Assert: Events include ON events (polarity=1)
    """
    # ARRANGE: Set up test preconditions
    dark_frame = np.full((480, 640, 3), 100, dtype=np.uint8)
    bright_frame = np.full((480, 640, 3), 200, dtype=np.uint8)
    
    # ACT: Execute the behavior being tested
    simulator.process(dark_frame, 0)
    _, _, _, events = simulator.process(bright_frame, 1)
    
    # ASSERT: Verify expected outcomes
    polarities = [event[2] for event in events]
    assert 1 in polarities
```

## 🔧 Fixtures (Shared Test Data)

Defined in `conftest.py` and available to all tests:

| Fixture | Purpose |
|---------|---------|
| `dummy_grayscale_frame` | Gradient pattern frame |
| `dummy_bgr_frame` | RGB version of grayscale |
| `uniform_frame` | Baseline (no events) |
| `moving_object_frame` | Simulated moving object |
| `stationary_frame` | Stationary object version |
| `frame_sequence` | 5-frame sequence with motion |
| `simulator_parameters` | Default parameter dict |
| `simulator` | Pre-configured simulator instance |
| `temp_video_file` | Temporary test video file |

**Usage**:
```python
def test_my_feature(self, simulator, frame_sequence):
    """Test uses simulator and frame_sequence fixtures."""
    for frame in frame_sequence:
        result = simulator.process(frame, 0)
```

## 📈 Test Coverage Goals

- **Unit Tests**: ≥95% coverage of core logic
- **Integration Tests**: ≥80% coverage of pipelines
- **E2E Tests**: ≥70% coverage of application workflows
- **Overall**: ≥90% code coverage

**View coverage**:
```bash
pytest tests/ --cov=src --cov-report=term-missing | grep -E "^src.*"
```

**Coverage by layer**:
```bash
# Unit tests only
pytest tests/unit/ --cov=src --cov-report=term-missing

# All tests
pytest tests/ --cov=src --cov-report=html
```

## 🚀 CI/CD Integration

### Pre-commit (Local)
```bash
# Run unit tests only (fast)
pytest tests/unit/ -x
```

### Pre-push (Comprehensive)
```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=85
```

## 🎓 TDD Best Practices Used Here

✅ **Isolated Unit Tests**: Each component tested independently  
✅ **Clear Test Names**: Test name describes what's being verified  
✅ **AAA Pattern**: Arrange-Act-Assert for readability  
✅ **Single Assertion**: Each test verifies one behavior (usually)  
✅ **Parametrized Tests**: Use `@pytest.mark.parametrize` for variations  
✅ **Fixture Reuse**: Fixtures shared across tests avoid duplication  
✅ **Fast Feedback**: Unit tests run in < 1 second  
✅ **Documentation**: Each test documents expected behavior  

## 🔍 Test Categorization by Testing Pyramid

```
          /\
         /  \ E2E Tests (Full Application + CLI)
        /    \
       /______\

        /\
       /  \ Integration Tests (Complete Pipelines)
      /    \
     /______\

      /\
     /  \ Unit Tests (Individual Components)
    /    \
   /______\
```

- **Unit Tests** (60%): Individual methods and classes - ⚡ Fast feedback
- **Integration Tests** (25%): Complete pipelines and scenarios - 🔗 Cross-component
- **E2E Tests** (15%): Full application workflow, CLI, video processing - 🚀 Realistic

## 📚 Adding New Tests

1. **Determine test type**:
   - Unit test? → `tests/unit/`
   - Integration test? → `tests/integration/`

2. **Choose or create test file**:
   - Tests for simulator? → `test_simulator_*.py`
   - Tests for CLI? → `test_cli_*.py`

3. **Write test using AAA pattern**:
   ```python
   def test_new_feature(self, simulator):
       """Brief description of what's being verified."""
       # Arrange: Set up test data
       data = ...
       
       # Act: Execute behavior
       result = simulator.method(data)
       
       # Assert: Verify outcome
       assert result.property == expected_value
   ```

4. **Run test**:
   ```bash
   pytest tests/ -k "test_new_feature" -v
   ```

## 🐛 Debugging Failed Tests

```bash
# Run with verbose output
pytest tests/ -v

# Run with full traceback
pytest tests/ -vv

# Run with print statements shown
pytest tests/ -s

# Run with pdb on first failure
pytest tests/ --pdb

# Run only tests matching pattern
pytest tests/ -k "event" -v
```

## 📊 Test Suite Summary

| Layer | Location | Count | Speed | Purpose |
|-------|----------|-------|-------|---------|
| **Unit** | `tests/unit/` | 60+ | ⚡ ~1s | Component isolation |
| **Integration** | `tests/integration/` | 10+ | 🔗 ~5s | Pipeline verification |
| **E2E** | `tests/e2e/` | 30+ | 🚀 ~10s | Application workflow |
| **Total** | All layers | **100+** | - | **Comprehensive** |

### Test Execution Time

```
pytest tests/unit/          # < 1 second   ⚡ Fast feedback
pytest tests/integration/   # ~5 seconds   🔗 Moderate
pytest tests/e2e/           # ~10 seconds  🚀 Thorough
pytest tests/               # ~15 seconds  ✅ Complete
```

---

**Last Updated**: 2026-09-15  
**Test Organization**: TDD Standard + E2E Testing  
**Total Tests**: 100+  
**Coverage Target**: >90%  
**Testing Pyramid**: Unit (60%) | Integration (25%) | E2E (15%)
