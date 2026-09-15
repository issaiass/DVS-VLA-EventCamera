"""Pytest configuration and shared fixtures for event camera tests.

Provides common setup, teardown, and test data for all test modules.
Follows pytest best practices for fixture organization.
"""

import pytest
import numpy as np
import cv2


@pytest.fixture
def dummy_grayscale_frame():
    """Create a dummy grayscale frame for testing.

    Returns
    -------
    np.ndarray
        Grayscale frame of shape (480, 640) with dtype uint8.
        Contains gradient pattern for realistic testing.

    Examples
    --------
    >>> def test_process(dummy_grayscale_frame):
    ...     assert dummy_grayscale_frame.shape == (480, 640)
    """
    frame = np.zeros((480, 640), dtype=np.uint8)
    # Create a gradient pattern for realistic content
    for row in range(480):
        frame[row, :] = int((row / 480) * 255)
    return frame


@pytest.fixture
def dummy_bgr_frame(dummy_grayscale_frame):
    """Create a dummy BGR color frame for testing.

    Parameters
    ----------
    dummy_grayscale_frame : np.ndarray
        Grayscale frame fixture.

    Returns
    -------
    np.ndarray
        BGR color frame of shape (480, 640, 3) with dtype uint8.
        Created by replicating grayscale across channels.

    Examples
    --------
    >>> def test_bgr_input(dummy_bgr_frame):
    ...     assert dummy_bgr_frame.shape == (480, 640, 3)
    """
    return cv2.cvtColor(dummy_grayscale_frame, cv2.COLOR_GRAY2BGR)


@pytest.fixture
def uniform_frame():
    """Create a uniform intensity frame for baseline testing.

    Returns
    -------
    np.ndarray
        BGR frame of shape (480, 640, 3) with uniform intensity (128).
        Useful for testing absence of events.
    """
    frame = np.full((480, 640, 3), 128, dtype=np.uint8)
    return frame


@pytest.fixture
def moving_object_frame():
    """Create a frame with a moving bright object.

    Returns
    -------
    np.ndarray
        BGR frame of shape (480, 640, 3) with dark background and bright square.
        The bright square at (100:200, 150:250) simulates a moving object.
    """
    frame = np.full((480, 640, 3), 50, dtype=np.uint8)  # Dark background
    frame[100:200, 150:250] = 200  # Bright moving object
    return frame


@pytest.fixture
def stationary_frame():
    """Create a frame identical to moving_object_frame.

    Returns
    -------
    np.ndarray
        BGR frame matching moving_object_frame for testing static regions.
    """
    frame = np.full((480, 640, 3), 50, dtype=np.uint8)
    frame[100:200, 150:250] = 200
    return frame


@pytest.fixture
def frame_sequence(moving_object_frame, stationary_frame):
    """Create a sequence of frames simulating motion.

    Parameters
    ----------
    moving_object_frame : np.ndarray
        Frame with moving object.
    stationary_frame : np.ndarray
        Frame with stationary object.

    Returns
    -------
    list[np.ndarray]
        List of 5 frames: 2 stationary, then object moves slightly, then stationary again.
        Used for testing temporal event detection.
    """
    frames = [
        stationary_frame.copy(),
        stationary_frame.copy(),
    ]

    # Simulate object moving right
    moving_frame = np.full((480, 640, 3), 50, dtype=np.uint8)
    moving_frame[100:200, 200:300] = 200  # Object moved right
    frames.append(moving_frame)

    frames.append(stationary_frame.copy())
    frames.append(stationary_frame.copy())

    return frames


@pytest.fixture
def simulator_parameters():
    """Provide default simulator parameters for testing.

    Returns
    -------
    dict
        Dictionary with key DVS simulator parameters:
        - positive_threshold: ON event threshold
        - negative_threshold: OFF event threshold
        - subframe_count: Temporal interpolation subframes
        - refractory_frames: Event suppression period
        - decay_window: Time surface decay time

    Examples
    --------
    >>> def test_simulator(simulator_parameters):
    ...     pos_thresh = simulator_parameters['positive_threshold']
    ...     assert pos_thresh == 0.35
    """
    return {
        "positive_threshold": 0.35,
        "negative_threshold": 0.35,
        "subframe_count": 5,
        "refractory_frames": 2,
        "decay_window": 3.0,
    }


@pytest.fixture
def simulator(simulator_parameters):
    """Create a VLAOptimizedDVSSimulator instance for testing.

    Parameters
    ----------
    simulator_parameters : dict
        Simulator parameter fixture.

    Returns
    -------
    VLAOptimizedDVSSimulator
        Simulator instance with default test parameters.

    Examples
    --------
    >>> def test_process(simulator, dummy_bgr_frame):
    ...     vis, ts, flow, events = simulator.process(dummy_bgr_frame)
    ...     assert vis.shape == (480, 640, 3)
    """
    from eventcamera import VLAOptimizedDVSSimulator

    return VLAOptimizedDVSSimulator(**simulator_parameters)


@pytest.fixture
def temp_video_file(tmp_path, dummy_bgr_frame):
    """Create a temporary test video file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory.
    dummy_bgr_frame : np.ndarray
        Frame fixture for video content.

    Returns
    -------
    str
        Path to created temporary video file.
        Contains 10 frames of dummy BGR content.

    Notes
    -----
    Video is created with:
    - Codec: MJPEG (broadly compatible)
    - FPS: 30
    - Resolution: 640x480
    - Duration: ~0.33 seconds (10 frames)
    """
    video_path = str(tmp_path / "test_video.avi")
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(video_path, fourcc, 30.0, (640, 480))

    for _ in range(10):
        writer.write(dummy_bgr_frame)

    writer.release()
    return video_path
