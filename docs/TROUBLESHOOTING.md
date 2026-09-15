# Troubleshooting Guide

Common issues and solutions for the event camera simulator.

## 🎥 Camera & Video Issues

### Camera Not Found

**Error**: `Error: Failed to initialize video capture.`

**Causes**:
- Camera not connected
- Camera already in use (another app)
- Wrong camera index
- No camera permission

**Solutions**:

```bash
# Try camera index 1 instead of 0
python src/main.py --source 1

# Try camera index 2
python src/main.py --source 2

# Check available cameras (on Linux)
ls -la /dev/video*
```

**On Linux**: Grant camera permissions
```bash
sudo usermod -a -G video $USER
# Log out and back in
```

**On macOS**: Grant camera access in System Preferences

**On Windows**: Check Device Manager for camera, ensure drivers installed

---

### Video File Not Found

**Error**: `OpenCV Error: (-215:Assertion failed) ...`

**Causes**:
- File doesn't exist
- Incorrect file path
- Unsupported video codec

**Solutions**:

```bash
# Use absolute path
python src/main.py --source "/full/path/to/video.mp4"

# Check file exists
ls -la video.mp4

# Try different video format
python src/main.py --source video.avi
```

**Supported formats**: MP4, AVI, MOV, MKV (depending on OpenCV codec support)

---

### Video Won't Play/Black Screen

**Error**: Video runs but displays only black screen

**Causes**:
- Video file corrupted
- Codec not installed
- Video is blank/empty

**Solutions**:

```bash
# Test video with ffplay (if installed)
ffplay video.mp4

# Try converting video with ffmpeg
ffmpeg -i video.mp4 -c:v libx264 video_converted.mp4
python src/main.py --source video_converted.mp4
```

---

### High CPU Usage / Slow Performance

**Error**: Application running slowly, high CPU usage

**Causes**:
- Too many subframes (temporal interpolation)
- Too low thresholds (generating too many events)
- High-resolution video

**Solutions**:

```bash
# Reduce temporal interpolation
python src/main.py --subframes 1

# Increase thresholds (fewer events)
python src/main.py --pos-threshold 0.8 --neg-threshold 0.8

# Reduce refractory period (generate fewer events)
python src/main.py --refractory 5
```

**Performance impact** (on typical hardware):
```
subframes=1:   ~100 fps
subframes=5:   ~20 fps
subframes=10:  ~10 fps
subframes=20:  ~5 fps
```

---

## 🎯 Event Detection Issues

### Too Many Events (Noisy Output)

**Symptom**: Event visualization is overwhelmingly crowded, hard to see patterns

**Causes**:
- Thresholds too low
- High ambient noise
- High illumination changes
- Refractory period too short

**Solutions**:

```bash
# Increase thresholds (higher = less sensitive)
python src/main.py --pos-threshold 0.5 --neg-threshold 0.5

# Increase refractory period (suppress repeated events)
python src/main.py --refractory 5

# Combine both
python src/main.py --pos-threshold 0.5 --neg-threshold 0.5 --refractory 3
```

**Expected behavior**:
- Edges and moving objects should show events
- Flat, stationary areas should be quiet
- If flat areas have events → thresholds too low

---

### Too Few Events (Missing Motion)

**Symptom**: Even with obvious motion, very few or no events generated

**Causes**:
- Thresholds too high
- Video has low contrast
- Motion is very slow
- Refractory period too long

**Solutions**:

```bash
# Decrease thresholds (lower = more sensitive)
python src/main.py --pos-threshold 0.1 --neg-threshold 0.1

# Decrease refractory period
python src/main.py --refractory 0

# Reduce subframes (can help with slow motion)
python src/main.py --subframes 10
```

**Debug threshold**:
```python
from eventcamera import VLAOptimizedDVSSimulator
import cv2

# Test different thresholds
for threshold in [0.05, 0.15, 0.35, 0.65, 1.0]:
    sim = VLAOptimizedDVSSimulator(positive_threshold=threshold)
    # Process frame and count events
    _, _, _, events = sim.process(frame, 0)
    print(f"Threshold {threshold}: {len(events)} events")
```

---

### Events Only on Edges

**Symptom**: Events only appear at object boundaries, not in interiors

**Causes**:
- Expected behavior (events are edge-based)
- Thresholds too high
- Video has low gradient

**Solutions**:

This is **normal behavior**! DVS sensors detect changes, not absolute intensity.

If you need interior events:
```bash
# Significantly lower thresholds
python src/main.py --pos-threshold 0.05 --neg-threshold 0.05
```

---

### Events Not Following Motion

**Symptom**: Events seem to lag or jump, not following smooth motion path

**Causes**:
- Insufficient temporal resolution
- Optical flow estimation failing
- Very fast motion
- High motion blur in video

**Solutions**:

```bash
# Increase temporal resolution
python src/main.py --subframes 10

# Combine with lower thresholds
python src/main.py --subframes 10 --pos-threshold 0.2

# Check optical flow with visualization
# (Press 'q' but note the "Optical Flow" window)
```

---

## 🎨 Visualization Issues

### Time Surface Always Black

**Symptom**: Time surface visualization is entirely black

**Causes**:
- No events being generated (see "Too Few Events")
- Decay window too short

**Solutions**:

```bash
# Increase decay window (longer visibility)
python src/main.py --decay 10.0

# Check if events exist at all
python src/main.py --pos-threshold 0.1 --neg-threshold 0.1
```

---

### Optical Flow Arrows Missing

**Symptom**: Optical flow visualization has no arrows, just grayscale image

**Causes**:
- Low motion (arrows only show if magnitude > 0.5)
- Camera is stationary
- Video is compressed artifacts

**Solutions**:

```bash
# Movement is too subtle, try with moving camera
python src/main.py --source video_with_motion.mp4

# The visualization only shows larger motion vectors
# This is expected and correct behavior
```

---

### Event Visualization Flickering

**Symptom**: Events appear and disappear rapidly, hard to see pattern

**Causes**:
- No refractory period (events firing constantly)
- Very low thresholds
- Video has jitter/noise

**Solutions**:

```bash
# Increase refractory period
python src/main.py --refractory 5

# Increase thresholds
python src/main.py --pos-threshold 0.5

# Reduce subframes (faster processing, less temporal noise)
python src/main.py --subframes 1
```

---

## ⚙️ Parameter-Related Issues

### Application Too Slow

**Symptom**: Application running at < 10 fps

**Causes**:
- High subframe count
- Low thresholds (generating too many events)
- High video resolution

**Solutions** (in order of impact):

```bash
# 1. Reduce subframes (biggest impact)
python src/main.py --subframes 1

# 2. Increase thresholds
python src/main.py --subframes 1 --pos-threshold 0.8

# 3. Increase refractory
python src/main.py --subframes 1 --pos-threshold 0.8 --refractory 5
```

**Performance expectations**:
```
subframes=1,  thresholds=0.35: ~50 fps (typical)
subframes=5,  thresholds=0.35: ~10 fps (default)
subframes=10, thresholds=0.35: ~5 fps
```

---

### Parameters Not Changing Behavior

**Symptom**: Parameters don't seem to affect output

**Causes**:
- Application caching parameters
- Parameters out of valid range
- Changes need significant scene change to see

**Solutions**:

```bash
# Verify parameters with extreme values
python src/main.py --pos-threshold 0.01   # Should be very noisy
python src/main.py --pos-threshold 1.5    # Should be very quiet

# If still no change, check application is running
# (verify output windows show up)
```

---

## 🛠️ Installation & Dependency Issues

### Module Not Found: 'eventcamera'

**Error**: `ModuleNotFoundError: No module named 'eventcamera'`

**Causes**:
- Package not installed
- Wrong directory
- Virtual environment not activated

**Solutions**:

```bash
# Install package
pip install -e .

# Or with uv
uv sync

# Verify installation
python -c "from eventcamera import VLAOptimizedDVSSimulator; print('OK')"
```

---

### OpenCV Error: CUDA/GPU Not Found

**Error**: `OpenCV Error: cuda runtime not found`

**Causes**:
- OpenCV built without CUDA support
- CUDA drivers not installed

**Solutions**:

```bash
# This is not a critical error - application will run on CPU
# To verify CPU mode works:
python src/main.py

# Install OpenCV with CPU support
pip install opencv-python
```

---

### Memory Issues (Out of Memory)

**Error**: Application crashes after running for a while

**Causes**:
- Processing very long video
- Subframe count too high
- Too many events being stored

**Solutions**:

```bash
# Process in chunks
python src/main.py --subframes 1  # Lower memory usage

# Monitor memory usage
# (on Linux: watch -n 1 'ps aux | grep python')

# Process shorter clips if full video too large
ffmpeg -i long_video.mp4 -t 60 short_clip.mp4  # First 60 seconds
python src/main.py --source short_clip.mp4
```

---

## 🐛 Debugging Tips

### Enable Verbose Output

```bash
# Add Python debugging
python -u src/main.py

# With profiling (if needed)
python -m cProfile -s cumtime src/main.py
```

### Test with Minimal Example

```python
import numpy as np
from eventcamera import VLAOptimizedDVSSimulator

# Create simple frames
sim = VLAOptimizedDVSSimulator()

# Frame 1: Dark
frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
sim.process(frame1, 0)

# Frame 2: Bright
frame2 = np.full((480, 640, 3), 255, dtype=np.uint8)
_, _, _, events = sim.process(frame2, 1)

print(f"Generated {len(events)} events")
# Expected: Should generate many events (brightness change)
```

### Check Hardware

```bash
# GPU availability (if using CUDA)
python -c "import cv2; print(cv2.cuda.getCudaEnabledDeviceCount())"

# CPU count
python -c "import os; print(os.cpu_count())"

# Memory available
python -c "import psutil; print(psutil.virtual_memory().available / 1e9, 'GB')"
```

---

## 📞 Getting Help

If issues persist:

1. **Check this guide** - Most common issues covered
2. **Review logs** - Check terminal output for specific errors
3. **Test minimal example** - Verify issue reproducible with simple case
4. **Check version** - Update to latest version
   ```bash
   pip install --upgrade eventcamera
   ```
5. **Create issue** - Include:
   - Exact command you ran
   - Error message (full traceback)
   - Hardware info (OS, Python version, OpenCV version)
   - Minimal reproducible example

---

## 🆘 FAQ

**Q: Can I process multiple videos in parallel?**  
A: Yes, create separate `VLAOptimizedDVSSimulator` instances in different threads or processes.

**Q: How do I save events to file?**  
A: Events are returned as lists of tuples. Save with JSON:
```python
import json
events_serializable = [(x, y, pol, float(ts)) for x, y, pol, ts in events]
with open('events.json', 'w') as f:
    json.dump(events_serializable, f)
```

**Q: Can I use with a web camera stream?**  
A: Yes, OpenCV supports IP cameras:
```bash
python src/main.py --source "http://192.168.1.100:8080/video"
```

**Q: How do I control frame rate?**  
A: OpenCV processes video at its native frame rate. To slow down:
```bash
# Process every Nth frame
for i, frame in enumerate(frame_sequence):
    if i % 2 == 0:  # Process every other frame
        sim.process(frame, i)
```

**Q: What's the maximum resolution supported?**  
A: Theoretically unlimited, but performance depends on hardware. Typical: up to 1080p@30fps on modern hardware.

**Q: Can I use with depth cameras?**  
A: Currently only RGB/grayscale. Would need separate extension.

---

**Last Updated**: 2026-09-15  
**Coverage**: Most common issues and solutions
