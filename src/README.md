# Source Code Structure

Understanding the source code organization and key components.

## 📁 Directory Layout

```
src/
├── main.py                 # CLI application entry point
└── eventcamera/
    ├── __init__.py        # Package initialization and exports
    └── simulator.py       # Core DVS simulator implementation
```

## 🎯 File Purposes

### main.py

Command-line interface and application wrapper.

**Contents:**
- `EventCameraApplication` - Main app class
- `create_argument_parser()` - CLI argument setup
- `parse_video_source()` - Smart source detection
- `main()` - Entry point

**Responsibilities:**
- Parse command-line arguments
- Manage video input/output
- Handle user interaction (display, quit)
- Resource cleanup

**When to modify:**
- Adding CLI arguments
- Changing application behavior
- Improving error handling
- Adding new output formats

**Key methods:**
```python
app = EventCameraApplication(video_source=0)
exit_code = app.run()  # Main loop
```

---

### simulator.py

Core event camera simulation algorithm.

**Contents:**
- `VLAOptimizedDVSSimulator` - Main simulator class

**Responsibilities:**
- Frame processing pipeline
- Event detection and generation
- Visualization generation
- Algorithm state management

**Core components (private methods):**

| Method | Purpose |
|--------|---------|
| `_convert_to_log_intensity()` | Convert to log-domain |
| `_initialize_first_frame()` | Setup internal state |
| `_warp_log_intensity_frame()` | Temporal interpolation |
| `_apply_refractory_period()` | Suppress repeated events |
| `_update_refractory_and_time_surface()` | Update state tracking |
| `_render_events_to_visualization()` | Draw events |
| `_create_time_surface_visualization()` | Generate time surface |
| `_apply_clahe_normalization()` | Normalize contrast |
| `_create_optical_flow_visualization()` | Draw motion vectors |

**Public interface:**
```python
sim = VLAOptimizedDVSSimulator(...)
event_vis, ts_vis, flow_vis, events = sim.process(frame, frame_index)
```

**When to modify:**
- Changing detection algorithm
- Adding new filtering
- Optimizing performance
- Adding new features

---

### __init__.py

Package initialization.

**Contents:**
- Exports public API
- Package docstring

**Current exports:**
```python
from .simulator import VLAOptimizedDVSSimulator

__all__ = ["VLAOptimizedDVSSimulator"]
```

**When to modify:**
- Adding new public classes
- Changing exported API
- Updating version

---

## 🔄 Data Flow

### High-Level Flow

```
main.py
   ↓
EventCameraApplication
   ├─→ parse command-line args
   ├─→ create VLAOptimizedDVSSimulator
   ├─→ open video source
   ├─→ main loop:
   │   ├─→ read frame
   │   ├─→ simulator.process(frame)
   │   ├─→ display visualizations
   │   └─→ check for quit
   └─→ cleanup
   
eventcamera/simulator.py
   ↓
VLAOptimizedDVSSimulator.process()
   ├─→ convert BGR to grayscale
   ├─→ background subtraction (MOG2)
   ├─→ convert to log intensity
   ├─→ estimate optical flow
   ├─→ for each subframe:
   │   ├─→ warp previous frame
   │   ├─→ compute intensity delta
   │   ├─→ detect events
   │   ├─→ apply refractory period
   │   └─→ render events
   ├─→ generate visualizations
   └─→ return (event_vis, ts_vis, flow_vis, events)
```

---

## 🏗️ Class Hierarchies

### VLAOptimizedDVSSimulator

```python
class VLAOptimizedDVSSimulator:
    """Main simulator class."""
    
    # Configuration (set at init, immutable)
    positive_threshold: float
    negative_threshold: float
    subframe_count: int
    refractory_frames: int
    decay_window: float
    
    # Algorithms (OpenCV instances)
    optical_flow_algorithm: cv2.DISOpticalFlow
    clahe: cv2.CLAHE
    background_subtractor: cv2.BackgroundSubtractorMOG2
    morphological_kernel: np.ndarray
    
    # State (updated per frame)
    previous_grayscale: np.ndarray | None
    previous_log_intensity: np.ndarray | None
    refractory_map: np.ndarray | None
    time_surface: np.ndarray | None
    coordinate_grid_x: np.ndarray | None
    coordinate_grid_y: np.ndarray | None
    
    # Public methods
    def process(self, frame_bgr, frame_index) -> tuple
    
    # Private methods
    def _convert_to_log_intensity(self, grayscale_frame)
    def _initialize_first_frame(self, grayscale_frame, log_intensity)
    def _warp_log_intensity_frame(self, optical_flow, fraction)
    def _apply_refractory_period(self, positive_mask, negative_mask)
    def _update_refractory_and_time_surface(self, pos, neg, timestamp)
    def _render_events_to_visualization(self, vis, pos, neg, events, ts)
    def _create_time_surface_visualization(self, current_timestamp)
    def _apply_clahe_normalization(self, bgr_visualization)
    def _create_optical_flow_visualization(self, grayscale_frame, flow)
```

### EventCameraApplication

```python
class EventCameraApplication:
    """CLI application class."""
    
    # Configuration
    video_source: str | int
    simulator: VLAOptimizedDVSSimulator
    
    # State
    video_capture: cv2.VideoCapture | None
    frame_index: int
    
    # Public methods
    def run(self) -> int
    
    # Private methods
    def _initialize_video_capture(self) -> bool
    def _read_frame(self) -> tuple[bool, np.ndarray | None]
    def _display_visualizations(...) -> bool
    def _cleanup_windows(self) -> None
    def _release_video_capture(self) -> None
```

---

## 🎯 Algorithm Implementation Details

### Log-Intensity Conversion

**File**: `simulator.py:_convert_to_log_intensity()`

```python
def _convert_to_log_intensity(self, grayscale_frame):
    normalized = grayscale_frame.astype(np.float32) / 255.0
    return cv2.log(normalized + self._LOG_EPSILON)
```

**Purpose**: Convert to log-domain for DVS modeling

**Why**: Biological vision responds logarithmically (Weber's law)

---

### Optical Flow Warping

**File**: `simulator.py:_warp_log_intensity_frame()`

```python
def _warp_log_intensity_frame(self, optical_flow, fraction):
    map_x = (self.coordinate_grid_x - optical_flow[..., 0] * fraction)
    map_y = (self.coordinate_grid_y - optical_flow[..., 1] * fraction)
    return cv2.remap(self.previous_log_intensity, map_x, map_y, ...)
```

**Purpose**: Enable sub-frame temporal interpolation

**Why**: Standard frame-based detection has 33ms resolution; subframes achieve microsecond precision

---

### Event Detection

**File**: `simulator.py:process()` (main loop)

```python
# Detect ON events (brightness increase)
positive_mask = cv2.bitwise_and(
    cv2.compare(delta, threshold, cv2.CMP_GT),
    foreground_mask
)

# Detect OFF events (brightness decrease)
negative_mask = cv2.bitwise_and(
    cv2.compare(delta, -threshold, cv2.CMP_LT),
    foreground_mask
)
```

**Purpose**: Generate events where log-intensity change exceeds threshold

**Why**: DVS sensors respond asynchronously to contrast changes

---

### Refractory Period

**File**: `simulator.py:_apply_refractory_period()` and `_update_refractory_and_time_surface()`

```python
# Suppress pixels in refractory period
active = cv2.compare(self.refractory_map, 0, cv2.CMP_GT)
not_active = cv2.bitwise_not(active)
suppressed = cv2.bitwise_and(mask, not_active)

# Update refractory map
self.refractory_map[fired > 0] = self.refractory_frames
self.refractory_map[self.refractory_map > 0] -= 1
```

**Purpose**: Prevent pixel saturation

**Why**: Biological sensors also have refractory periods

---

## 🔌 Extension Points

### Adding a New Algorithm

1. **Add as private method** in `VLAOptimizedDVSSimulator`
   ```python
   def _new_algorithm(self, input_data: np.ndarray) -> np.ndarray:
       """Docstring."""
       # Implementation
       return result
   ```

2. **Call from process()**
   ```python
   def process(self, frame_bgr, frame_index):
       # ...
       result = self._new_algorithm(data)
       # ...
   ```

3. **Add tests** in `tests/unit/test_simulator_*.py`

4. **Document** in `docs/ARCHITECTURE.md`

---

### Adding a CLI Parameter

1. **Add to ArgumentParser** in `main.py`
   ```python
   parser.add_argument(
       '--new-param',
       type=float,
       default=1.0,
       help="Description"
   )
   ```

2. **Pass to simulator** in `main()`
   ```python
   app = EventCameraApplication(
       new_param=args.new_param,
       ...
   )
   ```

3. **Store in VLAOptimizedDVSSimulator.__init__()**
   ```python
   self.new_param = new_param
   ```

4. **Add tests** and documentation

---

## 📊 Constants and Configuration

All magic numbers are defined as class constants:

**File**: `simulator.py`

```python
class VLAOptimizedDVSSimulator:
    _CLAHE_CLIP_LIMIT = 2.0
    _CLAHE_TILE_SIZE = (8, 8)
    _MOG2_HISTORY = 500
    _MOG2_VAR_THRESHOLD = 20
    _MORPH_KERNEL_SIZE = (3, 3)
    _LOG_EPSILON = 1e-6
    _FLOW_VISUALIZATION_STEP = 16
    _FLOW_VISUALIZATION_MIN_MAGNITUDE = 0.5
    _BGR_RED = (0, 0, 255)
    _BGR_BLUE = (255, 0, 0)
    _BGR_MAGENTA = (255, 0, 255)
```

**When to adjust:**
- Tuning algorithm behavior
- Optimizing performance
- Adapting to different sensors

---

## 🧪 Testing Structure

**Unit tests** for internal methods:
- `tests/unit/test_simulator_transformations.py` - Private methods
- `tests/unit/test_simulator_events.py` - Event detection
- `tests/unit/test_simulator_visualizations.py` - Visualization

**Integration tests** for full pipeline:
- `tests/integration/test_simulator_pipeline.py` - Complete workflow

**E2E tests** for application:
- `tests/e2e/test_application_workflow.py` - CLI and lifecycle
- `tests/e2e/test_video_processing.py` - Video handling

---

## 🎓 Design Patterns Used

### Single Responsibility Principle
- Each method does one thing
- Separation between app and simulator
- Clear private/public boundaries

### Dependency Injection
- Parameters passed to constructor
- No global state
- Easy to test with different configs

### State Management
- Clear initialization phase (first frame)
- Immutable configuration
- Managed mutable state (maps, surfaces)

### Error Handling
- Try/finally for resource cleanup
- Explicit error codes (exit codes)
- Clear error messages

---

## 📈 Performance Considerations

### Bottlenecks

1. **Optical Flow** - Most computationally expensive
2. **Sub-frame Loop** - Scales with subframe_count
3. **MOG2 Background Subtraction** - Moderate cost
4. **Event Rendering** - Scales with event count

### Optimizations Applied

- Refractory period reduces events
- Rate limiting prevents saturation
- Efficient NumPy/OpenCV operations
- Minimal memory allocations

### Future Optimizations

- GPU acceleration (CUDA)
- Event compression
- Sparse data structures
- Parallel processing

---

**Last Updated**: 2026-09-15  
**Version**: 1.0.0
