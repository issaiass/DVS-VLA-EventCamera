# API Reference

Complete API documentation for the event camera simulator.

## 📦 Import

```python
from eventcamera import VLAOptimizedDVSSimulator
from src.main import EventCameraApplication
```

---

## 🎯 VLAOptimizedDVSSimulator

Main simulator class for event camera processing.

### Constructor

```python
VLAOptimizedDVSSimulator(
    positive_threshold: float = 0.35,
    negative_threshold: float = 0.35,
    subframe_count: int = 5,
    refractory_frames: int = 2,
    decay_window: float = 3.0
) -> VLAOptimizedDVSSimulator
```

#### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `positive_threshold` | float | 0.35 | (0, 3.0] | Threshold for ON events in log-intensity space. Lower = more sensitive |
| `negative_threshold` | float | 0.35 | (0, 3.0] | Threshold for OFF events. Controls sensitivity to darkening |
| `subframe_count` | int | 5 | [1, 100] | Number of temporal interpolation subframes. Higher = finer timing |
| `refractory_frames` | int | 2 | [0, 100] | Refractory period in frames. Prevents pixel saturation |
| `decay_window` | float | 3.0 | (0, 10.0] | Time window for event decay in time surface (frames) |

#### Returns

Initialized simulator instance ready for processing frames.

#### Raises

- `ValueError`: If any parameter out of valid range

#### Example

```python
from eventcamera import VLAOptimizedDVSSimulator
import numpy as np

# Create simulator with default parameters
sim = VLAOptimizedDVSSimulator()

# Create simulator with custom parameters
sim = VLAOptimizedDVSSimulator(
    positive_threshold=0.25,    # More sensitive to brightness
    negative_threshold=0.30,    # Different sensitivity for darkening
    subframe_count=10,          # Fine temporal resolution
    refractory_frames=3,        # Longer suppression period
    decay_window=4.5            # Slower time surface decay
)

# Create with minimal interpolation
sim_fast = VLAOptimizedDVSSimulator(subframe_count=1)

# Create with maximum sensitivity
sim_sensitive = VLAOptimizedDVSSimulator(
    positive_threshold=0.01,
    negative_threshold=0.01
)
```

---

### process()

Process a single frame and generate events.

```python
process(
    frame_bgr: np.ndarray,
    frame_index: int = 0
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list]
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `frame_bgr` | np.ndarray | Input frame in BGR format, shape (height, width, 3), dtype uint8 |
| `frame_index` | int | Frame sequence index. Used for event timestamps |

#### Returns

Tuple of four elements:

1. **event_visualization** (np.ndarray)
   - Shape: (height, width, 3)
   - Dtype: uint8
   - Format: BGR
   - Red pixels: ON events (polarity=+1)
   - Blue pixels: OFF events (polarity=-1)
   - Black pixels: No events

2. **time_surface_visualization** (np.ndarray)
   - Shape: (height, width, 3)
   - Dtype: uint8
   - Format: BGR with JET colormap
   - Bright colors: Recent events
   - Dark colors: Old events
   - Black: No events (older than decay_window)

3. **optical_flow_visualization** (np.ndarray)
   - Shape: (height, width, 3)
   - Dtype: uint8
   - Format: Grayscale frame with magenta motion arrows
   - Shows optical flow vectors
   - Useful for motion analysis

4. **events** (list)
   - List of tuples: `(x, y, polarity, timestamp)`
   - `x`, `y`: int - Pixel coordinates [0, width) × [0, height)
   - `polarity`: int - 1 for ON, -1 for OFF
   - `timestamp`: float - Frame time with subframe fraction

#### Raises

- `ValueError`: If frame shape doesn't match previous frames
- `RuntimeError`: If state not initialized (shouldn't happen)

#### Notes

- **First frame**: Initializes internal state, returns empty event list
- **Subsequent frames**: Generates events based on intensity changes
- **Timestamps**: Can have fractional parts (e.g., 5.2, 5.4, 5.6)
- **Events**: Sparse output, typically 0-1000 events per frame depending on motion and thresholds

#### Example

```python
import cv2
import numpy as np
from eventcamera import VLAOptimizedDVSSimulator

# Create simulator
sim = VLAOptimizedDVSSimulator()

# Read from camera
cap = cv2.VideoCapture(0)

frame_idx = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Process frame
    event_vis, ts_vis, flow_vis, events = sim.process(frame, frame_idx)
    
    # Display results
    cv2.imshow("Events", event_vis)
    cv2.imshow("Time Surface", ts_vis)
    cv2.imshow("Optical Flow", flow_vis)
    
    # Process events
    print(f"Generated {len(events)} events at frame {frame_idx}")
    for x, y, polarity, timestamp in events[:10]:  # First 10 events
        polarity_str = "ON" if polarity == 1 else "OFF"
        print(f"  Event: ({x}, {y}) {polarity_str} at t={timestamp:.2f}")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    frame_idx += 1

cap.release()
cv2.destroyAllWindows()
```

---

## 🖥️ EventCameraApplication

CLI application wrapper for event camera simulator.

### Constructor

```python
EventCameraApplication(
    video_source: str | int = 0,
    positive_threshold: float = 0.35,
    negative_threshold: float = 0.35,
    subframe_count: int = 5,
    refractory_frames: int = 2,
    decay_window: float = 3.0
) -> EventCameraApplication
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_source` | str \| int | 0 | Camera index (int) or file path (str) |
| All others | - | - | Same as VLAOptimizedDVSSimulator |

#### Example

```python
from src.main import EventCameraApplication

# Use default camera
app = EventCameraApplication()

# Use camera 1
app = EventCameraApplication(video_source=1)

# Process video file
app = EventCameraApplication(video_source="video.mp4")

# With custom parameters
app = EventCameraApplication(
    video_source=0,
    positive_threshold=0.25,
    subframe_count=10
)
```

---

### run()

Execute main application loop.

```python
run() -> int
```

#### Returns

Exit code:
- `0`: Success
- `1`: Error (video capture failed, exception occurred)
- `130`: User interrupt (Ctrl+C)

#### Notes

- Displays frames until EOF or user presses 'q'
- Automatically cleans up resources (windows, video capture)
- Safe exception handling (try/finally)

#### Example

```python
from src.main import EventCameraApplication

app = EventCameraApplication()
exit_code = app.run()

if exit_code == 0:
    print("Application completed successfully")
elif exit_code == 130:
    print("User interrupted application")
else:
    print("Error occurred")
```

---

## 🛠️ Utility Functions

### parse_video_source()

Intelligently detect video source type.

```python
parse_video_source(source_string: str) -> int | str
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_string` | str | Camera index or file path as string |

#### Returns

- `int`: If string is numeric (camera index)
- `str`: If string is non-numeric (file path)

#### Example

```python
from src.main import parse_video_source

# Camera index
source = parse_video_source("0")
assert isinstance(source, int)  # True

# File path
source = parse_video_source("video.mp4")
assert isinstance(source, str)  # True
```

---

## 📊 Data Structures

### Event Tuple

```python
event: tuple[int, int, int, float] = (x, y, polarity, timestamp)

# Example
event = (320, 240, 1, 5.2)  # ON event at (320,240) at time 5.2
```

| Index | Name | Type | Range | Meaning |
|-------|------|------|-------|---------|
| 0 | x | int | [0, width) | Pixel x-coordinate |
| 1 | y | int | [0, height) | Pixel y-coordinate |
| 2 | polarity | int | {-1, 1} | -1=OFF, 1=ON |
| 3 | timestamp | float | [0, ∞) | Event time (frame + fraction) |

---

## 🎨 Visualization Formats

### Event Visualization

```python
event_vis.shape == (height, width, 3)  # BGR format
event_vis.dtype == np.uint8
```

Color encoding:
- **Red (0, 0, 255)**: ON events (positive change)
- **Blue (255, 0, 0)**: OFF events (negative change)
- **Black (0, 0, 0)**: No events

### Time Surface Visualization

```python
ts_vis.shape == (height, width, 3)  # BGR format
ts_vis.dtype == np.uint8
```

Colormap: JET
- **Bright (yellow/red)**: Recent events
- **Dark (blue)**: Older events
- **Black (0, 0, 0)**: No recent events (>decay_window)

### Optical Flow Visualization

```python
flow_vis.shape == (height, width, 3)  # BGR format
flow_vis.dtype == np.uint8
```

- **Grayscale background**: Input frame
- **Magenta arrows (255, 0, 255)**: Motion vectors
- Spacing: 16 pixels (configurable)
- Only shows vectors with magnitude > 0.5

---

## ⚙️ Configuration Classes

### None (Configuration via constructor parameters)

All configuration is done through constructor parameters. No separate config objects.

---

## 📝 Error Handling

### Exceptions

The simulator is robust but can raise:

1. **ValueError** - Invalid parameter ranges
2. **RuntimeError** - Unexpected state (shouldn't occur)
3. **opencv.error** - OpenCV operation failed

### Examples

```python
from eventcamera import VLAOptimizedDVSSimulator

# ValueError: threshold out of range
try:
    sim = VLAOptimizedDVSSimulator(positive_threshold=5.0)
except ValueError as e:
    print(f"Invalid threshold: {e}")

# OpenCV error: frame shape mismatch
sim = VLAOptimizedDVSSimulator()
frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
frame2 = np.zeros((720, 1280, 3), dtype=np.uint8)

sim.process(frame1, 0)
try:
    sim.process(frame2, 1)  # Shape mismatch!
except ValueError as e:
    print(f"Frame shape mismatch: {e}")
```

---

## 🔗 Integration Examples

### With NumPy/OpenCV

```python
import cv2
import numpy as np
from eventcamera import VLAOptimizedDVSSimulator

sim = VLAOptimizedDVSSimulator()

# Generate synthetic frames
for i in range(10):
    # Gradient frame
    frame = np.tile(
        np.arange(256, dtype=np.uint8)[np.newaxis, :],
        (480, 1)
    )[:, :640].repeat(3, axis=2)
    
    event_vis, ts_vis, flow_vis, events = sim.process(frame, i)
    
    # Analyze events
    event_array = np.array(events)
    if len(events) > 0:
        polarities = event_array[:, 2]
        on_count = np.sum(polarities == 1)
        off_count = np.sum(polarities == -1)
        print(f"Frame {i}: {on_count} ON, {off_count} OFF events")
```

### With Video File

```python
import cv2
from eventcamera import VLAOptimizedDVSSimulator

sim = VLAOptimizedDVSSimulator(subframe_count=10)
cap = cv2.VideoCapture("video.mp4")

frame_idx = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    _, _, _, events = sim.process(frame, frame_idx)
    print(f"Frame {frame_idx}: {len(events)} events")
    
    frame_idx += 1

cap.release()
```

---

**Last Updated**: 2026-09-15  
**API Version**: 1.0.0  
**Stability**: Stable
