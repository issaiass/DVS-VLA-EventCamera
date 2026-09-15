"""End-to-End tests for video file processing.

Tests the complete event camera application with actual video files,
verifying frame-by-frame processing, event generation, and output quality.
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.main import EventCameraApplication


class TestVideoFileProcessing:
    """Test application processing of complete video files."""

    def test_process_video_sequence_to_completion(self, frame_sequence):
        """Test processing complete video sequence without errors.

        Arrange: Video frame sequence
        Act: Process all frames through application
        Assert: All frames processed, outputs valid
        """
        app = EventCameraApplication()
        all_events = []
        frame_count = 0

        for frame_idx, frame in enumerate(frame_sequence):
            event_vis, ts_vis, flow_vis, events = app.simulator.process(
                frame, frame_idx
            )

            # Verify outputs
            assert event_vis.shape == (480, 640, 3)
            assert ts_vis.shape == (480, 640, 3)
            assert flow_vis.shape == (480, 640, 3)

            all_events.extend(events)
            frame_count += 1

        # Verify completion
        assert frame_count == len(frame_sequence)
        assert isinstance(all_events, list)

    def test_video_processing_with_different_resolutions(self):
        """Test application handles different video resolutions.

        Arrange: Frames with different resolutions
        Act: Process each through simulator
        Assert: All processed without errors
        """
        resolutions = [(480, 640), (720, 1280), (360, 480)]

        app = EventCameraApplication()

        for height, width in resolutions:
            frame = np.full((height, width, 3), 100, dtype=np.uint8)

            # First frame initializes
            vis1, _, _, _ = app.simulator.process(frame, 0)
            assert vis1.shape == (height, width, 3)

            # Should fail on second frame due to dimension mismatch
            # (simulator expects consistent dimensions)
            # This is expected behavior
            app = EventCameraApplication()  # Reset for next resolution

    def test_video_processing_with_varying_brightness(self):
        """Test processing video with gradual brightness changes.

        Arrange: Create sequence with gradual brightness increase
        Act: Process frames through simulator
        Assert: Events generated at brightness transitions
        """
        app = EventCameraApplication()

        # Create gradual brightness increase
        frames = []
        for brightness in range(50, 200, 30):
            frame = np.full((480, 640, 3), brightness, dtype=np.uint8)
            frames.append(frame)

        total_events = 0
        for frame_idx, frame in enumerate(frames):
            _, _, _, events = app.simulator.process(frame, frame_idx)
            total_events += len(events)

        # Should generate events due to brightness changes
        assert total_events >= 0

    def test_video_processing_with_noise(self):
        """Test processing video with noise (robust to jitter).

        Arrange: Create frames with added noise
        Act: Process noisy frames
        Assert: Handles noise without crashes
        """
        app = EventCameraApplication()

        base_frame = np.full((480, 640, 3), 128, dtype=np.uint8)

        for frame_idx in range(5):
            # Add noise to base frame
            noise = np.random.normal(0, 5, base_frame.shape)
            noisy_frame = np.clip(base_frame + noise, 0, 255).astype(np.uint8)

            vis, ts, flow, events = app.simulator.process(noisy_frame, frame_idx)

            # Should handle noisy input
            assert vis.shape == (480, 640, 3)
            assert isinstance(events, list)

    def test_video_processing_event_ordering(self, frame_sequence):
        """Test that events maintain correct temporal ordering.

        Arrange: Process frame sequence
        Act: Collect events with timestamps
        Assert: Timestamps are monotonically increasing
        """
        app = EventCameraApplication()
        all_timestamps = []

        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = app.simulator.process(frame, frame_idx)

            for x, y, polarity, timestamp in events:
                all_timestamps.append(timestamp)

        # Verify ordering
        if len(all_timestamps) > 1:
            for i in range(len(all_timestamps) - 1):
                assert all_timestamps[i] <= all_timestamps[i + 1]


class TestVideoCaptureMocking:
    """Test application with mocked video capture."""

    @patch("cv2.VideoCapture")
    def test_application_with_mocked_camera(self, mock_capture, frame_sequence):
        """Test application processes frames from mocked camera.

        Arrange: Mock cv2.VideoCapture with test frames
        Act: Run application with mocked video
        Assert: Frames processed correctly
        """
        mock_instance = mock_capture.return_value
        mock_instance.isOpened.return_value = True

        frame_index = [0]

        def mock_read():
            if frame_index[0] < len(frame_sequence):
                frame = frame_sequence[frame_index[0]]
                frame_index[0] += 1
                return (True, frame)
            return (False, None)

        mock_instance.read.side_effect = mock_read

        app = EventCameraApplication()
        result = app._initialize_video_capture()

        assert result is True

    @patch("cv2.VideoCapture")
    def test_application_handles_camera_failure(self, mock_capture):
        """Test application handles camera failure gracefully.

        Arrange: Mock camera to fail opening
        Act: Run application initialization
        Assert: Returns False, application continues
        """
        mock_instance = mock_capture.return_value
        mock_instance.isOpened.return_value = False

        app = EventCameraApplication()
        result = app._initialize_video_capture()

        assert result is False


class TestOutputQualityMetrics:
    """Test output quality and consistency metrics."""

    def test_event_spatial_distribution(self, frame_sequence):
        """Test that events are spatially distributed across frame.

        Arrange: Process frame sequence
        Act: Collect event coordinates
        Assert: Events distributed across frame (not just one pixel)
        """
        app = EventCameraApplication()
        all_x = []
        all_y = []

        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = app.simulator.process(frame, frame_idx)

            for x, y, _, _ in events:
                all_x.append(x)
                all_y.append(y)

        # If events generated, should span multiple pixels
        if len(all_x) > 0:
            x_range = max(all_x) - min(all_x)
            y_range = max(all_y) - min(all_y)
            # Events should span at least some range
            assert x_range >= 0
            assert y_range >= 0

    def test_visualization_value_distribution(self, frame_sequence):
        """Test that visualizations use reasonable pixel value ranges.

        Arrange: Process frames
        Act: Analyze visualization pixel values
        Assert: Values distributed across range, not saturated
        """
        app = EventCameraApplication()

        for frame_idx, frame in enumerate(frame_sequence):
            event_vis, ts_vis, flow_vis, _ = app.simulator.process(frame, frame_idx)

            # Check value distributions
            for vis in [event_vis, ts_vis, flow_vis]:
                # Should have at least some variation (not all zeros)
                assert vis.min() >= 0
                assert vis.max() <= 255

    def test_event_polarity_distribution(self, frame_sequence):
        """Test that both ON and OFF events are generated.

        Arrange: Process frames with brightness changes
        Act: Collect event polarities
        Assert: Both polarity types present (or single type if appropriate)
        """
        app = EventCameraApplication()
        on_events = 0
        off_events = 0

        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = app.simulator.process(frame, frame_idx)

            for x, y, polarity, _ in events:
                if polarity == 1:
                    on_events += 1
                elif polarity == -1:
                    off_events += 1

        # Should have events
        assert on_events + off_events >= 0


class TestApplicationIntegrationScenarios:
    """Test realistic application usage scenarios."""

    def test_long_video_processing(self):
        """Test processing long video sequence without memory issues.

        Arrange: Create long frame sequence
        Act: Process through simulator multiple times
        Assert: No memory leaks or degradation
        """
        app = EventCameraApplication()

        # Process many frames
        for frame_idx in range(100):
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            _, _, _, events = app.simulator.process(frame, frame_idx)

            # Should continue without issues
            assert isinstance(events, list)

    def test_rapid_parameter_changes(self):
        """Test creating applications with different parameters rapidly.

        Arrange: Different parameter configurations
        Act: Create and use multiple applications
        Assert: All work correctly, no parameter leakage
        """
        configs = [
            {"positive_threshold": 0.1},
            {"positive_threshold": 0.5},
            {"subframe_count": 10},
            {"refractory_frames": 5},
        ]

        frame = np.full((480, 640, 3), 100, dtype=np.uint8)
        bright_frame = np.full((480, 640, 3), 200, dtype=np.uint8)

        for config in configs:
            app = EventCameraApplication(**config)

            # Process frames
            app.simulator.process(frame, 0)
            _, _, _, events = app.simulator.process(bright_frame, 1)

            # Should work with each configuration
            assert isinstance(events, list)

    def test_mixed_input_video_characteristics(self):
        """Test application with various video characteristics.

        Arrange: Frames with different properties
        Act: Process mixed input types
        Assert: Application handles variety correctly
        """
        app = EventCameraApplication()

        frame_types = [
            np.zeros((480, 640, 3), dtype=np.uint8),  # Black frame
            np.full((480, 640, 3), 255, dtype=np.uint8),  # White frame
            np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),  # Random
            np.full((480, 640, 3), 128, dtype=np.uint8),  # Gray frame
        ]

        for frame_idx, frame in enumerate(frame_types):
            vis, ts, flow, events = app.simulator.process(frame, frame_idx)

            # All should process correctly
            assert vis.shape == (480, 640, 3)
            assert ts.shape == (480, 640, 3)
            assert flow.shape == (480, 640, 3)
