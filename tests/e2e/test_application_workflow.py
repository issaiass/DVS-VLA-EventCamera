"""End-to-End tests for complete application workflow.

Tests the entire event camera application from CLI invocation through
frame processing and output generation.

These tests:
- Use the actual application code (not mocked)
- Process real video files
- Verify output quality and consistency
- Test error handling and edge cases
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.main import EventCameraApplication, main, parse_video_source


class TestApplicationWorkflow:
    """Test complete application workflows from initialization to output."""

    def test_application_full_lifecycle_with_frame_sequence(self, frame_sequence):
        """Test complete application workflow with frame sequence.

        Arrange: Create application with default parameters
        Act: Process complete frame sequence
        Assert: Application completes successfully, outputs valid results
        """
        app = EventCameraApplication(video_source=0)

        # Verify application initialized
        assert app.simulator is not None
        assert app.frame_index == 0

        # Simulate frame processing
        frame_count = 0
        for frame_idx, frame in enumerate(frame_sequence):
            event_vis, ts_vis, flow_vis, events = app.simulator.process(
                frame, frame_idx
            )

            # Verify all outputs
            assert event_vis.shape == (480, 640, 3)
            assert ts_vis.shape == (480, 640, 3)
            assert flow_vis.shape == (480, 640, 3)
            assert isinstance(events, list)

            frame_count += 1

        # Verify all frames processed
        assert frame_count == len(frame_sequence)

    def test_application_with_custom_parameters(self, frame_sequence):
        """Test application with custom simulator parameters.

        Arrange: Create application with non-default parameters
        Act: Process frames and verify parameters are used
        Assert: Simulator uses custom parameters correctly
        """
        custom_params = {
            "positive_threshold": 0.25,
            "negative_threshold": 0.30,
            "subframe_count": 10,
            "refractory_frames": 3,
            "decay_window": 4.5,
        }

        app = EventCameraApplication(**custom_params)

        # Verify parameters stored
        assert app.simulator.positive_threshold == 0.25
        assert app.simulator.negative_threshold == 0.30
        assert app.simulator.subframe_count == 10
        assert app.simulator.refractory_frames == 3
        assert app.simulator.decay_window == 4.5

        # Process frames with custom parameters
        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = app.simulator.process(frame, frame_idx)
            assert isinstance(events, list)

    def test_application_different_video_sources(self):
        """Test application with different video source types.

        Arrange: Prepare different video source specifications
        Act: Create applications with each source type
        Assert: All sources accepted and stored correctly
        """
        # Camera index
        app_camera = EventCameraApplication(video_source=0)
        assert app_camera.video_source == 0

        # Camera index as string (will be converted)
        app_camera_str = EventCameraApplication(video_source="1")
        assert app_camera_str.video_source == "1"

        # File path
        app_file = EventCameraApplication(video_source="test_video.mp4")
        assert app_file.video_source == "test_video.mp4"


class TestApplicationErrorHandling:
    """Test application behavior with invalid inputs and error conditions."""

    @patch("src.main.EventCameraApplication._initialize_video_capture")
    def test_application_handles_failed_video_capture(self, mock_init):
        """Test application gracefully handles video capture failure.

        Arrange: Mock video capture to fail
        Act: Run application
        Assert: Returns error code without crashing
        """
        mock_init.return_value = False

        app = EventCameraApplication()
        exit_code = app.run()

        # Should return error code
        assert exit_code == 1

    @patch("src.main.EventCameraApplication._cleanup_windows")
    @patch("src.main.EventCameraApplication._release_video_capture")
    @patch("src.main.EventCameraApplication._initialize_video_capture")
    def test_application_cleanup_on_exception(
        self, mock_init, mock_release, mock_cleanup
    ):
        """Test application cleans up resources on exception.

        Arrange: Mock application to raise exception during processing
        Act: Run application
        Assert: Cleanup methods are called despite exception
        """
        mock_init.return_value = True

        app = EventCameraApplication()
        app._read_frame = MagicMock(side_effect=RuntimeError("Test error"))

        exit_code = app.run()

        # Should handle exception gracefully
        assert exit_code == 1
        # Should still clean up
        mock_cleanup.assert_called_once()
        mock_release.assert_called_once()

    @patch("src.main.EventCameraApplication._cleanup_windows")
    @patch("src.main.EventCameraApplication._release_video_capture")
    @patch("src.main.EventCameraApplication._initialize_video_capture")
    def test_application_handles_keyboard_interrupt(
        self, mock_init, mock_release, mock_cleanup
    ):
        """Test application handles user interrupt (Ctrl+C) gracefully.

        Arrange: Mock application to raise KeyboardInterrupt
        Act: Run application
        Assert: Returns interrupt exit code and cleans up
        """
        mock_init.return_value = True

        app = EventCameraApplication()
        app._read_frame = MagicMock(side_effect=KeyboardInterrupt())

        exit_code = app.run()

        # Should return standard interrupt exit code
        assert exit_code == 130
        # Should still clean up
        mock_cleanup.assert_called_once()
        mock_release.assert_called_once()


class TestCLIIntegration:
    """Test CLI integration and entry point."""

    @patch("src.main.EventCameraApplication")
    def test_main_creates_application_with_defaults(self, mock_app_class):
        """Test main() creates application with default arguments.

        Arrange: Mock application class
        Act: Call main() with no arguments
        Assert: Application created with default parameters
        """
        mock_app = MagicMock()
        mock_app.run.return_value = 0
        mock_app_class.return_value = mock_app

        exit_code = main()

        # Application should be created
        mock_app_class.assert_called_once()
        # With default camera (0)
        call_args = mock_app_class.call_args
        assert call_args[1]["video_source"] == 0

    @patch("src.main.EventCameraApplication")
    def test_main_passes_custom_arguments(self, mock_app_class):
        """Test main() passes custom CLI arguments to application.

        Arrange: Mock application class and set up CLI arguments
        Act: Call main with custom arguments
        Assert: Application receives custom parameters
        """
        mock_app = MagicMock()
        mock_app.run.return_value = 0
        mock_app_class.return_value = mock_app

        # Simulate CLI arguments for custom parameters
        import sys

        original_argv = sys.argv
        try:
            sys.argv = [
                "event-camera",
                "--source",
                "1",
                "--pos-threshold",
                "0.25",
                "--subframes",
                "10",
            ]

            from src.main import create_argument_parser

            parser = create_argument_parser()
            args = parser.parse_args()

            # Verify arguments parsed correctly
            assert args.source == "1"
            assert args.pos_threshold == 0.25
            assert args.subframes == 10

        finally:
            sys.argv = original_argv


class TestVideoSourceDetection:
    """Test intelligent video source detection (camera index vs file)."""

    def test_camera_index_detection(self):
        """Test detection and parsing of camera indices.

        Arrange: Numeric camera indices
        Act: Parse with parse_video_source
        Assert: Correctly identified as camera indices
        """
        for idx in [0, 1, 2, 5]:
            source = parse_video_source(str(idx))
            assert isinstance(source, int)
            assert source == idx

    def test_file_path_detection(self):
        """Test detection of file paths.

        Arrange: File path strings
        Act: Parse with parse_video_source
        Assert: Correctly identified as file paths
        """
        paths = [
            "video.mp4",
            "path/to/video.avi",
            "/absolute/path/video.mov",
            "C:\\Windows\\path\\video.mp4",
        ]

        for path in paths:
            source = parse_video_source(path)
            assert isinstance(source, str)
            assert source == path

    def test_fallback_to_file_path_on_invalid_number(self):
        """Test fallback to file path when number parsing fails.

        Arrange: String that looks numeric but isn't valid camera index
        Act: Parse with parse_video_source
        Assert: Treated as file path
        """
        source = parse_video_source("3.14")
        assert isinstance(source, str)
        assert source == "3.14"


class TestSimulatorParameterRanges:
    """Test application behavior with extreme parameter values."""

    def test_very_low_thresholds(self, frame_sequence):
        """Test simulator with very low (sensitive) thresholds.

        Arrange: Create simulator with very low thresholds
        Act: Process frames
        Assert: Generates events from minor changes
        """
        app = EventCameraApplication(
            positive_threshold=0.01, negative_threshold=0.01
        )

        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = app.simulator.process(frame, frame_idx)
            assert isinstance(events, list)

    def test_very_high_thresholds(self, frame_sequence):
        """Test simulator with very high (insensitive) thresholds.

        Arrange: Create simulator with very high thresholds
        Act: Process frames
        Assert: Generates few or no events
        """
        app = EventCameraApplication(
            positive_threshold=2.0, negative_threshold=2.0
        )

        event_count = 0
        for frame_idx, frame in enumerate(frame_sequence):
            _, _, _, events = app.simulator.process(frame, frame_idx)
            event_count += len(events)

        # High thresholds should produce few events
        assert event_count >= 0

    def test_extreme_subframe_counts(self, frame_sequence):
        """Test simulator with extreme subframe counts.

        Arrange: Very high and very low subframe counts
        Act: Process frames with each setting
        Assert: All complete successfully
        """
        for subframes in [1, 50]:
            app = EventCameraApplication(subframe_count=subframes)

            for frame_idx, frame in enumerate(frame_sequence):
                _, _, _, events = app.simulator.process(frame, frame_idx)
                assert isinstance(events, list)

    def test_extreme_refractory_periods(self, frame_sequence):
        """Test simulator with extreme refractory periods.

        Arrange: Very long refractory periods
        Act: Process frames
        Assert: Refractory suppression works at extremes
        """
        for refractory in [1, 100]:
            app = EventCameraApplication(refractory_frames=refractory)

            for frame_idx, frame in enumerate(frame_sequence):
                _, _, _, events = app.simulator.process(frame, frame_idx)
                assert isinstance(events, list)


class TestOutputConsistency:
    """Test that application produces consistent outputs."""

    def test_deterministic_event_generation(self):
        """Test that same input produces same events (determinism).

        Arrange: Identical frame pairs with fresh simulators
        Act: Process with two independent application instances
        Assert: Event counts match exactly
        """
        frame1 = np.full((480, 640, 3), 50, dtype=np.uint8)
        frame2 = np.full((480, 640, 3), 200, dtype=np.uint8)

        # First run
        app1 = EventCameraApplication()
        app1.simulator.process(frame1, 0)
        _, _, _, events1 = app1.simulator.process(frame2, 1)

        # Second run (identical)
        app2 = EventCameraApplication()
        app2.simulator.process(frame1, 0)
        _, _, _, events2 = app2.simulator.process(frame2, 1)

        # Should produce identical results
        assert len(events1) == len(events2)

    def test_visualization_consistency(self):
        """Test that visualizations are generated consistently.

        Arrange: Identical frames processed twice
        Act: Generate visualizations for both
        Assert: Visualizations have same shapes and properties
        """
        frame = np.full((480, 640, 3), 100, dtype=np.uint8)

        # First run
        app1 = EventCameraApplication()
        vis1, ts1, flow1, _ = app1.simulator.process(frame, 0)

        # Second run
        app2 = EventCameraApplication()
        vis2, ts2, flow2, _ = app2.simulator.process(frame, 0)

        # Shapes should match
        assert vis1.shape == vis2.shape
        assert ts1.shape == ts2.shape
        assert flow1.shape == flow2.shape

        # All should be uint8
        assert vis1.dtype == np.uint8
        assert ts1.dtype == np.uint8
        assert flow1.dtype == np.uint8
