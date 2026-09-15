# Parameter Tuning Guide

Complete guide to understanding and tuning event camera simulator parameters.

## 🎯 Parameter Overview

The simulator has 5 main parameters controlling event detection and output:

| Parameter | Default | Range | Impact | Speed |
|-----------|---------|-------|--------|-------|
| `positive_threshold` | 0.35 | (0, 3.0] | ON event sensitivity | None |
| `negative_threshold` | 0.35 | (0, 3.0] | OFF event sensitivity | None |
| `subframe_count` | 5 | [1, 100] | Temporal resolution | ⬇️ (slower) |
| `refractory_frames` | 2 | [0, 100] | Saturation suppression | ⬇️ (more events) |
| `decay_window` | 3.0 | (0, 10.0] | Time surface decay | None |

---

## 📊 Parameter 1: positive_threshold

Controls sensitivity to **brightness increases** (ON events).

### What It Does

```
ON event fires when: log_intensity_change > positive_threshold
```

Lower value = more sensitive = more ON events

### Value Ranges

```
Very Sensitive      Sensitive      Moderate       Insensitive    Very Insensitive
0.01               0.15           0.35           0.65           1.5
  ↑                                                               ↑
Detects tiny       Good for       Good for       Detects only   Detects only
brightness        hand motion    general use    major changes  extreme brightening
changes
```

### Effects

| Value | Events | Noise | Speed | Best For |
|-------|--------|-------|-------|----------|
| 0.01 | ⬆️⬆️ Huge | ⬆️⬆️ High | ⬇️ Slow | Research, detailed motion |
| 0.15 | ⬆️ Many | ⬆️ Moderate | Normal | Hand tracking, gestures |
| 0.35 | ✓ Balanced | ✓ Low | ✓ Normal | **Default, general use** |
| 0.65 | ⬇️ Few | ⬇️ Very low | ✓ Fast | Sparse motion only |
| 1.5 | ⬇️⬇️ Minimal | ⬇️⬇️ None | ✓ Fast | High-contrast scenes only |

### Visual Comparison

```
Same scene, different positive_threshold:

Original:  A person waving hand (moderate brightness change)

pos_thresh=0.01:  [████████████████] Dense events everywhere
                  Lots of noise, high computational load

pos_thresh=0.35:  [████████░░░░░░░░] Balanced events
                  Clean output, fast processing ✓

pos_thresh=0.65:  [████░░░░░░░░░░░░] Few events
                  Only main hand edges, might miss details

pos_thresh=1.5:   [██░░░░░░░░░░░░░░] Sparse events
                  Only extreme brightness jumps detected
```

### Recommendations

**For robotics (humanoid hand tracking):**
```bash
python src/main.py --pos-threshold 0.25
```
Lower threshold captures fine finger movements

**For general use:**
```bash
python src/main.py --pos-threshold 0.35  # Default
```

**For high-motion scenes (sports, fast motion):**
```bash
python src/main.py --pos-threshold 0.15
```
Captures rapid changes

**For low-motion scenes (surveillance):**
```bash
python src/main.py --pos-threshold 0.65
```
Reduces noise from static content

---

## 📊 Parameter 2: negative_threshold

Controls sensitivity to **brightness decreases** (OFF events).

### What It Does

```
OFF event fires when: log_intensity_change < -negative_threshold
```

Same principles as `positive_threshold` but for darkening.

### Typical Values

Usually set **equal to** `positive_threshold`:

```bash
python src/main.py --pos-threshold 0.35 --neg-threshold 0.35
```

### When to Separate

Different lighting scenarios:

```bash
# Bright object on dark background (motion-capture)
# Want more ON events, fewer OFF events
python src/main.py --pos-threshold 0.2 --neg-threshold 0.5

# Dark object on bright background (surveillance)
# Want more OFF events, fewer ON events
python src/main.py --pos-threshold 0.5 --neg-threshold 0.2
```

---

## 📊 Parameter 3: subframe_count

Controls temporal resolution through **sub-frame interpolation**.

### What It Does

Each video frame is divided into N interpolation steps:

```
N=1:  Frame 0 → Frame 1
      One comparison, fast

N=5:  Frame 0 → [Sub1, Sub2, Sub3, Sub4, Sub5] → Frame 1
      Five comparisons, fine-grained timing

N=20: Frame 0 → [20 subframes] → Frame 1
      Fine-grained, slow
```

### Temporal Resolution Achieved

Assuming 30fps video:

```
Frame rate:  33.3 ms per frame

subframe_count=1:   33.3 ms resolution (standard frame-based)
subframe_count=5:   6.7 ms resolution
subframe_count=10:  3.3 ms resolution
subframe_count=20:  1.7 ms resolution
```

### Effects

| Value | Events | Timing Accuracy | Speed | Best For |
|-------|--------|-----------------|-------|----------|
| 1 | ⬇️ Few | Poor | ⬆️ Fastest | Fast prototyping |
| 5 | ✓ Balanced | ✓ Good | ✓ Normal | **Default, general** |
| 10 | ⬆️ More | Excellent | ⬇️ 2× slower | Research, fine motion |
| 20 | ⬆️⬆️ Many | Microsecond | ⬇️⬇️ 4× slower | Very precise timing |

### Visual Example

Hand moving across screen:

```
subframe_count=1:
Events at frame 0, frame 1, frame 2, ...
Temporal gaps between events

subframe_count=5:
Events at 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, ...
Smooth continuous motion trail ✓

subframe_count=20:
Events at 0.05, 0.10, 0.15, ...
Very smooth, dense timeline
```

### Recommendations

**Fast feedback (prototyping):**
```bash
python src/main.py --subframes 1
```

**Balanced (default):**
```bash
python src/main.py --subframes 5  # Default
```

**Precise timing (research):**
```bash
python src/main.py --subframes 10
```

**Maximum precision (detailed analysis):**
```bash
python src/main.py --subframes 20
```

### Performance Impact

Subframe count directly multiplies computation:

```
Processing time ≈ subframe_count × base_time

subframes=1:  base_time
subframes=5:  5× base_time
subframes=10: 10× base_time
```

Consider this when processing high-resolution video in real-time.

---

## 📊 Parameter 4: refractory_frames

Controls **refractory period** (event suppression after firing).

### What It Does

After a pixel fires an event, it's suppressed for N frames:

```
Frame 0: Event fires → refractory_map = 2
Frame 1: refractory_map = 1 → No events allowed
Frame 2: refractory_map = 0 → Can fire again
```

### Effects

| Value | Events | Noise | Repeated Events | Speed |
|-------|--------|-------|-----------------|-------|
| 0 | ⬆️⬆️ Max | ⬆️⬆️ High | ✓ Yes | ⬇️ Slowest |
| 1 | ⬆️ Many | ⬆️ Moderate | ⬇️ Some | Normal |
| 2 | ✓ Balanced | ✓ Low | ✓ Rare | ✓ Normal |
| 5 | ⬇️ Few | ⬇️ Very low | ⬇️⬇️ None | ⬆️ Faster |
| 10 | ⬇️⬇️ Sparse | ⬇️⬇️ None | ⬇️⬇️ None | ⬆️⬆️ Fastest |

### Visual Example

Oscillating light (flickers on/off rapidly):

```
refractory=0:
Rapid ON/OFF events alternating quickly
High event rate, possibly saturated

refractory=2:
ON event → suppression → OFF event → suppression
Fewer events, cleaner temporal pattern ✓

refractory=5:
After ON event, long period with no events
Only major transitions detected
```

### Recommendations

**Capture all detail (research):**
```bash
python src/main.py --refractory 0
```
No suppression, high event rate

**Balanced (default):**
```bash
python src/main.py --refractory 2  # Default
```
Good for hand tracking

**Reduce noise:**
```bash
python src/main.py --refractory 3
```
Suppress repeated events

**Sparse output (extreme cases):**
```bash
python src/main.py --refractory 10
```
Only major changes

### Trade-offs

```
Lower refractory:
  + More detail captured
  - More noise
  - Slower processing

Higher refractory:
  + Cleaner output
  + Faster processing
  - May miss rapid changes
```

---

## 📊 Parameter 5: decay_window

Controls **time surface decay** (visualization only).

### What It Does

Pixels in time surface fade out over time:

```
decay_window = 3.0 frames

intensity(pixel) = 1.0 - (current_time - last_event_time) / 3.0

Time since event:
0.0 s → intensity = 1.0 (bright)
1.5 s → intensity = 0.5 (medium)
3.0 s → intensity = 0.0 (black, disappeared)
```

### Effects

| Value | Recent Events | Old Events | Best For |
|-------|---------------|-----------|----------|
| 0.5 | ⬆️ Bright | ⬇️⬇️ Fade fast | Real-time tracking |
| 1.0 | ✓ Visible | ⬇️ Fade quick | Standard use |
| 3.0 | ✓ Visible | ✓ Linger | **Default** |
| 5.0 | ✓ Bright | ⬆️ Linger long | Trail visualization |
| 10.0 | ⬆️ Very bright | ⬆️⬆️ Long trails | Historical analysis |

### Visual Example

Hand moving left-to-right across screen:

```
decay_window = 0.5:
Current hand bright, previous positions immediately black
⭕→  (snapshot of current position only)

decay_window = 3.0:
Current hand bright, recent path visible
⭕→ ⭕→ ⭕→  (few recent positions) ✓

decay_window = 10.0:
Long trail of the hand's motion
⭕→ ⭕→ ⭕→ ⭕→ ⭕→ ⭕→  (extended history)
```

### Recommendations

**Real-time response (robotics):**
```bash
python src/main.py --decay 1.0
```
See only immediate motion

**Standard visualization:**
```bash
python src/main.py --decay 3.0  # Default
```

**Motion trails (analysis):**
```bash
python src/main.py --decay 5.0
```
See motion trajectory

**Long historical view:**
```bash
python src/main.py --decay 10.0
```
Complete motion record

---

## 🎮 Use Case Configurations

### Configuration 1: Hand Gesture Recognition (Robotics)

```bash
python src/main.py \
    --pos-threshold 0.25 \
    --neg-threshold 0.25 \
    --subframes 5 \
    --refractory 2 \
    --decay 3.0
```

**Why:**
- Lower thresholds: Capture fine finger movements
- Medium subframes: Balanced timing + speed
- Standard refractory: Clean output
- Standard decay: Good visibility

### Configuration 2: High-Speed Motion (Sports)

```bash
python src/main.py \
    --pos-threshold 0.15 \
    --neg-threshold 0.15 \
    --subframes 10 \
    --refractory 1 \
    --decay 1.0
```

**Why:**
- Very low thresholds: Rapid changes
- High subframes: Precise timing
- Low refractory: Capture frequent events
- Short decay: See only current motion

### Configuration 3: Surveillance (Low Motion)

```bash
python src/main.py \
    --pos-threshold 0.65 \
    --neg-threshold 0.65 \
    --subframes 2 \
    --refractory 5 \
    --decay 5.0
```

**Why:**
- High thresholds: Only significant changes
- Low subframes: Fast processing
- High refractory: Minimize noise
- Long decay: See motion history

### Configuration 4: Research (Maximum Detail)

```bash
python src/main.py \
    --pos-threshold 0.1 \
    --neg-threshold 0.1 \
    --subframes 20 \
    --refractory 0 \
    --decay 3.0
```

**Why:**
- Very low thresholds: Capture everything
- Maximum subframes: Precise timing
- No refractory: All events
- Standard decay: Good visualization

### Configuration 5: Video Processing (Batch)

```bash
python src/main.py \
    --source video.mp4 \
    --pos-threshold 0.35 \
    --neg-threshold 0.35 \
    --subframes 3 \
    --refractory 2 \
    --decay 3.0
```

**Why:**
- File-based: Process stored video
- Standard thresholds: General-purpose
- Low subframes: Speed for large files
- Standard settings: Balanced quality

---

## 📈 Tuning Workflow

### Step 1: Start with Defaults
```bash
python src/main.py
```

### Step 2: Evaluate Initial Output

- Too many events? → Increase thresholds
- Too few events? → Decrease thresholds
- Temporal jitter? → Increase subframes
- Too slow? → Decrease subframes or increase refractory
- Pixelation in time surface? → Adjust decay

### Step 3: Adjust Based on Needs

```bash
# Too much noise
python src/main.py --pos-threshold 0.5 --neg-threshold 0.5

# Need finer timing
python src/main.py --subframes 10

# Want motion trails
python src/main.py --decay 5.0
```

### Step 4: Iterate

Re-evaluate, adjust, test until satisfied.

---

## 🔍 Debugging Parameter Effects

### Measure Event Count

```python
from eventcamera import VLAOptimizedDVSSimulator
import cv2

configs = [
    {"positive_threshold": 0.25},
    {"positive_threshold": 0.35},
    {"positive_threshold": 0.65},
]

cap = cv2.VideoCapture("video.mp4")
ret, frame = cap.read()
cap.release()

for config in configs:
    sim = VLAOptimizedDVSSimulator(**config)
    sim.process(frame, 0)
    _, _, _, events = sim.process(frame, 1)
    print(f"Config {config}: {len(events)} events")
```

### Profile Performance

```bash
# Time the execution
time python src/main.py --source video.mp4 --subframes 5
time python src/main.py --source video.mp4 --subframes 10
```

---

**Last Updated**: 2026-09-15  
**Version**: 1.0.0
