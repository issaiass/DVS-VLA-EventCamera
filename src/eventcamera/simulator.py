"""Event camera simulator using DIS Optical Flow, MOG2 background subtraction, and CLAHE normalization.

This module implements a VLA-optimized DVS (Dynamic Vision Sensor) simulator
designed for robotics applications, particularly humanoid robot vision systems.
"""

import cv2
import numpy as np


class VLAOptimizedDVSSimulator:
    """Vision Language Agent optimized Dynamic Vision Sensor simulator.

    Simulates an event camera using a combination of optical flow warping,
    background subtraction, and temporal filtering. Optimized for multimodal
    vision systems in robotics applications.

    Parameters
    ----------
    positive_threshold : float, optional
        Threshold for positive (ON) event generation in log-intensity space.
        Default is 0.35.
    negative_threshold : float, optional
        Threshold for negative (OFF) event generation in log-intensity space.
        Default is 0.35.
    subframe_count : int, optional
        Number of interpolation subframes between input frames.
        Higher values give better temporal resolution. Default is 5.
    refractory_frames : int, optional
        Refractory period (in frames) after an event fires at a pixel.
        Prevents multiple events from the same pixel in quick succession.
        Default is 2.
    decay_window : float, optional
        Time window (in frames) for event decay in time surface visualization.
        Default is 3.0.

    Attributes
    ----------
    positive_threshold : float
        Threshold for ON events.
    negative_threshold : float
        Threshold for OFF events.
    subframe_count : int
        Number of interpolation subframes.
    refractory_frames : int
        Refractory period in frames.
    decay_window : float
        Event decay time window.
    optical_flow_algorithm : cv2.DISOpticalFlow
        DIS Optical Flow algorithm instance.
    clahe : cv2.CLAHE
        CLAHE contrast normalization instance.
    background_subtractor : cv2.BackgroundSubtractorMOG2
        MOG2 background subtraction algorithm instance.

    Examples
    --------
    >>> import cv2
    >>> simulator = VLAOptimizedDVSSimulator(
    ...     positive_threshold=0.35,
    ...     negative_threshold=0.35,
    ...     subframe_count=5
    ... )
    >>> cap = cv2.VideoCapture(0)
    >>> ret, frame = cap.read()
    >>> if ret:
    ...     event_vis, time_surface, flow_vis, events = simulator.process(frame)
    """

    # Configuration constants following Clean Code principles
    _CLAHE_CLIP_LIMIT = 2.0
    _CLAHE_TILE_SIZE = (8, 8)
    _MOG2_HISTORY = 500
    _MOG2_VAR_THRESHOLD = 20  # Fine-tuned for hand dexterity
    _MORPH_KERNEL_SIZE = (3, 3)
    _LOG_EPSILON = 1e-6
    _FLOW_VISUALIZATION_STEP = 16  # Arrow spacing in flow visualization
    _FLOW_VISUALIZATION_MIN_MAGNITUDE = 0.5
    _BGR_RED = (0, 0, 255)
    _BGR_BLUE = (255, 0, 0)
    _BGR_MAGENTA = (255, 0, 255)

    def __init__(
        self,
        positive_threshold: float = 0.35,
        negative_threshold: float = 0.35,
        subframe_count: int = 5,
        refractory_frames: int = 2,
        decay_window: float = 3.0,
    ) -> None:
        """Initialize the DVS simulator with configured parameters.

        Parameters
        ----------
        positive_threshold : float, optional
            ON event threshold. Default is 0.35.
        negative_threshold : float, optional
            OFF event threshold. Default is 0.35.
        subframe_count : int, optional
            Number of interpolation subframes. Default is 5.
        refractory_frames : int, optional
            Refractory period. Default is 2.
        decay_window : float, optional
            Time surface decay window. Default is 3.0.
        """
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold
        self.subframe_count = subframe_count
        self.refractory_frames = refractory_frames
        self.decay_window = decay_window

        # Temporal state tracking: maintains pixel history across frames
        # for computing log-intensity deltas and enforcing refractory periods
        self.previous_grayscale = None
        self.previous_log_intensity = None
        self.refractory_map = None
        self.time_surface = None
        self.last_visualization = None
        self.coordinate_grid_x = None
        self.coordinate_grid_y = None

        # Core algorithms for event detection pipeline:
        # DIS optical flow: enables sub-frame temporal interpolation for finer
        # event timing and better motion tracking
        self.optical_flow_algorithm = cv2.DISOpticalFlow_create(
            cv2.DISOpticalFlow_PRESET_MEDIUM
        )

        # CLAHE (Contrast Limited Adaptive Histogram Equalization) ensures VLA
        # systems don't get "blinded" by sudden illumination changes or high contrast
        self.clahe = cv2.createCLAHE(
            clipLimit=self._CLAHE_CLIP_LIMIT, tileGridSize=self._CLAHE_TILE_SIZE
        )

        # MOG2 background subtraction isolates dynamic foreground objects,
        # reducing false events from static scene noise and shadows
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=self._MOG2_HISTORY,
            varThreshold=self._MOG2_VAR_THRESHOLD,
            detectShadows=False,
        )

        # Morphological filtering cleans MOG2 output by removing salt-and-pepper noise
        self.morphological_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, self._MORPH_KERNEL_SIZE
        )

    def _convert_to_log_intensity(self, grayscale_frame: np.ndarray) -> np.ndarray:
        """Convert grayscale frame to log-intensity space.

        Parameters
        ----------
        grayscale_frame : np.ndarray
            Input grayscale frame of shape (height, width) with dtype uint8.

        Returns
        -------
        np.ndarray
            Log-intensity representation of shape (height, width) with dtype float32.
            Range is approximately (-inf, 0] with typical values around [-6, 0].

        Examples
        --------
        >>> import numpy as np
        >>> gray_frame = np.array([[0, 128, 255]], dtype=np.uint8)
        >>> simulator = VLAOptimizedDVSSimulator()
        >>> log_frame = simulator._convert_to_log_intensity(gray_frame)
        >>> log_frame.shape
        (1, 3)
        >>> log_frame.dtype
        dtype('float32')
        """
        normalized_frame = grayscale_frame.astype(np.float32) / 255.0
        return cv2.log(normalized_frame + self._LOG_EPSILON)

    def _initialize_first_frame(
        self, grayscale_frame: np.ndarray, log_intensity: np.ndarray
    ) -> tuple:
        """Initialize internal state on first frame.

        Parameters
        ----------
        grayscale_frame : np.ndarray
            First input grayscale frame of shape (height, width).
        log_intensity : np.ndarray
            Log-intensity representation of the frame.

        Returns
        -------
        tuple
            Four-element tuple containing:
            - event_visualization : np.ndarray, shape (height, width, 3), dtype uint8
            - time_surface_visualization : np.ndarray, same shape and dtype
            - optical_flow_visualization : np.ndarray, same shape and dtype
            - events : list, empty list (no events on first frame)

        Examples
        --------
        >>> import numpy as np
        >>> gray = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
        >>> simulator = VLAOptimizedDVSSimulator()
        >>> log_int = simulator._convert_to_log_intensity(gray)
        >>> vis_event, vis_ts, vis_flow, evts = simulator._initialize_first_frame(gray, log_int)
        >>> vis_event.shape
        (480, 640, 3)
        >>> len(evts)
        0
        """
        height, width = grayscale_frame.shape

        self.previous_grayscale = grayscale_frame
        self.previous_log_intensity = log_intensity
        self.refractory_map = np.zeros((height, width), dtype=np.int32)
        self.time_surface = np.zeros((height, width), dtype=np.float32)
        self.last_visualization = np.zeros((height, width, 3), dtype=np.uint8)
        self.coordinate_grid_x, self.coordinate_grid_y = np.meshgrid(
            np.arange(width), np.arange(height)
        )

        blank_visualization = np.zeros((height, width, 3), dtype=np.uint8)
        return (
            blank_visualization.copy(),
            blank_visualization.copy(),
            blank_visualization.copy(),
            [],
        )

    def _warp_log_intensity_frame(
        self, optical_flow: np.ndarray, interpolation_fraction: float
    ) -> np.ndarray:
        """Warp previous log-intensity frame according to optical flow.

        Performs temporal interpolation by warping the previous frame
        along the computed optical flow field.

        Parameters
        ----------
        optical_flow : np.ndarray
            Optical flow field of shape (height, width, 2) representing
            x and y displacements.
        interpolation_fraction : float
            Fraction of flow to apply, in range [0, 1]. Value of 0.5
            represents motion at halfway between frames.

        Returns
        -------
        np.ndarray
            Warped log-intensity frame of shape (height, width, dtype float32).

        Examples
        --------
        >>> import numpy as np
        >>> simulator = VLAOptimizedDVSSimulator()
        >>> # Simulate a 3x3 grid with optical flow
        >>> simulator.previous_log_intensity = np.random.randn(3, 3).astype(np.float32)
        >>> simulator.coordinate_grid_x = np.array([[0, 1, 2], [0, 1, 2], [0, 1, 2]], dtype=np.float32)
        >>> simulator.coordinate_grid_y = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=np.float32)
        >>> flow = np.zeros((3, 3, 2), dtype=np.float32)
        >>> warped = simulator._warp_log_intensity_frame(flow, 0.5)
        >>> warped.shape
        (3, 3)
        """
        map_x = (
            self.coordinate_grid_x - optical_flow[..., 0] * interpolation_fraction
        ).astype(np.float32)
        map_y = (
            self.coordinate_grid_y - optical_flow[..., 1] * interpolation_fraction
        ).astype(np.float32)
        return cv2.remap(
            self.previous_log_intensity, map_x, map_y, cv2.INTER_LINEAR
        )

    def _apply_refractory_period(
        self, positive_mask: np.ndarray, negative_mask: np.ndarray
    ) -> tuple:
        """Apply refractory period suppression to event masks.

        Pixels that fired recently are suppressed to prevent multiple
        events at the same location in quick succession.

        Parameters
        ----------
        positive_mask : np.ndarray
            Binary mask of ON events, shape (height, width).
        negative_mask : np.ndarray
            Binary mask of OFF events, shape (height, width).

        Returns
        -------
        tuple
            Two-element tuple of suppressed masks:
            - positive_mask_suppressed : np.ndarray, binary mask
            - negative_mask_suppressed : np.ndarray, binary mask

        Examples
        --------
        >>> import numpy as np
        >>> simulator = VLAOptimizedDVSSimulator(refractory_frames=2)
        >>> simulator.refractory_map = np.array([[0, 1], [0, 0]], dtype=np.int32)
        >>> pos = np.array([[1, 1], [1, 1]], dtype=np.uint8) * 255
        >>> neg = np.array([[1, 1], [1, 1]], dtype=np.uint8) * 255
        >>> pos_sup, neg_sup = simulator._apply_refractory_period(pos, neg)
        >>> pos_sup[0, 1]  # Suppressed due to refractory
        0
        """
        active_pixels = cv2.compare(self.refractory_map, 0, cv2.CMP_GT)
        inactive_pixels = cv2.bitwise_not(active_pixels)

        positive_suppressed = cv2.bitwise_and(positive_mask, inactive_pixels)
        negative_suppressed = cv2.bitwise_and(negative_mask, inactive_pixels)

        return positive_suppressed, negative_suppressed

    def _update_refractory_and_time_surface(
        self,
        positive_mask: np.ndarray,
        negative_mask: np.ndarray,
        timestamp: float,
    ) -> None:
        """Update refractory period map and time surface.

        Parameters
        ----------
        positive_mask : np.ndarray
            Binary mask of ON events.
        negative_mask : np.ndarray
            Binary mask of OFF events.
        timestamp : float
            Current frame timestamp (frame index + subframe fraction).

        Returns
        -------
        None
            Updates internal state in-place.

        Examples
        --------
        >>> import numpy as np
        >>> simulator = VLAOptimizedDVSSimulator(refractory_frames=2)
        >>> simulator.refractory_map = np.zeros((2, 2), dtype=np.int32)
        >>> simulator.time_surface = np.zeros((2, 2), dtype=np.float32)
        >>> pos = np.array([[1, 0], [0, 0]], dtype=np.uint8) * 255
        >>> neg = np.array([[0, 0], [0, 1]], dtype=np.uint8) * 255
        >>> simulator._update_refractory_and_time_surface(pos, neg, 1.5)
        >>> simulator.refractory_map[0, 0]
        2
        >>> simulator.time_surface[1, 1]
        1.5
        """
        self.refractory_map[positive_mask > 0] = self.refractory_frames
        self.refractory_map[negative_mask > 0] = self.refractory_frames
        self.refractory_map[self.refractory_map > 0] -= 1

        self.time_surface[positive_mask > 0] = timestamp
        self.time_surface[negative_mask > 0] = timestamp

    def _render_events_to_visualization(
        self,
        visualization: np.ndarray,
        positive_mask: np.ndarray,
        negative_mask: np.ndarray,
        events_list: list,
        timestamp: float,
    ) -> None:
        """Render event masks to visualization and append to event list.

        Parameters
        ----------
        visualization : np.ndarray
            Color visualization array of shape (height, width, 3), modified in-place.
        positive_mask : np.ndarray
            Binary mask of ON events.
        negative_mask : np.ndarray
            Binary mask of OFF events.
        events_list : list
            List to append events to. Each event is a tuple (x, y, polarity, timestamp).
        timestamp : float
            Current frame timestamp.

        Returns
        -------
        None
            Modifies visualization and events_list in-place.

        Examples
        --------
        >>> import numpy as np
        >>> vis = np.zeros((2, 2, 3), dtype=np.uint8)
        >>> pos = np.array([[1, 0], [0, 0]], dtype=np.uint8) * 255
        >>> neg = np.array([[0, 0], [0, 1]], dtype=np.uint8) * 255
        >>> events = []
        >>> simulator = VLAOptimizedDVSSimulator()
        >>> simulator._render_events_to_visualization(vis, pos, neg, events, 1.0)
        >>> len(events)
        2
        >>> events[0][2]  # Polarity of first event (ON)
        1
        """
        positive_coords = np.nonzero(positive_mask)
        for y_coord, x_coord in zip(positive_coords[0], positive_coords[1]):
            events_list.append((x_coord, y_coord, 1, timestamp))
            visualization[y_coord, x_coord] = self._BGR_RED

        negative_coords = np.nonzero(negative_mask)
        for y_coord, x_coord in zip(negative_coords[0], negative_coords[1]):
            events_list.append((x_coord, y_coord, -1, timestamp))
            visualization[y_coord, x_coord] = self._BGR_BLUE

    def _create_time_surface_visualization(
        self, current_timestamp: float
    ) -> np.ndarray:
        """Create time surface visualization with exponential decay.

        Generates a visualization where pixel intensity represents
        time since last event (recent events are bright, old events are dark).

        Parameters
        ----------
        current_timestamp : float
            Current frame timestamp.

        Returns
        -------
        np.ndarray
            Visualization array of shape (height, width, 3), dtype uint8.
            Uses jet colormap where bright colors indicate recent events.

        Examples
        --------
        >>> import numpy as np
        >>> simulator = VLAOptimizedDVSSimulator(decay_window=3.0)
        >>> simulator.time_surface = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32)
        >>> ts_vis = simulator._create_time_surface_visualization(3.5)
        >>> ts_vis.shape
        (2, 2, 3)
        >>> ts_vis.dtype
        dtype('uint8')
        """
        time_since_event = current_timestamp - self.time_surface
        normalized_time = np.clip(
            1.0 - (time_since_event / self.decay_window), 0, 1
        )
        intensity_map = (normalized_time * 255).astype(np.uint8)
        time_surface_vis = cv2.applyColorMap(intensity_map, cv2.COLORMAP_JET)
        time_surface_vis[time_since_event >= self.decay_window] = (0, 0, 0)
        return time_surface_vis

    def _apply_clahe_normalization(self, bgr_visualization: np.ndarray) -> np.ndarray:
        """Apply CLAHE normalization to prevent VLA 'blinding'.

        Applies Contrast Limited Adaptive Histogram Equalization
        in LAB color space to normalize contrast while preserving
        natural color appearance.

        Parameters
        ----------
        bgr_visualization : np.ndarray
            Color visualization in BGR format, shape (height, width, 3).

        Returns
        -------
        np.ndarray
            CLAHE-normalized visualization in BGR format.

        Examples
        --------
        >>> import numpy as np
        >>> import cv2
        >>> simulator = VLAOptimizedDVSSimulator()
        >>> vis = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
        >>> normalized = simulator._apply_clahe_normalization(vis)
        >>> normalized.shape
        (10, 10, 3)
        """
        lab_image = cv2.cvtColor(bgr_visualization, cv2.COLOR_BGR2Lab)
        lab_image[:, :, 0] = self.clahe.apply(lab_image[:, :, 0])
        return cv2.cvtColor(lab_image, cv2.COLOR_Lab2BGR)

    def _create_optical_flow_visualization(
        self, grayscale_frame: np.ndarray, optical_flow: np.ndarray
    ) -> np.ndarray:
        """Create optical flow visualization with motion arrows.

        Parameters
        ----------
        grayscale_frame : np.ndarray
            Grayscale frame of shape (height, width).
        optical_flow : np.ndarray
            Optical flow field of shape (height, width, 2).

        Returns
        -------
        np.ndarray
            Visualization with flow vectors drawn as arrows.

        Examples
        --------
        >>> import numpy as np
        >>> simulator = VLAOptimizedDVSSimulator()
        >>> gray = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
        >>> flow = np.random.randn(480, 640, 2).astype(np.float32)
        >>> flow_vis = simulator._create_optical_flow_visualization(gray, flow)
        >>> flow_vis.shape
        (480, 640, 3)
        """
        flow_vis = cv2.cvtColor(grayscale_frame, cv2.COLOR_GRAY2BGR)
        height, width = grayscale_frame.shape
        y_coords, x_coords = np.mgrid[
            8 : height : self._FLOW_VISUALIZATION_STEP,
            8 : width : self._FLOW_VISUALIZATION_STEP,
        ].reshape(2, -1).astype(int)

        flow_x, flow_y = optical_flow[y_coords, x_coords].T

        for idx in range(len(x_coords)):
            magnitude = np.sqrt(flow_x[idx] ** 2 + flow_y[idx] ** 2)
            if magnitude > self._FLOW_VISUALIZATION_MIN_MAGNITUDE:
                end_x = int(x_coords[idx] + flow_x[idx] * 2)
                end_y = int(y_coords[idx] + flow_y[idx] * 2)
                cv2.arrowedLine(
                    flow_vis,
                    (x_coords[idx], y_coords[idx]),
                    (end_x, end_y),
                    self._BGR_MAGENTA,
                    1,
                    cv2.LINE_AA,
                    0,
                    0.3,
                )

        return flow_vis

    def process(
        self, frame_bgr: np.ndarray, frame_index: int = 0
    ) -> tuple:
        """Process a single frame and generate events.

        Main processing pipeline: background subtraction → optical flow →
        temporal interpolation → event detection → visualization.

        Parameters
        ----------
        frame_bgr : np.ndarray
            Input frame in BGR color format, shape (height, width, 3), dtype uint8.
        frame_index : int, optional
            Index of the frame in the sequence. Used for event timestamps.
            Default is 0.

        Returns
        -------
        tuple
            Four-element tuple containing:
            - event_visualization : np.ndarray, shape (height, width, 3), dtype uint8.
              Red pixels indicate ON events, blue indicate OFF events.
            - time_surface_visualization : np.ndarray, same shape and dtype.
              Jet colormap where bright colors indicate recent events.
            - optical_flow_visualization : np.ndarray, same shape and dtype.
              Input frame with magenta arrows showing motion vectors.
            - events : list of tuples
              Each event is (x, y, polarity, timestamp) where polarity is
              1 for ON and -1 for OFF.

        Examples
        --------
        >>> import cv2
        >>> import numpy as np
        >>> simulator = VLAOptimizedDVSSimulator()
        >>> # Create a dummy frame (480x640 BGR)
        >>> frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        >>> event_vis, ts_vis, flow_vis, events = simulator.process(frame, 0)
        >>> event_vis.shape
        (480, 640, 3)
        >>> isinstance(events, list)
        True

        Notes
        -----
        - First frame initializes internal state and returns all-zero visualizations.
        - Events are sparse and typically concentrated at edges and moving regions.
        - Timestamps are continuous floats (e.g., frame 5 might have events at 5.2, 5.4).
        """
        # Step 1: Extract grayscale and compute foreground mask
        # Static background is filtered early to reduce spurious events from noise
        grayscale_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # Morphological opening (erode→dilate) removes small noise blobs from MOG2 output
        foreground_mask = cv2.morphologyEx(
            self.background_subtractor.apply(grayscale_frame),
            cv2.MORPH_OPEN,
            self.morphological_kernel,
        )

        # Step 2: Convert to log-intensity space for DVS modeling
        # Log space mimics biological photoreceptor response and event generation
        current_log_intensity = self._convert_to_log_intensity(grayscale_frame)

        # First frame is special: initialize state but don't generate events
        if self.previous_grayscale is None:
            return self._initialize_first_frame(grayscale_frame, current_log_intensity)

        # Step 3: Estimate motion between frames using optical flow
        # Flow enables temporal interpolation for finer event timing resolution
        optical_flow = self.optical_flow_algorithm.calc(
            self.previous_grayscale, grayscale_frame, None
        )
        event_visualization = np.zeros(
            (*grayscale_frame.shape, 3), dtype=np.uint8
        )
        events_list = []

        # Step 4: Interpolate between frames and detect events at sub-frame level
        # This achieves much finer temporal resolution than frame-based detection
        for subframe_index in range(1, self.subframe_count + 1):
            interpolation_fraction = subframe_index / self.subframe_count

            # Warp previous frame along motion trajectory to intermediate time
            warped_log_intensity = self._warp_log_intensity_frame(
                optical_flow, interpolation_fraction
            )

            # Compute intensity change in log space (approximates biological sensor)
            intensity_delta = cv2.subtract(
                warped_log_intensity, self.previous_log_intensity
            )

            # Threshold in log domain: positive (brightness increase) vs negative (decrease)
            # Combine with foreground mask to ignore background noise
            positive_mask = cv2.bitwise_and(
                cv2.compare(intensity_delta, self.positive_threshold, cv2.CMP_GT),
                foreground_mask,
            )
            negative_mask = cv2.bitwise_and(
                cv2.compare(
                    intensity_delta, -self.negative_threshold, cv2.CMP_LT
                ),
                foreground_mask,
            )

            # Apply refractory period to prevent pixel saturation from rapid repeated events
            positive_mask, negative_mask = self._apply_refractory_period(
                positive_mask, negative_mask
            )

            # Render detected events with sub-frame timestamp
            timestamp = frame_index + interpolation_fraction
            self._render_events_to_visualization(
                event_visualization,
                positive_mask,
                negative_mask,
                events_list,
                timestamp,
            )
            self._update_refractory_and_time_surface(
                positive_mask, negative_mask, timestamp
            )

        # Step 5: Implement event latching (persistence) for visualization
        # If no new events this frame, show last frame's events to reduce flicker
        self.last_visualization = (
            event_visualization.copy() if events_list else
            (self.last_visualization if self.last_visualization is not None else event_visualization)
        )

        # Step 6: Update state for next frame
        self.previous_grayscale = grayscale_frame
        self.previous_log_intensity = current_log_intensity

        # Step 7: Generate all output visualizations for robotics pipeline
        time_surface_vis = self._create_time_surface_visualization(
            frame_index + 1.0
        )
        # CLAHE prevents VLA systems from being overwhelmed by high-contrast regions
        clahe_normalized_ts = self._apply_clahe_normalization(time_surface_vis)
        # Optical flow visualization aids in debugging motion tracking
        flow_vis = self._create_optical_flow_visualization(
            grayscale_frame, optical_flow
        )

        return self.last_visualization, clahe_normalized_ts, flow_vis, events_list
