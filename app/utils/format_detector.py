"""
Netflix Format Detector
Parses manifest data to detect video/audio formats including HDR, Dolby Vision, and Atmos
"""

import base64
import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional


class FormatDetector:
    """Detects available video and audio formats from Netflix manifest data"""

    def __init__(self):
        self.log = logging.getLogger("FormatDetector")

    def analyze_manifest(self, manifest_data: dict) -> Dict:
        """
        Analyze Netflix manifest to detect available formats

        :param manifest_data: Manifest data from MSL response
        :return: Dictionary with detected formats
        """
        result = {
            'title': None,
            'video_tracks': [],
            'audio_tracks': [],
            'subtitle_tracks': [],
            'dolby_vision': False,
            'hdr10': False,
            'atmos': False,
            'max_resolution': None,
            'max_resolution_label': None,
            'max_bitrate': 0
        }

        # Extract title information
        if 'video_tracks' in manifest_data:
            for track in manifest_data['video_tracks']:
                if 'title' in track:
                    result['title'] = track['title']
                    break

        # Check if manifest contains DASH MPD
        mpd_url = None
        if 'result' in manifest_data:
            mpd_data = manifest_data['result']
        else:
            mpd_data = manifest_data

        # Look for video tracks in the manifest
        if 'video_tracks' in mpd_data:
            result['video_tracks'] = self._parse_video_tracks(mpd_data['video_tracks'])

        # Look for audio tracks
        if 'audio_tracks' in mpd_data:
            result['audio_tracks'] = self._parse_audio_tracks(mpd_data['audio_tracks'])

        # Look for subtitle tracks
        if 'timedtexttracks' in mpd_data:
            result['subtitle_tracks'] = self._parse_subtitle_tracks(mpd_data['timedtexttracks'])

        # Parse from MPD if available
        if 'url' in mpd_data or 'urls' in mpd_data:
            mpd_tracks = self._parse_mpd_manifest(mpd_data)
            if mpd_tracks['video_tracks']:
                result['video_tracks'].extend(mpd_tracks['video_tracks'])
            if mpd_tracks['audio_tracks']:
                result['audio_tracks'].extend(mpd_tracks['audio_tracks'])

        # Determine overall capabilities
        for track in result['video_tracks']:
            if 'dolby_vision' in track.get('format', '').lower() or track.get('dv', False):
                result['dolby_vision'] = True
            if 'hdr10' in track.get('format', '').lower() or track.get('hdr10', False):
                result['hdr10'] = True

            # Track max resolution
            if track.get('width') and track.get('height'):
                resolution = f"{track['width']}x{track['height']}"
                if not result['max_resolution'] or self._compare_resolutions(resolution, result['max_resolution']) > 0:
                    result['max_resolution'] = resolution

            # Track max bitrate
            if track.get('bitrate', 0) > result['max_bitrate']:
                result['max_bitrate'] = track['bitrate']

        for track in result['audio_tracks']:
            if 'atmos' in track.get('format', '').lower() or track.get('atmos', False):
                result['atmos'] = True

        # Convert max resolution to human-readable label
        if result['max_resolution']:
            result['max_resolution_label'] = self._classify_resolution(result['max_resolution'])

        return result

    def _parse_video_tracks(self, video_tracks: List[dict]) -> List[dict]:
        """Parse video tracks from manifest"""
        tracks = []

        for track in video_tracks:
            track_info = {
                'id': track.get('trackId', track.get('id')),
                'bitrate': track.get('bitrate', 0),
                'width': track.get('width', track.get('res_w')),
                'height': track.get('height', track.get('res_h')),
                'codec': None,
                'format': 'SDR',
                'fps': track.get('framerate', track.get('fps')),
                'hdr10': False,
                'dv': False,
                'profile': None
            }

            # Detect codec and format from various fields
            codec = track.get('codec', track.get('content_profile', ''))

            # Parse codec information
            if codec:
                track_info['codec'] = self._parse_video_codec(codec)
                track_info['format'], track_info['hdr10'], track_info['dv'], track_info['profile'] = \
                    self._detect_video_format(codec)

            tracks.append(track_info)

        return tracks

    def _parse_audio_tracks(self, audio_tracks: List[dict]) -> List[dict]:
        """Parse audio tracks from manifest"""
        tracks = []

        for track in audio_tracks:
            track_info = {
                'id': track.get('trackId', track.get('id')),
                'language': track.get('language', track.get('languageDescription', 'Unknown')),
                'bitrate': track.get('bitrate', 0),
                'channels': track.get('channels', track.get('channelsCount')),
                'codec': None,
                'format': 'Stereo',
                'atmos': False
            }

            # Detect codec and format
            codec = track.get('codec', track.get('content_profile', ''))
            if codec:
                track_info['codec'] = self._parse_audio_codec(codec)
                track_info['format'], track_info['atmos'] = self._detect_audio_format(codec, track)

            tracks.append(track_info)

        return tracks

    def _parse_subtitle_tracks(self, subtitle_tracks: List[dict]) -> List[dict]:
        """Parse subtitle tracks from manifest"""
        tracks = []

        for track in subtitle_tracks:
            track_info = {
                'id': track.get('trackId', track.get('id')),
                'language': track.get('language', track.get('languageDescription', 'Unknown')),
                'type': track.get('trackType', 'subtitle'),
                'forced': track.get('isForcedNarrative', False),
                'sdh': 'sdh' in track.get('trackType', '').lower()
            }
            tracks.append(track_info)

        return tracks

    def _parse_mpd_manifest(self, mpd_data: dict) -> Dict:
        """Parse DASH MPD XML manifest if available"""
        result = {
            'video_tracks': [],
            'audio_tracks': []
        }

        # This would require fetching and parsing the actual MPD XML
        # For now, we'll work with the structured data Netflix provides

        return result

    def _parse_video_codec(self, codec_string: str) -> str:
        """Parse video codec from codec string"""
        codec_lower = codec_string.lower()

        if 'h264' in codec_lower or 'avc' in codec_lower:
            return 'H.264'
        elif 'h265' in codec_lower or 'hevc' in codec_lower or 'hev' in codec_lower or 'hvc' in codec_lower:
            return 'H.265/HEVC'
        elif 'vp9' in codec_lower:
            return 'VP9'
        elif 'av1' in codec_lower or 'av01' in codec_lower:
            return 'AV1'
        elif 'dvhe' in codec_lower or 'dvh1' in codec_lower:
            return 'H.265/HEVC (Dolby Vision)'

        return codec_string

    def _detect_video_format(self, codec_string: str) -> tuple:
        """
        Detect video format from codec string

        :return: (format_name, is_hdr10, is_dolby_vision, dv_profile)
        """
        codec_lower = codec_string.lower()

        # Dolby Vision detection
        if 'dv' in codec_lower or 'dolbyvision' in codec_lower:
            # Extract Dolby Vision profile
            profile = None
            if 'dv5' in codec_lower or 'dvhe.05' in codec_lower or 'dvh1.05' in codec_lower:
                profile = '5'
            elif 'dv7' in codec_lower or 'dvhe.07' in codec_lower or 'dvh1.07' in codec_lower:
                profile = '7'
            elif 'dv8' in codec_lower or 'dvhe.08' in codec_lower or 'dvh1.08' in codec_lower:
                profile = '8'
            elif 'dv4' in codec_lower or 'dvhe.04' in codec_lower or 'dvh1.04' in codec_lower:
                profile = '4'

            format_name = f"Dolby Vision"
            if profile:
                format_name += f" Profile {profile}"

            return (format_name, False, True, profile)

        # HDR10 detection
        if 'hdr' in codec_lower:
            if 'hdr10+' in codec_lower or 'hdr10plus' in codec_lower:
                return ('HDR10+', True, False, None)
            else:
                return ('HDR10', True, False, None)

        # HLG detection
        if 'hlg' in codec_lower:
            return ('HLG', False, False, None)

        # Default to SDR
        return ('SDR', False, False, None)

    def _parse_audio_codec(self, codec_string: str) -> str:
        """Parse audio codec from codec string"""
        codec_lower = codec_string.lower()

        if 'aac' in codec_lower:
            return 'AAC'
        elif 'ac-3' in codec_lower or 'ac3' in codec_lower or 'dd' in codec_lower and 'ddplus' not in codec_lower:
            return 'Dolby Digital (AC-3)'
        elif 'ec-3' in codec_lower or 'ec3' in codec_lower or 'ddplus' in codec_lower or 'eac3' in codec_lower:
            return 'Dolby Digital Plus (E-AC-3)'
        elif 'opus' in codec_lower:
            return 'Opus'
        elif 'vorbis' in codec_lower:
            return 'Vorbis'

        return codec_string

    def _detect_audio_format(self, codec_string: str, track_data: dict) -> tuple:
        """
        Detect audio format from codec string and track data

        :return: (format_name, is_atmos)
        """
        codec_lower = codec_string.lower()

        # Atmos detection
        if 'atmos' in codec_lower:
            channels = track_data.get('channels', 0)
            return (f'Dolby Atmos ({channels} channels)', True)

        # Standard surround sound
        channels = track_data.get('channels', 0)
        if channels:
            if channels >= 6:
                return (f'{channels/2:.1f} Surround', False)
            elif channels == 2:
                return ('Stereo', False)
            elif channels == 1:
                return ('Mono', False)

        # Check for specific formats in codec
        if 'ddplus' in codec_lower or 'ec-3' in codec_lower:
            return ('Dolby Digital Plus 5.1', False)
        elif 'dd' in codec_lower or 'ac-3' in codec_lower:
            return ('Dolby Digital 5.1', False)

        return ('Stereo', False)

    @staticmethod
    def _classify_resolution(resolution: str) -> str:
        """
        Convert resolution string to human-readable label

        :param resolution: Resolution string like "3840x2160"
        :return: Label like "UHD (4K)", "FHD (1080p)", etc.
        """
        try:
            w, h = map(int, resolution.split('x'))
            pixels = w * h

            # Classifications based on height (more reliable than pixel count)
            if h >= 2160:  # 4K / UHD
                return "UHD (4K)"
            elif h >= 1440:  # QHD
                return "QHD (1440p)"
            elif h >= 1080:  # Full HD
                return "FHD (1080p)"
            elif h >= 720:  # HD
                return "HD (720p)"
            elif h >= 480:  # SD
                return "SD (480p)"
            else:
                return f"{resolution}"
        except:
            return resolution

    @staticmethod
    def _compare_resolutions(res1: str, res2: str) -> int:
        """
        Compare two resolution strings

        :return: 1 if res1 > res2, -1 if res1 < res2, 0 if equal
        """
        def parse_res(res):
            w, h = map(int, res.split('x'))
            return w * h

        pixels1 = parse_res(res1)
        pixels2 = parse_res(res2)

        if pixels1 > pixels2:
            return 1
        elif pixels1 < pixels2:
            return -1
        return 0

    def format_results(self, analysis: dict) -> str:
        """Format analysis results as a readable string"""
        lines = []

        if analysis.get('title'):
            lines.append(f"Title: {analysis['title']}")

        lines.append("\nVideo Capabilities:")
        lines.append(f"  Dolby Vision: {'✓ Yes' if analysis['dolby_vision'] else '✗ No'}")
        lines.append(f"  HDR10: {'✓ Yes' if analysis['hdr10'] else '✗ No'}")
        lines.append(f"  Max Resolution: {analysis['max_resolution'] or 'N/A'}")
        lines.append(f"  Max Bitrate: {analysis['max_bitrate'] / 1000:.1f} Mbps" if analysis['max_bitrate'] else "  Max Bitrate: N/A")

        lines.append("\nAudio Capabilities:")
        lines.append(f"  Dolby Atmos: {'✓ Yes' if analysis['atmos'] else '✗ No'}")

        if analysis.get('video_tracks'):
            lines.append(f"\nVideo Tracks ({len(analysis['video_tracks'])}):")
            for i, track in enumerate(analysis['video_tracks'][:10], 1):  # Limit to 10
                lines.append(f"  {i}. {track.get('format', 'Unknown')} - "
                           f"{track.get('width', '?')}x{track.get('height', '?')} - "
                           f"{track.get('bitrate', 0) / 1000:.1f} Mbps - "
                           f"{track.get('codec', 'Unknown')}")

        if analysis.get('audio_tracks'):
            lines.append(f"\nAudio Tracks ({len(analysis['audio_tracks'])}):")
            for i, track in enumerate(analysis['audio_tracks'][:10], 1):  # Limit to 10
                lines.append(f"  {i}. {track.get('language', 'Unknown')} - "
                           f"{track.get('format', 'Unknown')} - "
                           f"{track.get('codec', 'Unknown')}")

        return '\n'.join(lines)
