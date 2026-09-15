"""Event camera simulator command-line interface for robotics applications.

This module provides a command-line interface to simulate event camera output
from video frames, with options for configuring algorithm parameters.
"""

import argparse
import sys
from typing import Optional

import cv2

from eventcamera import VLAOptimizedDVSSimulator


class EventCameraApplication:
    """Main application for event camera simulation.

    Manages video input, event camera simulation, and visualization output.
    Follows Uncle Bob Martin's Clean Code principles with single responsibility
    for each method.

    Architecture:
    - Separates concerns: video I/O, simulation, visualization, cleanup
    - Each method does one thing: initialize, read, process, display, or cleanup
    - Robust resource management: try/finally ensures cleanup even on exceptions
    - Clear error codes: enables scripting and CI/CD integration

    Parameters
    ----------
    video_source : str or int
        Video file path or camera device index (0 for default camera).
    positive_threshold : float
        Threshold for ON event generation.
    negative_threshold : float
        Threshold for OFF event generation.
    subframe_count : int
        Number of interpolation subframes.
    refractory_frames : int
        Refractory period in frames.
    decay_window : float
        Event decay time window.

    Examples
    --------
    >>> app = EventCameraApplication(
    ...     video_source=0,
    ...     positive_threshold=0.35,
    ...     negative_threshold=0.35
    ... )
    >>> app.run()
    """

    # Window configuration constants - avoid magic strings in code
    _WINDOW_NAME_SOURCE = "Source Frame"
    _WINDOW_NAME_EVENTS = "Simulated Events (Warping + MOG2 + Latch)"
    _WINDOW_NAME_TIME_SURFACE = "Time Surface (Decay)"
    _WINDOW_NAME_OPTICAL_FLOW = "Optical Flow (Quiver)"
    _QUIT_KEY = ord("q")
    _KEY_WAIT_TIME_MS = 1  # Non-blocking: allows responsive quit handling

    def __init__(
        self,
        video_source: str | int = 0,
        positive_threshold: float = 0.35,
        negative_threshold: float = 0.35,
        subframe_count: int = 5,
        refractory_frames: int = 2,
        decay_window: float = 3.0,
    ) -> None:
        """Initialize the event camera application.

        Parameters
        ----------
        video_source : str or int, optional
            Video file path or camera device index. Default is 0 (default camera).
        positive_threshold : float, optional
            Threshold for ON events. Default is 0.35.
        negative_threshold : float, optional
            Threshold for OFF events. Default is 0.35.
        subframe_count : int, optional
            Number of subframes. Default is 5.
        refractory_frames : int, optional
            Refractory period. Default is 2.
        decay_window : float, optional
            Decay time window. Default is 3.0.
        """
        self.video_source = video_source
        self.simulator = VLAOptimizedDVSSimulator(
            positive_threshold=positive_threshold,
            negative_threshold=negative_threshold,
            subframe_count=subframe_count,
            refractory_frames=refractory_frames,
            decay_window=decay_window,
        )
        self.video_capture = None
        self.frame_index = 0

    def _initialize_video_capture(self) -> bool:
        """Initialize video capture from source.

        Attempts to open the configured video source. If the source is a string,
        it's treated as a file path. If numeric, it's treated as a camera index.

        Returns
        -------
        bool
            True if video source opened successfully, False otherwise.

        Examples
        --------
        >>> app = EventCameraApplication(video_source=0)
        >>> success = app._initialize_video_capture()
        >>> isinstance(success, bool)
        True
        """
        try:
            if isinstance(self.video_source, str):
                self.video_capture = cv2.VideoCapture(self.video_source)
            else:
                self.video_capture = cv2.VideoCapture(int(self.video_source))

            if not self.video_capture.isOpened():
                return False

            return True
        except (ValueError, TypeError) as error:
            print(f"Error initializing video capture: {error}")
            return False

    def _read_frame(self) -> tuple[bool, Optional[cv2.typing.MatLike]]:
        """Read next frame from video source.

        Returns
        -------
        tuple[bool, Optional[cv2.typing.MatLike]]
            Tuple of (success, frame) where success is True if frame
            was read successfully, False otherwise. Frame is None if
            reading failed.

        Examples
        --------
        >>> app = EventCameraApplication(video_source=0)
        >>> if app._initialize_video_capture():
        ...     success, frame = app._read_frame()
        ...     if success:
        ...         print(f"Frame shape: {frame.shape}")
        """
        if self.video_capture is None:
            return False, None

        try:
            success, frame = self.video_capture.read()
            return success, frame if success else None
        except Exception as error:
            print(f"Error reading frame: {error}")
            return False, None

    def _display_visualizations(
        self,
        source_frame: cv2.typing.MatLike,
        event_visualization: cv2.typing.MatLike,
        time_surface_visualization: cv2.typing.MatLike,
        optical_flow_visualization: cv2.typing.MatLike,
    ) -> bool:
        """Display all output visualizations in separate windows.

        Parameters
        ----------
        source_frame : cv2.typing.MatLike
            Original input frame.
        event_visualization : cv2.typing.MatLike
            Event detection visualization.
        time_surface_visualization : cv2.typing.MatLike
            Time surface decay visualization.
        optical_flow_visualization : cv2.typing.MatLike
            Optical flow motion vectors visualization.

        Returns
        -------
        bool
            True if user requested quit (pressed 'q'), False otherwise.

        Examples
        --------
        >>> import numpy as np
        >>> app = EventCameraApplication()
        >>> dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        >>> # Note: display returns bool indicating quit request
        >>> quit_requested = app._display_visualizations(
        ...     dummy_frame, dummy_frame, dummy_frame, dummy_frame
        ... )
        """
        cv2.imshow(self._WINDOW_NAME_SOURCE, source_frame)
        cv2.imshow(self._WINDOW_NAME_EVENTS, event_visualization)
        cv2.imshow(self._WINDOW_NAME_TIME_SURFACE, time_surface_visualization)
        cv2.imshow(self._WINDOW_NAME_OPTICAL_FLOW, optical_flow_visualization)

        key_pressed = cv2.waitKey(self._KEY_WAIT_TIME_MS)
        return key_pressed == self._QUIT_KEY

    def _cleanup_windows(self) -> None:
        """Destroy all OpenCV display windows.

        Returns
        -------
        None

        Examples
        --------
        >>> app = EventCameraApplication()
        >>> app._cleanup_windows()  # Safe to call even if no windows exist
        """
        cv2.destroyAllWindows()

    def _release_video_capture(self) -> None:
        """Release video capture resource.

        Returns
        -------
        None

        Examples
        --------
        >>> app = EventCameraApplication(video_source=0)
        >>> app.video_capture = cv2.VideoCapture(0)
        >>> app._release_video_capture()
        """
        if self.video_capture is not None:
            self.video_capture.release()

    def run(self) -> int:
        """Run the event camera simulation main loop.

        Processes frames from video source, generates events, and displays results.
        Main loop continues until end of video or user presses 'q'.

        Design: try/finally pattern ensures resources are cleaned up regardless
        of how the loop exits (normal completion, EOF, exception, user interrupt).
        This prevents resource leaks and zombie processes.

        Returns
        -------
        int
            Exit code: 0 for successful completion, non-zero for errors.
            Exit codes follow Unix conventions for scripting compatibility.

        Examples
        --------
        >>> app = EventCameraApplication(video_source=0)
        >>> exit_code = app.run()
        >>> print(f"Application exited with code: {exit_code}")
        """
        # Early exit if video source cannot be opened
        if not self._initialize_video_capture():
            print("Error: Failed to initialize video capture.")
            return 1

        try:
            # Main processing loop: read → simulate → display → check quit
            while True:
                success, frame = self._read_frame()
                if not success:
                    # EOF or read error: normal termination
                    break

                # Run DVS simulation on frame to generate events
                (
                    event_visualization,
                    time_surface_visualization,
                    optical_flow_visualization,
                    events,
                ) = self.simulator.process(frame, self.frame_index)

                # Display all visualizations and check for user quit request
                quit_requested = self._display_visualizations(
                    frame,
                    event_visualization,
                    time_surface_visualization,
                    optical_flow_visualization,
                )

                if quit_requested:
                    # User pressed 'q': graceful shutdown
                    break

                self.frame_index += 1

            return 0

        except KeyboardInterrupt:
            # User pressed Ctrl+C: standard signal handling
            print("\nApplication interrupted by user.")
            return 130  # SIGINT exit code

        except Exception as error:
            # Unhandled exception: log and propagate error
            print(f"Unexpected error during execution: {error}")
            return 1

        finally:
            # Resource cleanup: always executes regardless of exit path
            # Prevents orphaned windows and unclosed file handles
            self._cleanup_windows()
            self._release_video_capture()


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure command-line argument parser.

    Separated into its own function following Clean Code principle:
    each function should have a single responsibility.
    This simplifies testing, reuse, and documentation.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser for event camera simulation.
        Exposes all simulator parameters as CLI flags with sensible defaults.

    Examples
    --------
    >>> parser = create_argument_parser()
    >>> args = parser.parse_args([])
    >>> isinstance(args.video_source, int)
    True
    """
    parser = argparse.ArgumentParser(
        prog="event-camera",
        description="VLA-Optimized DVS Simulator for Robotics Applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default webcam
  python main.py

  # Use specific camera device
  python main.py --source 1

  # Process video file
  python main.py --source path/to/video.mp4

  # Adjust event thresholds
  python main.py --pos-threshold 0.25 --neg-threshold 0.25

  # Fine-tune temporal resolution
  python main.py --subframes 10 --refractory 3
        """,
    )

    parser.add_argument(
        "--source",
        type=str,
        default="0",
        help="Video source (camera index or file path). Default: 0 (default camera)",
        metavar="SOURCE",
    )

    parser.add_argument(
        "--pos-threshold",
        type=float,
        default=0.35,
        help="Positive (ON) event threshold. Default: 0.35",
        metavar="THRESHOLD",
    )

    parser.add_argument(
        "--neg-threshold",
        type=float,
        default=0.35,
        help="Negative (OFF) event threshold. Default: 0.35",
        metavar="THRESHOLD",
    )

    parser.add_argument(
        "--subframes",
        type=int,
        default=5,
        help="Number of interpolation subframes between frames. Default: 5",
        metavar="COUNT",
    )

    parser.add_argument(
        "--refractory",
        type=int,
        default=2,
        help="Refractory period in frames. Default: 2",
        metavar="FRAMES",
    )

    parser.add_argument(
        "--decay",
        type=float,
        default=3.0,
        help="Time surface decay window in frames. Default: 3.0",
        metavar="WINDOW",
    )

    return parser


def parse_video_source(source_string: str) -> int | str:
    """Parse video source argument into appropriate type.

    Implements intelligent type detection: tries numeric first (camera index),
    falls back to string (file path). This pattern is more user-friendly than
    requiring explicit type flags like --type camera vs --type file.

    Parameters
    ----------
    source_string : str
        Video source string (camera index or file path).

    Returns
    -------
    int | str
        Camera device index if numeric string, file path otherwise.

    Examples
    --------
    >>> parse_video_source("0")
    0
    >>> parse_video_source("video.mp4")
    'video.mp4'
    >>> parse_video_source("2")
    2
    """
    try:
        # Try numeric: most common case (camera indices 0, 1, 2, ...)
        return int(source_string)
    except ValueError:
        # Fall back to file path: handles all string-based sources
        return source_string


def main() -> int:
    """Main entry point for event camera simulator.

    Orchestrates the command-line workflow:
    1. Parse arguments from user input
    2. Convert argument types appropriately
    3. Create application with parsed configuration
    4. Run application and return exit code

    This top-level function is intentionally thin and linear,
    making it easy to understand the overall flow at a glance.

    Returns
    -------
    int
        Exit code: 0 for success, non-zero for errors.
        Enables shell scripting and CI/CD integration.

    Examples
    --------
    >>> exit_code = main()
    >>> print(f"Exit code: {exit_code}")
    """
    # Step 1: Create and parse CLI arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Step 2: Convert video source to appropriate type (int for camera, str for file)
    video_source = parse_video_source(args.source)

    # Step 3: Instantiate application with user-provided configuration
    app = EventCameraApplication(
        video_source=video_source,
        positive_threshold=args.pos_threshold,
        negative_threshold=args.neg_threshold,
        subframe_count=args.subframes,
        refractory_frames=args.refractory,
        decay_window=args.decay,
    )

    # Step 4: Run application and return exit code to shell
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
