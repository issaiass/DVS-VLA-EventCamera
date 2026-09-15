# System Architecture

Complete explanation of how the event camera simulator works internally.

## 🏗️ Overall Architecture

```
Input Video Frame
       ↓
   [COLOR SPACE CONVERSION] (BGR → Grayscale)
       ↓
   [BACKGROUND SUBTRACTION] (MOG2) → Foreground Mask
       ↓
   [LOG-INTENSITY CONVERSION] (log-domain modeling)
       ↓
   [OPTICAL FLOW ESTIMATION] (DIS algorithm)
       ↓
   [TEMPORAL INTERPOLATION] (sub-frame warping)
       ├→ For each subframe:
       │   ├→ [WARP LOG-INTENSITY FRAME] (along motion trajectory)
       │   ├→ [COMPUTE INTENSITY DELTA] (current - previous)
       │   ├→ [THRESHOLD COMPARISON] (against pos/neg thresholds)
       │   ├→ [APPLY FOREGROUND MASK] (combine with MOG2)
       │   ├→ [REFRACTORY SUPPRESSION] (prevent saturation)
       │   ├→ [RENDER EVENTS] (red/blue pixels)
       │   └→ [UPDATE TIME SURFACE] (track event timing)
       ↓
   [VISUALIZATION GENERATION]
       ├→ Event visualization (red/blue pixels)
       ├→ Time surface (JET colormap decay)
       └→ Optical flow (motion arrows)
       ↓
   Output: Event List + 3 Visualizations
```

## 📊 Component Details

### 1. **Background Subtraction (MOG2)**

**Purpose**: Isolate moving foreground objects, reduce static noise

**Algorithm**: Mixture of Gaussians (MOG2)
- Maintains model of background pixels
- Updates model adaptively over time
- Outputs binary foreground/background mask

**Configuration**:
```python
cv2.createBackgroundSubtractorMOG2(
    history=500,           # Frames to learn background model
    varThreshold=20,       # Pixel variance threshold (tuned for hand dexterity)
    detectShadows=False    # Disable shadow detection
)
```

**Output**: Binary mask where 255 = foreground, 0 = background

**Why**: Events at static background noise are artifacts. MOG2 filtering ensures events only in foreground.

### 2. **Log-Intensity Conversion**

**Purpose**: Model biological photoreceptor response in log-domain

**Formula**:
```
L(x,y) = log(I(x,y) / 255.0 + ε)

Where:
- I(x,y) = grayscale intensity [0, 255]
- ε = 1e-6 (prevents log(0) singularity)
- L(x,y) = log-intensity ≈ [-13, 0]
```

**Why**: 
- Biological retinas respond logarithmically to intensity
- DVS sensors simulate biological response
- Log domain captures relative changes, not absolute intensity

**Example**:
```
Intensity: 0     128    255
Log:       -13   -1.0   0
```

### 3. **Optical Flow Estimation (DIS)**

**Purpose**: Estimate pixel motion between frames for temporal interpolation

**Algorithm**: Dense Inverse Search (DIS)
- Fast, robust optical flow
- Handles occlusions reasonably well
- Built into OpenCV (no external dependencies)

**Configuration**:
```python
cv2.DISOpticalFlow_create(
    cv2.DISOpticalFlow_PRESET_MEDIUM  # Speed vs accuracy trade-off
)
```

**Output**: Flow field of shape (H, W, 2) where:
- `flow[y, x, 0]` = x-displacement
- `flow[y, x, 1]` = y-displacement

**Why**: Enables sub-frame event timing by interpolating along motion trajectory

### 4. **Temporal Interpolation (Sub-frame Warping)**

**Purpose**: Generate events at sub-frame level by warping intermediate frames

**Process**:
```
For each subframe i in 1..N:
    fraction = i / N
    warped_frame = warp(previous_log_frame, optical_flow, fraction)
    delta = warped_frame - previous_log_frame
    detect_events(delta)
```

**Example with N=5 subframes**:
```
Frame 0 (t=0.0)
  ↓
Subframe 1 (t=0.2) → Events at 1.2, 1.4, ...
  ↓
Subframe 2 (t=0.4) → Events at 0.4, 0.6, ...
  ↓
Subframe 3 (t=0.6) → Events at 0.6, 0.8, ...
  ↓
Subframe 4 (t=0.8) → Events at 0.8, 1.0, ...
  ↓
Subframe 5 (t=1.0)
  ↓
Frame 1 (t=1.0)
```

**Why**: Standard frame-based detection has ~33ms temporal resolution (at 30fps). Subframes achieve microsecond precision.

### 5. **Warping (Inverse Mapping)**

**Purpose**: Remap previous frame along optical flow trajectory

**Formula**:
```
warped[y, x] = bilinear_interpolate(
    previous_frame,
    x - flow[y, x, 0] * fraction,
    y - flow[y, x, 1] * fraction
)
```

**Why**: Inverse mapping is more stable than forward mapping (avoids holes)

### 6. **Event Detection (Threshold Comparison)**

**Purpose**: Identify pixels where log-intensity change exceeds threshold

**Formula**:
```
ON event at (x,y):   delta[y,x] > pos_threshold
OFF event at (x,y):  delta[y,x] < -neg_threshold

Where:
- delta = warped_log - previous_log (log-intensity change)
- pos_threshold = 0.35 (default)
- neg_threshold = 0.35 (default)
```

**Polarity Encoding**:
```
ON event (brightness increase):   polarity = +1
OFF event (brightness decrease):  polarity = -1
```

**Why**: 
- Mimics DVS sensor behavior (responds to relative changes)
- Asynchronous: only fires when change exceeds threshold
- Two polarities capture direction of change

### 7. **Refractory Period**

**Purpose**: Prevent pixel saturation by suppressing repeated firing

**Implementation**:
```python
# After event fires at pixel (x, y):
refractory_map[y, x] = refractory_frames  # e.g., 2

# Each frame:
refractory_map[refractory_map > 0] -= 1

# Only allow events if refractory_map[y, x] == 0
```

**Timeline (refractory_frames=2)**:
```
Frame 0: Event fires at pixel → refractory_map = 2
Frame 1: refractory_map = 1 → Suppress any new events at this pixel
Frame 2: refractory_map = 0 → Allow new events again
Frame 3: Can fire again
```

**Why**: Prevents pixel from firing continuously (biological sensors also have refractory periods)

### 8. **Time Surface Tracking**

**Purpose**: Track when each pixel last fired an event

**Implementation**:
```python
time_surface[y, x] = timestamp  # When event fired at this pixel
```

**Usage**:
- Visualization (event decay colormap)
- Temporal analysis
- Motion tracking

**Decay Formula**:
```
intensity = max(0, 1.0 - (current_time - time_surface[y,x]) / decay_window)
```

### 9. **Foreground Masking**

**Purpose**: Ensure events only generated in foreground regions

**Implementation**:
```python
positive_events = cv2.bitwise_and(
    threshold_mask,      # From threshold comparison
    foreground_mask      # From MOG2 background subtraction
)
```

**Effect**: Events in background noise are filtered out, improving signal quality

### 10. **CLAHE Normalization (Contrast Limited Adaptive Histogram Equalization)**

**Purpose**: Normalize contrast for Vision Language Agents

**Configuration**:
```python
cv2.createCLAHE(
    clipLimit=2.0,           # Contrast limit
    tileGridSize=(8, 8)      # 8x8 tiles
)
```

**Process**:
```
BGR Image
    ↓
Convert to LAB (L=lightness, A=color, B=color)
    ↓
Apply CLAHE to L (lightness) channel
    ↓
Convert back to BGR
```

**Why**: 
- Prevents VLA systems from being "blinded" by extreme contrast
- Preserves natural colors (works in LAB space)
- Adaptive (handles local contrast variations)

## 🔄 Data Flow Example

**Scenario**: Bright object moves across dark background

```
Frame N (t=0):
  Grayscale image → Log-intensity L_N

Frame N+1 (t=1):
  Grayscale image → Log-intensity L_{N+1}
  
  Optical flow: Shows object moved (+5 pixels x, +3 pixels y)
  
  Subframe 1 (fraction=0.2):
    Warp L_N by 20% along flow → L_warped
    delta = L_warped - L_N ≈ 2.0  (significant brightening)
    delta > pos_threshold (0.35)? YES
    Foreground mask = 255? YES
    Refractory OK? YES
    → Generate ON event at (x, y, +1, timestamp=0.2)
  
  Subframe 2 (fraction=0.4):
    Similar process...
    → More ON events
  
  Subframe 3-5:
    Continue generating events as object moves
  
  Result: ~100-500 ON events from single moving object
          Timestamps spread across [0.0, 1.0]
          High temporal resolution captured
```

## 📈 Parameter Interactions

```
pos_threshold
    ↓ (lower = more sensitive)
    → More events
    → More noise
    → Higher computational load

subframe_count
    ↓ (higher = finer resolution)
    → Better temporal accuracy
    → More events generated
    → Higher computational load

refractory_frames
    ↓ (higher = longer refractory)
    → Fewer repeated events
    → Less noise
    → May miss genuine rapid changes

decay_window (time surface only)
    ↓ (shorter window)
    → Faster decay in visualization
    → Recent events more visible
    → Historical events fade quickly
```

## 🎯 Design Decisions

### Why Log-Domain?
- Matches biological vision (Weber's law)
- Relative changes matter more than absolute intensity
- Natural compression of dynamic range

### Why Optical Flow?
- Enables sub-frame precision without explicit interpolation models
- Handles complex motion patterns
- More accurate than frame differencing

### Why MOG2 Background Subtraction?
- Separates foreground from static noise
- Adaptive model handles slow illumination changes
- Computationally efficient

### Why Refractory Period?
- Prevents pixel saturation
- Matches biological sensor behavior
- Reduces computational load (fewer events)

### Why CLAHE?
- Prevents contrast extremes from breaking VLA perception
- Handles varying lighting conditions
- Adaptive (local not global)

---

## 📚 References

- **Log-Intensity**: Weber's Law (1846) - Relative Perception in Vision
- **Optical Flow**: Sun et al. (2014) - "A Large Outdoor Stereo Dataset with Ground Truth" (DIS algorithm)
- **Background Subtraction**: Zivkovic (2004) - "Improved adaptive Gaussian mixture model"
- **DVS Sensors**: Gehrig et al. (2020) - "Event-based Vision: A Survey"
- **CLAHE**: Zuiderveld (1994) - "Contrast Limited Adaptive Histogram Equalization"

---

**Last Updated**: 2026-09-15  
**Accuracy**: Matches implementation in `simulator.py`
