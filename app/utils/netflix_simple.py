"""
Simple Netflix metadata fetcher using public Shakti API
This avoids the complexity of MSL and uses Netflix's public APIs
"""

import requests
import json
import re
from http.cookiejar import MozillaCookieJar


class NetflixSimple:
    """Simple Netflix metadata fetcher"""

    def __init__(self, cookies_path):
        self.cookies_path = cookies_path
        self.session = requests.Session()
        self._load_cookies()
        self._setup_headers()

    def _load_cookies(self):
        """Load cookies from cookies.txt"""
        jar = MozillaCookieJar(self.cookies_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        self.session.cookies = jar

    def _setup_headers(self):
        """Setup request headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def get_build_identifier(self):
        """Get Netflix build identifier from homepage"""
        try:
            r = self.session.get('https://www.netflix.com/browse')
            match = re.search(r'"BUILD_IDENTIFIER":"([^"]+)"', r.text)
            if match:
                return match.group(1)

            # Alternative pattern
            match = re.search(r'netflix\.reactContext\s*=.*?"BUILD_IDENTIFIER":"([^"]+)"', r.text)
            if match:
                return match.group(1)

            return "vf633bfcf"  # Fallback
        except:
            return "vf633bfcf"  # Fallback

    def get_title_metadata(self, title_id):
        """
        Get title metadata from Netflix's Shakti API

        :param title_id: Netflix title ID
        :return: Dictionary with metadata
        """
        build_id = self.get_build_identifier()

        # Try the metadata endpoint
        metadata_url = f"https://www.netflix.com/nq/website/memberapi/{build_id}/metadata"

        params = {
            'movieid': title_id,
            'imageformat': 'jpg'
        }

        try:
            r = self.session.get(metadata_url, params=params)
            r.raise_for_status()
            return r.json()
        except:
            pass

        # Fallback: Try pathEvaluator endpoint
        path_url = f"https://www.netflix.com/nq/website/memberapi/{build_id}/pathEvaluator"

        paths = [
            f'["videos",{title_id},["summary","title","synopsis","regularSynopsis","evidence","queue","episodeCount","info","maturity","runtime","seasonCount","releaseYear","userRating","numSeasonsLabel","delivery"]]'
        ]

        params = {
            'path': paths,
            'authURL': title_id
        }

        try:
            r = self.session.get(path_url, params=params)
            r.raise_for_status()
            data = r.json()

            # Extract video data
            if 'value' in data and 'videos' in data['value']:
                video_data = data['value']['videos'].get(str(title_id), {})
                return video_data

            return data
        except Exception as e:
            print(f"Error fetching metadata: {e}")
            return None

    def check_formats(self, title_id):
        """
        Check available formats for a title by analyzing the title page

        :param title_id: Netflix title ID
        :return: Dictionary with format information
        """
        result = {
            'title': None,
            'dolby_vision': False,
            'hdr10': False,
            'atmos': False,
            'uhd': False,
            'video_formats': [],
            'audio_formats': []
        }

        try:
            # Get the title page
            url = f"https://www.netflix.com/title/{title_id}"
            r = self.session.get(url)
            r.raise_for_status()
            html = r.text

            # Try to get metadata from Shakti API
            metadata = self.get_title_metadata(title_id)
            if metadata:
                # Extract title
                if 'title' in metadata:
                    result['title'] = metadata['title']
                elif isinstance(metadata.get('value'), dict):
                    result['title'] = metadata['value'].get('title')

                # Check delivery info for formats
                delivery = metadata.get('delivery', {})
                if delivery:
                    # Check for HDR/DV in delivery profiles
                    if 'has4K' in delivery or 'hasUltraHD' in delivery:
                        result['uhd'] = True
                    if 'hasDolbyVision' in delivery:
                        result['dolby_vision'] = True
                    if 'hasHDR' in delivery or 'hasHDR10' in delivery:
                        result['hdr10'] = True
                    if 'hasDolbyAtmos' in delivery or 'hasAtmos' in delivery:
                        result['atmos'] = True

            # Also check HTML for format indicators
            html_lower = html.lower()

            # Check for UHD/4K
            if any(x in html_lower for x in ['ultra hd', '4k', 'uhd']):
                result['uhd'] = True

            # Check for Dolby Vision
            if any(x in html_lower for x in ['dolby vision', 'dolbyvision', 'vision-enabled']):
                result['dolby_vision'] = True

            # Check for HDR
            if any(x in html_lower for x in ['hdr10', 'hdr-10', 'high dynamic range']):
                result['hdr10'] = True

            # Check for Atmos
            if any(x in html_lower for x in ['dolby atmos', 'atmosenabled', 'atmos-enabled']):
                result['atmos'] = True

            # Try to extract from React context
            match = re.search(r'netflix\.reactContext\s*=\s*({.+?});', html, re.DOTALL)
            if match:
                try:
                    react_data = json.loads(match.group(1))
                    models = react_data.get('models', {})

                    # Look for the video data
                    for key, value in models.items():
                        if isinstance(value, dict):
                            # Check for format information
                            delivery = value.get('delivery', {})
                            if delivery:
                                if delivery.get('has4K'):
                                    result['uhd'] = True
                                if delivery.get('hasDolbyVision'):
                                    result['dolby_vision'] = True
                                if delivery.get('hasHDR'):
                                    result['hdr10'] = True
                                if delivery.get('hasDolbyAtmos'):
                                    result['atmos'] = True
                except:
                    pass

            return result

        except Exception as e:
            print(f"Error checking formats: {e}")
            return result
