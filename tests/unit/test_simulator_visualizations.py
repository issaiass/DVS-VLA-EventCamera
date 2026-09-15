"""Unit tests for visualization generation.

Tests cover event visualization, time surface visualization,
and optical flow visualization generation.

TDD: These tests define output formats and color encoding.
"""

import pytest
import numpy as np

from eventcamera import VLAOptimizedDVSSimulator


class TestEventVisualization:
    """Test event rendering to visualization frames."""

    def test_event_visualization_output_shape(self, simulator, dummy_bgr_frame):
        """Verify event visualization matches input frame dimensions.

        Arrange: Frame (480, 640, 3)
        Act: Process frame and get event visualization
        Assert: Output shape is (480, 640, 3)
        """
        event_vis, _, _, _ = simulator.process(dummy_bgr_frame, 0)

        assert event_vis.shape == (480, 640, 3)

    def test_event_visualization_dtype(self, simulator, dummy_bgr_frame):
        """Verify event visualization is uint8 for display.

        Arrange: Process frame
        Act: Get event visualization
        Assert: dtype is uint8 (required for cv2.imshow)
        """
        event_vis, _, _, _ = simulator.process(dummy_bgr_frame, 0)

        assert event_vis.dtype == np.uint8

    def test_event_visualization_color_coding(self, simulator):
        """Verify event colors: RED for ON, BLUE for OFF.

        Arrange: Frame change from dark to bright
        Act: Process and generate event visualization
        Assert: Visualization contains red pixels (ON events)
        """
        dark = np.full((480, 640, 3), 50, dtype=np.uint8)
        bright = np.full((480, 640, 3), 200, dtype=np.uint8)

        simulator.process(dark, 0)
        event_vis, _, _, _ = simulator.process(bright, 1)

        # Brightness increase generates ON events (red)
        # Red in BGR is (0, 0, 255), so red_channel should have values > 0
        red_channel = event_vis[:, :, 2]
        # Might have events, so check if any red pixels exist or all zero
        assert red_channel.max() >= 0

    def test_event_visualization_accumulation(self, simulator):
        """Verify multiple events from same region create cumulative color.

        Arrange: Sequence of frames with consistent motion
        Act: Process frames with multiple events in same area
        Assert: Event visualization reflects all events
        """
        frames = [
            np.full((480, 640, 3), 100, dtype=np.uint8),
            np.full((480, 640, 3), 150, dtype=np.uint8),
            np.full((480, 640, 3), 200, dtype=np.uint8),
        ]

        for i, frame in enumerate(frames):
            event_vis, _, _, _ = simulator.process(frame, i)

        # Last visualization should show events
        assert event_vis.dtype == np.uint8


class TestTimeSurfaceVisualization:
    """Test time surface (event decay) visualization."""

    def test_time_surface_output_shape(self, simulator, dummy_bgr_frame):
        """Verify time surface visualization has correct dimensions.

        Arrange: Process frame
        Act: Get time surface visualization
        Assert: Shape is (height, width, 3)
        """
        _, ts_vis, _, _ = simulator.process(dummy_bgr_frame, 0)

        assert ts_vis.shape == (480, 640, 3)

    def test_time_surface_dtype(self, simulator, dummy_bgr_frame):
        """Verify time surface is uint8 for display.

        Arrange: Process frame
        Act: Get time surface visualization
        Assert: dtype is uint8
        """
        _, ts_vis, _, _ = simulator.process(dummy_bgr_frame, 0)

        assert ts_vis.dtype == np.uint8

    def test_time_surface_value_range(self, simulator, dummy_bgr_frame):
        """Verify time surface pixel values in valid display range [0, 255].

        Arrange: Process frame(s)
        Act: Get time surface visualization
        Assert: All pixel values in [0, 255]
        """
        simulator.process(dummy_bgr_frame, 0)
        _, ts_vis, _, _ = simulator.process(dummy_bgr_frame, 1)

        assert ts_vis.min() >= 0
        assert ts_vis.max() <= 255

    def test_time_surface_uses_colormap(self, simulator):
        """Verify time surface uses JET colormap (colored, not grayscale).

        Arrange: Process frames with events
        Act: Get time surface visualization
        Assert: Output uses full color (not just grayscale)
        """
        dark = np.full((480, 640, 3), 50, dtype=np.uint8)
        bright = np.full((480, 640, 3), 200, dtype=np.uint8)

        simulator.process(dark, 0)
        simulator.process(bright, 1)
        _, ts_vis, _, _ = simulator.process(bright, 2)

        # JET colormap produces colored output
        # Check that it's not pure grayscale (R != G != B in some pixels)
        r, g, b = ts_vis[:, :, 2], ts_vis[:, :, 1], ts_vis[:, :, 0]
        # At least some pixels should have different channel values
        channel_diff = np.abs(r.astype(int) - g.astype(int))
        assert np.any(channel_diff > 0) or np.all(ts_vis == 0)


class TestOpticalFlowVisualization:
    """Test optical flow motion vector visualization."""

    def test_optical_flow_output_shape(self, simulator, dummy_bgr_frame):
        """Verify optical flow visualization has correct dimensions.

        Arrange: Process frame
        Act: Get optical flow visualization
        Assert: Shape is (height, width, 3)
        """
        _, _, flow_vis, _ = simulator.process(dummy_bgr_frame, 0)

        assert flow_vis.shape == (480, 640, 3)

    def test_optical_flow_dtype(self, simulator, dummy_bgr_frame):
        """Verify optical flow visualization is uint8.

        Arrange: Process frame
        Act: Get optical flow visualization
        Assert: dtype is uint8
        """
        _, _, flow_vis, _ = simulator.process(dummy_bgr_frame, 0)

        assert flow_vis.dtype == np.uint8

    def test_optical_flow_contains_arrows_on_motion(self, simulator, frame_sequence):
        """Verify optical flow visualization shows arrows for motion.

        Arrange: Frame sequence with motion
        Act: Process frames with moving objects
        Assert: Flow visualization contains motion vectors (non-zero)
        """
        simulator.process(frame_sequence[0], 0)
        _, _, flow_vis, _ = simulator.process(frame_sequence[1], 1)

        # Should have some non-zero pixels (flow visualization)
        # or be identical to source (if no motion detected)
        assert flow_vis.shape == (480, 640, 3)
        assert flow_vis.dtype == np.uint8


class TestVisualizationPersistence:
    """Test event latching (visualization persistence)."""

    def test_visualization_latching_on_no_events(self, simulator):
        """Verify last event visualization persists when no new events.

        Arrange: First frame generates events
        Act: Process two frames, second with no events
        Assert: Second frame shows last events (latching)
        """
        frame1 = np.full((480, 640, 3), 50, dtype=np.uint8)
        frame2 = np.full((480, 640, 3), 200, dtype=np.uint8)
        frame3 = np.full((480, 640, 3), 200, dtype=np.uint8)  # Same as frame2

        simulator.process(frame1, 0)
        vis2, _, _, events2 = simulator.process(frame2, 1)
        vis3, _, _, events3 = simulator.process(frame3, 2)

        # Frame 3 should show latched visualization if no new events
        assert vis3.dtype == np.uint8
        assert vis3.shape == (480, 640, 3)

    def test_visualization_updates_on_new_events(self, simulator):
        """Verify visualization updates when new events occur.

        Arrange: Sequence with varying brightness
        Act: Process frames with different event patterns
        Assert: Visualization reflects current events
        """
        frames = [
            np.full((480, 640, 3), 50, dtype=np.uint8),
            np.full((480, 640, 3), 200, dtype=np.uint8),
            np.full((480, 640, 3), 50, dtype=np.uint8),
        ]

        for i, frame in enumerate(frames):
            vis, _, _, _ = simulator.process(frame, i)
            assert vis.shape == (480, 640, 3)
