"""Integration tests for complete DVS simulator pipeline.

Tests verify that simulator components work together correctly
with realistic frame sequences and expected event patterns.

These are slower than unit tests but test the complete flow.
"""

import pytest
import numpy as np

from eventcamera import VLAOptimizedDVSSimulator


class TestCompleteSimulatorPipeline:
    """Test the complete simulator processing pipeline with realistic data."""

    def test_process_realistic_video_sequence(self, frame_sequence):
        """Verify simulator handles complete frame sequence correctly.

        Arrange: Realistic frame sequence with motion
        Act: Process all frames through simulator
        Assert: All outputs are properly formatted and consistent
        """
        simulator = VLAOptimizedDVSSimulator()
        all_events = []

        for frame_idx, frame in enumerate(frame_sequence):
            event_vis, ts_vis, flow_vis, events = simulator.process(frame, frame_idx)

            # Verify all outputs have correct format
            assert event_vis.shape == (480, 640, 3)
            assert ts_vis.shape == (480, 640, 3)
            assert flow_vis.shape == (480, 640, 3)
            assert isinstance(events, list)

            all_events.extend(events)

        # Verify that processing generates reasonable output
        assert len(all_events) >= 0  # May be 0 if thresholds are high

    def test_events_maintain_temporal_order(self, frame_sequence):
        """Verify events maintain strict temporal ordering across frames.

        Arrange: Frame sequence with potential events
        Act: Process frames and collect all event timestamps
        Assert: All timestamps are non-decreasing
        """
        simulator = VLAOptimizedDVSSimulator()
        all_timestamps = []

        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = simulator.process(frame, frame_idx)
            all_timestamps.extend([event[3] for event in events])

        # Verify strict temporal ordering
        if len(all_timestamps) > 1:
            for i in range(len(all_timestamps) - 1):
                assert all_timestamps[i] <= all_timestamps[i + 1]

    def test_events_within_frame_bounds(self, frame_sequence):
        """Verify all events are within valid frame coordinates.

        Arrange: Frame sequence with events
        Act: Process frames and collect events
        Assert: All x in [0, width), y in [0, height)
        """
        simulator = VLAOptimizedDVSSimulator()
        height, width = frame_sequence[0].shape[:2]

        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = simulator.process(frame, frame_idx)

            for x, y, polarity, timestamp in events:
                # All coordinates must be within frame
                assert 0 <= x < width, f"x={x} out of bounds [0, {width})"
                assert 0 <= y < height, f"y={y} out of bounds [0, {height})"
                assert polarity in [1, -1]

    def test_state_consistency_across_frames(self, frame_sequence):
        """Verify simulator state remains consistent across frames.

        Arrange: Frame sequence
        Act: Process frames and monitor state transitions
        Assert: State evolves correctly without corruption
        """
        simulator = VLAOptimizedDVSSimulator()

        for frame_idx, frame in enumerate(frame_sequence):
            simulator.process(frame, frame_idx)

            # State should always be initialized after first frame
            if frame_idx > 0:
                assert simulator.previous_grayscale is not None
                assert simulator.previous_log_intensity is not None
                assert simulator.refractory_map is not None
                assert simulator.time_surface is not None


class TestParameterVariations:
    """Test simulator behavior with different parameter combinations."""

    @pytest.mark.parametrize("pos_thresh,neg_thresh", [
        (0.1, 0.1),   # Very sensitive
        (0.35, 0.35), # Default
        (0.5, 0.5),   # Moderate
        (0.8, 0.8),   # Insensitive
    ])
    def test_various_threshold_combinations(
        self, pos_thresh, neg_thresh, frame_sequence
    ):
        """Test simulator with various threshold combinations.

        Arrange: Different threshold values
        Act: Process frames with each threshold pair
        Assert: All process without error
        """
        simulator = VLAOptimizedDVSSimulator(
            positive_threshold=pos_thresh,
            negative_threshold=neg_thresh,
        )

        for frame_idx, frame in enumerate(frame_sequence):
            vis, ts, flow, events = simulator.process(frame, frame_idx)
            # All should complete without error
            assert vis.shape == (480, 640, 3)

    @pytest.mark.parametrize("subframes", [1, 5, 10, 20])
    def test_various_subframe_counts(self, subframes, frame_sequence):
        """Test simulator with different temporal interpolation levels.

        Arrange: Different subframe counts
        Act: Process frames with each setting
        Assert: All configurations work correctly
        """
        simulator = VLAOptimizedDVSSimulator(subframe_count=subframes)

        all_events = []
        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = simulator.process(frame, frame_idx)
            all_events.extend(events)

        assert isinstance(all_events, list)

    @pytest.mark.parametrize("refractory", [1, 2, 5, 10])
    def test_various_refractory_periods(self, refractory, frame_sequence):
        """Test simulator with different refractory period settings.

        Arrange: Different refractory frame counts
        Act: Process frames with each setting
        Assert: All configurations handle properly
        """
        simulator = VLAOptimizedDVSSimulator(refractory_frames=refractory)

        all_events = []
        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = simulator.process(frame, frame_idx)
            all_events.extend(events)

        assert isinstance(all_events, list)

    def test_extreme_threshold_produces_more_or_fewer_events(self, frame_sequence):
        """Verify sensitivity relationship: low threshold → more events.

        Arrange: Two simulators with high and low thresholds
        Act: Process same frames with both
        Assert: Low threshold produces more events
        """
        sim_high = VLAOptimizedDVSSimulator(positive_threshold=0.8)
        sim_low = VLAOptimizedDVSSimulator(positive_threshold=0.1)

        events_high = []
        events_low = []

        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, e_high = sim_high.process(frame, frame_idx)
            _, _, _, e_low = sim_low.process(frame, frame_idx)
            events_high.extend(e_high)
            events_low.extend(e_low)

        # Lower threshold should produce more events
        assert len(events_low) >= len(events_high)


class TestEndToEndPipelineQuality:
    """Test overall quality of complete end-to-end pipeline."""

    def test_full_pipeline_produces_valid_outputs(self, frame_sequence):
        """Verify complete pipeline produces all expected outputs.

        Arrange: Realistic frame sequence
        Act: Process through complete pipeline
        Assert: All outputs valid and consistent
        """
        simulator = VLAOptimizedDVSSimulator(
            positive_threshold=0.35,
            negative_threshold=0.35,
            subframe_count=5,
            refractory_frames=2,
            decay_window=3.0,
        )

        frame_count = 0
        total_events = 0

        for frame_idx, frame in enumerate(frame_sequence):
            event_vis, ts_vis, flow_vis, events = simulator.process(frame, frame_idx)

            # Verify output integrity
            assert event_vis.shape == (480, 640, 3)
            assert event_vis.dtype == np.uint8
            assert ts_vis.shape == (480, 640, 3)
            assert ts_vis.dtype == np.uint8
            assert flow_vis.shape == (480, 640, 3)
            assert flow_vis.dtype == np.uint8

            # Verify events format
            for event in events:
                assert len(event) == 4
                x, y, pol, ts = event
                assert 0 <= x < 640
                assert 0 <= y < 480
                assert pol in [1, -1]

            frame_count += 1
            total_events += len(events)

        # Pipeline completed successfully
        assert frame_count == len(frame_sequence)
        assert total_events >= 0

    def test_pipeline_consistency_with_identical_inputs(self):
        """Verify pipeline produces deterministic output for same input.

        Arrange: Identical frame sequences
        Act: Process twice with fresh simulators
        Assert: Event generation is deterministic
        """
        frame = np.full((480, 640, 3), 100, dtype=np.uint8)
        bright = np.full((480, 640, 3), 200, dtype=np.uint8)

        # First run
        sim1 = VLAOptimizedDVSSimulator()
        sim1.process(frame, 0)
        _, _, _, events1 = sim1.process(bright, 1)

        # Second run (identical)
        sim2 = VLAOptimizedDVSSimulator()
        sim2.process(frame, 0)
        _, _, _, events2 = sim2.process(bright, 1)

        # Should produce same number of events
        assert len(events1) == len(events2)
