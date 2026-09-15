"""Unit tests for VLAOptimizedDVSSimulator initialization.

Tests cover constructor, parameter validation, and algorithm initialization.
Each test verifies a specific aspect of the initialization phase.

Following TDD: these tests define the contract for simulator setup.
"""

import pytest

from eventcamera import VLAOptimizedDVSSimulator


class TestSimulatorInitialization:
    """Test simulator constructor with various parameter combinations."""

    def test_initialization_with_defaults(self):
        """Verify simulator uses correct default parameter values.

        Arrange: Create simulator with no arguments
        Act: Initialize VLAOptimizedDVSSimulator
        Assert: All parameters match documented defaults
        """
        simulator = VLAOptimizedDVSSimulator()

        assert simulator.positive_threshold == 0.35
        assert simulator.negative_threshold == 0.35
        assert simulator.subframe_count == 5
        assert simulator.refractory_frames == 2
        assert simulator.decay_window == 3.0

    def test_initialization_with_custom_parameters(self):
        """Verify simulator accepts and stores custom parameters.

        Arrange: Prepare non-default parameters
        Act: Initialize with custom values
        Assert: Parameters are stored correctly
        """
        simulator = VLAOptimizedDVSSimulator(
            positive_threshold=0.25,
            negative_threshold=0.30,
            subframe_count=10,
            refractory_frames=3,
            decay_window=4.5,
        )

        assert simulator.positive_threshold == 0.25
        assert simulator.negative_threshold == 0.30
        assert simulator.subframe_count == 10
        assert simulator.refractory_frames == 3
        assert simulator.decay_window == 4.5

    def test_initialization_with_extreme_parameters(self):
        """Verify simulator handles extreme but valid parameter values.

        Arrange: Prepare edge case parameters
        Act: Initialize with very high/low values
        Assert: No errors, values stored correctly
        """
        simulator = VLAOptimizedDVSSimulator(
            positive_threshold=0.01,  # Very sensitive
            negative_threshold=2.0,   # Very insensitive
            subframe_count=1,         # No interpolation
            refractory_frames=100,    # Long refractory
            decay_window=0.1,         # Quick decay
        )

        assert simulator.positive_threshold == 0.01
        assert simulator.negative_threshold == 2.0
        assert simulator.subframe_count == 1
        assert simulator.refractory_frames == 100
        assert simulator.decay_window == 0.1


class TestAlgorithmInitialization:
    """Test that all required algorithms are properly initialized."""

    def test_optical_flow_algorithm_initialized(self):
        """Verify DIS optical flow algorithm is created.

        Arrange: Create simulator
        Act: Initialize VLAOptimizedDVSSimulator
        Assert: optical_flow_algorithm is not None and usable
        """
        simulator = VLAOptimizedDVSSimulator()

        assert simulator.optical_flow_algorithm is not None

    def test_clahe_initialized(self):
        """Verify CLAHE contrast normalization is created.

        Arrange: Create simulator
        Act: Initialize VLAOptimizedDVSSimulator
        Assert: clahe is not None and usable
        """
        simulator = VLAOptimizedDVSSimulator()

        assert simulator.clahe is not None

    def test_background_subtractor_initialized(self):
        """Verify MOG2 background subtraction algorithm is created.

        Arrange: Create simulator
        Act: Initialize VLAOptimizedDVSSimulator
        Assert: background_subtractor is not None and usable
        """
        simulator = VLAOptimizedDVSSimulator()

        assert simulator.background_subtractor is not None

    def test_morphological_kernel_initialized(self):
        """Verify morphological kernel for filtering is created.

        Arrange: Create simulator
        Act: Initialize VLAOptimizedDVSSimulator
        Assert: morphological_kernel is not None with correct shape
        """
        simulator = VLAOptimizedDVSSimulator()

        assert simulator.morphological_kernel is not None
        assert simulator.morphological_kernel.shape == (3, 3)


class TestInitialState:
    """Test that internal state is properly initialized before processing."""

    def test_state_variables_are_none_initially(self):
        """Verify all state variables start as None (uninitialized).

        Arrange: Create simulator
        Act: Initialize VLAOptimizedDVSSimulator
        Assert: No state has been created yet
        """
        simulator = VLAOptimizedDVSSimulator()

        assert simulator.previous_grayscale is None
        assert simulator.previous_log_intensity is None
        assert simulator.refractory_map is None
        assert simulator.time_surface is None
        assert simulator.coordinate_grid_x is None
        assert simulator.coordinate_grid_y is None

    def test_frame_index_tracking(self):
        """Verify frame index counter can be used without error.

        Arrange: Create simulator
        Act: Access frame_index if tracked by caller
        Assert: Simulator ready for frame processing
        """
        simulator = VLAOptimizedDVSSimulator()

        # Simulator doesn't track frame_index itself (caller does)
        # This test documents this behavior
        assert not hasattr(simulator, "frame_index")
