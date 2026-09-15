"""Unit tests for frame transformations and conversions.

Tests cover individual transformation methods: log-intensity conversion,
optical flow warping, refractory application, etc.

TDD: These tests define the mathematical properties of each transformation.
"""

import pytest
import numpy as np

from eventcamera import VLAOptimizedDVSSimulator


class TestLogIntensityConversion:
    """Test log-intensity conversion (log-domain modeling of DVS)."""

    def test_conversion_preserves_shape(self, simulator, dummy_grayscale_frame):
        """Verify log conversion maintains frame dimensions.

        Arrange: Grayscale frame (480, 640)
        Act: Convert to log intensity
        Assert: Output shape unchanged
        """
        log_frame = simulator._convert_to_log_intensity(dummy_grayscale_frame)

        assert log_frame.shape == dummy_grayscale_frame.shape

    def test_conversion_produces_float32(self, simulator, dummy_grayscale_frame):
        """Verify log conversion outputs float32 for numerical precision.

        Arrange: Grayscale uint8 frame
        Act: Convert to log intensity
        Assert: Output is float32 (required for logarithm)
        """
        log_frame = simulator._convert_to_log_intensity(dummy_grayscale_frame)

        assert log_frame.dtype == np.float32

    def test_conversion_monotonic_relationship(self, simulator):
        """Verify log conversion preserves intensity ordering.

        Arrange: Frames with increasing pixel values
        Act: Convert to log intensity
        Assert: Log values maintain strict monotonic ordering
        """
        # Dark, medium, bright pixels
        frame = np.array([[0, 128, 255]], dtype=np.uint8)
        log_frame = simulator._convert_to_log_intensity(frame)

        # Darker pixels have more negative log values
        assert log_frame[0, 0] < log_frame[0, 1]
        assert log_frame[0, 1] < log_frame[0, 2]

    def test_conversion_handles_zero_without_nan(self, simulator):
        """Verify log(0) is handled safely (logarithm singularity).

        Arrange: Frame with zero pixels
        Act: Convert to log intensity
        Assert: No NaN or Inf values (epsilon prevents singularity)
        """
        frame = np.zeros((10, 10), dtype=np.uint8)
        log_frame = simulator._convert_to_log_intensity(frame)

        # Epsilon in log prevents NaN
        assert not np.any(np.isnan(log_frame))
        assert not np.any(np.isinf(log_frame))

    def test_conversion_output_range(self, simulator):
        """Verify log intensity is in expected range.

        Arrange: Full dynamic range frame (0-255)
        Act: Convert to log intensity
        Assert: Output range approximately [-13, 0]
        """
        frame = np.array([[1, 128, 255]], dtype=np.uint8)
        log_frame = simulator._convert_to_log_intensity(frame)

        # Log of small values is large negative, large values near 0
        assert np.all(log_frame <= 0)
        assert np.all(log_frame > -20)


class TestReactoryPeriodApplication:
    """Test refractory period suppression logic.

    Refractory period prevents pixel saturation by suppressing
    repeated events at the same location.
    """

    def test_active_pixels_are_suppressed(self, simulator):
        """Verify that pixels in refractory period are suppressed.

        Arrange: Refractory map with some active pixels
        Act: Apply refractory period suppression
        Assert: Active pixels have no events
        """
        simulator.refractory_map = np.array([[0, 1], [0, 0]], dtype=np.int32)
        pos = np.array([[1, 1], [1, 1]], dtype=np.uint8) * 255
        neg = np.array([[1, 1], [1, 1]], dtype=np.uint8) * 255

        pos_sup, neg_sup = simulator._apply_refractory_period(pos, neg)

        # Pixel (0, 1) is active (refractory_map=1), should be suppressed
        assert pos_sup[0, 1] == 0
        assert neg_sup[0, 1] == 0

    def test_inactive_pixels_pass_through(self, simulator):
        """Verify that pixels not in refractory period pass through.

        Arrange: Refractory map with all zeros (no refractory)
        Act: Apply refractory period suppression
        Assert: All events pass through
        """
        simulator.refractory_map = np.zeros((2, 2), dtype=np.int32)
        pos = np.array([[1, 1], [1, 1]], dtype=np.uint8) * 255
        neg = np.array([[1, 1], [1, 1]], dtype=np.uint8) * 255

        pos_sup, neg_sup = simulator._apply_refractory_period(pos, neg)

        # No refractory active, all events pass through
        assert np.all(pos_sup > 0)
        assert np.all(neg_sup > 0)

    def test_mixed_active_and_inactive(self, simulator):
        """Verify selective suppression of only active pixels.

        Arrange: Checkerboard pattern of active/inactive pixels
        Act: Apply refractory period suppression
        Assert: Only active pixels are suppressed
        """
        simulator.refractory_map = np.array([[0, 1, 0], [1, 0, 1]], dtype=np.int32)
        pos = np.ones((2, 3), dtype=np.uint8) * 255

        pos_sup, _ = simulator._apply_refractory_period(pos, pos)

        # Check expected suppression pattern
        assert pos_sup[0, 0] > 0  # Inactive, passes
        assert pos_sup[0, 1] == 0  # Active, suppressed
        assert pos_sup[0, 2] > 0  # Inactive, passes
        assert pos_sup[1, 0] == 0  # Active, suppressed
        assert pos_sup[1, 1] > 0  # Inactive, passes
        assert pos_sup[1, 2] == 0  # Active, suppressed


class TestTimeSurfaceUpdate:
    """Test time surface tracking for event timing."""

    def test_time_surface_updates_with_events(self, simulator):
        """Verify time surface is updated when events fire.

        Arrange: Time surface with initial values
        Act: Update with event masks at specific timestamp
        Assert: Event locations have new timestamp
        """
        simulator.time_surface = np.zeros((2, 2), dtype=np.float32)
        pos = np.array([[1, 0], [0, 0]], dtype=np.uint8) * 255

        simulator._update_refractory_and_time_surface(pos, np.zeros_like(pos), 1.5)

        # Event at (0, 0) should have timestamp 1.5
        assert simulator.time_surface[0, 0] == 1.5
        assert simulator.time_surface[0, 1] == 0.0

    def test_time_surface_not_updated_without_events(self, simulator):
        """Verify time surface only updates at event locations.

        Arrange: Time surface with initial values
        Act: Update with empty event masks
        Assert: Time surface unchanged
        """
        initial_ts = np.ones((2, 2), dtype=np.float32) * 2.0
        simulator.time_surface = initial_ts.copy()

        simulator._update_refractory_and_time_surface(
            np.zeros((2, 2), dtype=np.uint8),
            np.zeros((2, 2), dtype=np.uint8),
            5.0,
        )

        # No events, no changes
        assert np.allclose(simulator.time_surface, initial_ts)
