"""Unit tests for CLI argument parsing.

Tests cover argument parser creation, default values, and custom arguments.

TDD: These tests define the CLI contract and user-facing interface.
"""

import pytest

from src.main import (
    create_argument_parser,
    parse_video_source,
)


class TestArgumentParser:
    """Test command-line argument parser configuration."""

    def test_parser_creation(self):
        """Verify argument parser is created successfully.

        Arrange: Request parser creation
        Act: Create argument parser
        Assert: Parser is not None and configured
        """
        parser = create_argument_parser()

        assert parser is not None
        assert parser.prog == "event-camera"

    def test_parser_default_source_is_camera_zero(self):
        """Verify default video source is camera 0.

        Arrange: Parse empty arguments
        Act: Get default argument values
        Assert: source defaults to "0" (camera 0)
        """
        parser = create_argument_parser()
        args = parser.parse_args([])

        assert args.source == "0"

    def test_parser_default_thresholds(self):
        """Verify default threshold values match simulator defaults.

        Arrange: Parse empty arguments
        Act: Get threshold defaults
        Assert: Thresholds match documented defaults
        """
        parser = create_argument_parser()
        args = parser.parse_args([])

        assert args.pos_threshold == 0.35
        assert args.neg_threshold == 0.35

    def test_parser_default_temporal_params(self):
        """Verify default temporal parameters.

        Arrange: Parse empty arguments
        Act: Get temporal parameter defaults
        Assert: Subframes, refractory, decay match defaults
        """
        parser = create_argument_parser()
        args = parser.parse_args([])

        assert args.subframes == 5
        assert args.refractory == 2
        assert args.decay == 3.0

    def test_parser_accepts_camera_index(self):
        """Verify parser accepts numeric camera index.

        Arrange: Prepare camera index argument
        Act: Parse --source 1
        Assert: source value is "1"
        """
        parser = create_argument_parser()
        args = parser.parse_args(["--source", "1"])

        assert args.source == "1"

    def test_parser_accepts_file_path(self):
        """Verify parser accepts file path as source.

        Arrange: Prepare file path argument
        Act: Parse --source video.mp4
        Assert: source value is "video.mp4"
        """
        parser = create_argument_parser()
        args = parser.parse_args(["--source", "video.mp4"])

        assert args.source == "video.mp4"

    def test_parser_accepts_custom_thresholds(self):
        """Verify parser accepts custom threshold arguments.

        Arrange: Prepare threshold arguments
        Act: Parse with custom thresholds
        Assert: Values are parsed correctly
        """
        parser = create_argument_parser()
        args = parser.parse_args(
            ["--pos-threshold", "0.25", "--neg-threshold", "0.30"]
        )

        assert args.pos_threshold == 0.25
        assert args.neg_threshold == 0.30

    def test_parser_accepts_temporal_parameters(self):
        """Verify parser accepts temporal parameter arguments.

        Arrange: Prepare temporal arguments
        Act: Parse with custom temporal values
        Assert: Values are parsed correctly
        """
        parser = create_argument_parser()
        args = parser.parse_args(
            ["--subframes", "10", "--refractory", "3", "--decay", "4.5"]
        )

        assert args.subframes == 10
        assert args.refractory == 3
        assert args.decay == 4.5

    def test_parser_combined_arguments(self):
        """Verify parser accepts all arguments together.

        Arrange: Prepare complete CLI invocation
        Act: Parse all arguments at once
        Assert: All values parsed correctly
        """
        parser = create_argument_parser()
        args = parser.parse_args(
            [
                "--source",
                "test.mp4",
                "--pos-threshold",
                "0.20",
                "--neg-threshold",
                "0.40",
                "--subframes",
                "8",
                "--refractory",
                "4",
                "--decay",
                "5.0",
            ]
        )

        assert args.source == "test.mp4"
        assert args.pos_threshold == 0.20
        assert args.neg_threshold == 0.40
        assert args.subframes == 8
        assert args.refractory == 4
        assert args.decay == 5.0


class TestVideoSourceParsing:
    """Test parse_video_source() intelligent type detection."""

    def test_parse_camera_index_zero(self):
        """Verify numeric 0 is converted to int.

        Arrange: Source string "0"
        Act: Parse with parse_video_source
        Assert: Returns integer 0
        """
        result = parse_video_source("0")

        assert isinstance(result, int)
        assert result == 0

    def test_parse_camera_indices(self):
        """Verify numeric camera indices are parsed as integers.

        Arrange: Multiple camera index strings
        Act: Parse each with parse_video_source
        Assert: All converted to int correctly
        """
        for idx in [0, 1, 2, 5, 10]:
            result = parse_video_source(str(idx))
            assert isinstance(result, int)
            assert result == idx

    def test_parse_file_path(self):
        """Verify file path is returned as string.

        Arrange: File path argument
        Act: Parse with parse_video_source
        Assert: Returns string unchanged
        """
        result = parse_video_source("video.mp4")

        assert isinstance(result, str)
        assert result == "video.mp4"

    def test_parse_absolute_file_path(self):
        """Verify absolute file paths are preserved.

        Arrange: Absolute path argument
        Act: Parse with parse_video_source
        Assert: Returns full path string
        """
        path = "/path/to/video.avi"
        result = parse_video_source(path)

        assert result == path

    def test_parse_windows_file_path(self):
        """Verify Windows file paths are preserved.

        Arrange: Windows-style path argument
        Act: Parse with parse_video_source
        Assert: Returns path unchanged
        """
        path = "C:\\Users\\test\\video.mp4"
        result = parse_video_source(path)

        assert result == path

    def test_parse_fails_gracefully_on_invalid_numeric(self):
        """Verify non-numeric strings treated as file paths.

        Arrange: Invalid numeric string
        Act: Parse with parse_video_source
        Assert: Falls back to string (file path)
        """
        # Decimal number should fail int() conversion
        result = parse_video_source("3.14")

        assert isinstance(result, str)
        assert result == "3.14"
