"""
Netflix Format Checker - Pure HTML Scraping Approach
No API calls, just parse the Netflix title page HTML
"""

import requests
import re
import json
from http.cookiejar import MozillaCookieJar
from app.models.poster_fetcher import PosterFetcher, extract_year_from_title


class NetflixScraper:
    """Netflix format checker using pure HTML scraping"""

    def __init__(self, cookies_path):
        self.cookies_path = cookies_path
        self.session = requests.Session()
        self._load_cookies()
        self._setup_headers()
        self.dolby_digital_detected = False
        self.spatial_audio_detected = False
        self.poster_fetcher = PosterFetcher()  # Initialize TMDB poster fetcher

    def _load_cookies(self):
        """Load cookies from cookies.txt"""
        jar = MozillaCookieJar(self.cookies_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        self.session.cookies = jar

    def _setup_headers(self):
        """Setup realistic browser headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })

    def check_formats(self, title_id):
        """
        Check available formats by scraping the title page

        :param title_id: Netflix title ID
        :return: Dictionary with format information
        """
        result = {
            'title': None,
            'year': None,
            'poster': None,
            'dolby_vision': False,
            'hdr10': False,
            'atmos': False,
            'dolby_digital': False,
            'spatial_audio': False,
            'uhd': False,
            '4k': False,
            'hd': False,
            'sdr': False,
            'is_available': True,
            'availability_status': 'Available',
            'coming_date': None,
            'is_series': False
        }

        try:
            # Fetch the title page
            url = f"https://www.netflix.com/title/{title_id}"
            print(f"Fetching: {url}")

            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            html = r.text

            print(f"Response length: {len(html)} chars")

            # Check if we got redirected to login
            if 'Sign In' in html or 'login' in r.url.lower():
                raise Exception("Not logged in. Please re-export cookies.txt while logged into Netflix.")

            # Extract title, year, and poster from various possible locations
            result['title'] = self._extract_title(html, title_id)
            result['year'] = self._extract_year(html, title_id)

            # Cache year for IMDb poster search (for accurate matching when multiple titles exist)
            if result['year']:
                self._cached_year = result['year']

            result['poster'] = self._extract_poster(html, title_id)

            # If year was populated by IMDb fetcher, update the result
            if hasattr(self, '_cached_year') and self._cached_year and not result['year']:
                result['year'] = self._cached_year
                print(f"Updated year from IMDb: {result['year']}")

            # Extract availability and content type information
            self._extract_availability(html, result)
            self._extract_content_type(html, result)

            # Method 1: Extract from embedded JSON data (most accurate)
            json_found = self._extract_from_json(html, result, title_id)

            # Always scan for additional audio formats (can coexist with JSON data)
            self._detect_audio_formats(html, result)

            # Method 2: Only use text pattern matching as fallback if no JSON data found
            if not json_found:
                print("Warning: No JSON delivery data found, using text pattern matching as fallback")
                html_lower = html.lower()

                # UHD/4K detection
                uhd_patterns = [
                    'ultra hd', 'ultrahd', '4k', 'uhd', '2160p',
                    '"is4k":true', '"has4k":true', 'hasultra'
                ]
                result['uhd'] = any(pattern in html_lower for pattern in uhd_patterns)
                result['4k'] = result['uhd']

                # HD detection (if not 4K)
                if not result['uhd']:
                    hd_patterns = ['1080p', '"isHd":true', 'high definition']
                    result['hd'] = any(pattern in html_lower for pattern in hd_patterns)

                # Dolby Vision detection
                dv_patterns = [
                    'dolby vision', 'dolbyvision', 'dolby-vision', 'vision-enabled',
                    'profiledolbyvision', 'dovi-enabled', 'dovi', 'dvhe', 'dvh1',
                    '"hasdolbyvision":true', 'hasdolbyvision'
                ]
                result['dolby_vision'] = any(pattern in html_lower for pattern in dv_patterns)

                # HDR10 detection
                hdr_patterns = [
                    'hdr10', 'hdr-10', 'hdr 10', 'high dynamic range',
                    'hdr-enabled', 'hdr enabled', '"hashdr":true', 'hashdr10'
                ]
                result['hdr10'] = any(pattern in html_lower for pattern in hdr_patterns)

                # Dolby Atmos detection
                atmos_patterns = [
                    'dolby atmos', 'dolbyatmos', 'dolby-atmos', 'atmosenabled',
                    'atmos-enabled', 'atmos audio', '"hasdolbyatmos":true',
                    'hasdolbyatmos', 'hasatmos'
                ]
                result['atmos'] = any(pattern in html_lower for pattern in atmos_patterns)

                # SDR (Standard Dynamic Range) detection - mutually exclusive with HDR
                # If no HDR formats detected, default to SDR being available
                has_hdr = result['hdr10'] or result['dolby_vision']
                if has_hdr:
                    result['sdr'] = False  # HDR means no SDR
                else:
                    # No HDR detected, so SDR should be True (default for standard content)
                    result['sdr'] = True


            print(f"Detection results: DV={result['dolby_vision']}, HDR={result['hdr10']}, Atmos={result['atmos']}, 4K={result['uhd']}")

            return result

        except requests.RequestException as e:
            print(f"Request error: {e}")
            raise Exception(f"Failed to fetch Netflix page: {e}")
        except Exception as e:
            print(f"Error: {e}")
            raise

    def _detect_audio_formats(self, html, result):
        """Detect additional audio formats from page content

        Only updates if not already set by JSON extraction (JSON is more reliable)
        """
        html_lower = html.lower()

        # Look for Dolby Digital (5.1 Dolby) mentions
        # Only update if not already detected from JSON
        if not result.get('dolby_digital'):
            dolby_digital_patterns = [
                'dolby digital',
                'dolby-digital',
                'ac-3',
                'ac3',
                '5.1',
                '5.1 dolby'
            ]
            result['dolby_digital'] = any(pattern in html_lower for pattern in dolby_digital_patterns)

        # Look for Spatial Audio
        # Only update if not already detected from JSON
        if not result.get('spatial_audio'):
            spatial_audio_patterns = [
                'spatial audio',
                'spatial-audio'
            ]
            result['spatial_audio'] = any(pattern in html_lower for pattern in spatial_audio_patterns)

    def _extract_title(self, html, title_id):
        """Extract title name from HTML"""
        def decode_title(title_str):
            """Decode escaped characters in title"""
            # Replace \x20 with space and other common escapes
            title_str = title_str.replace('\\x20', ' ')
            title_str = title_str.replace('\\x27', "'")
            title_str = title_str.replace('\\x26', '&')
            # Use codecs to handle any remaining hex escapes
            try:
                # Encode to bytes and decode to handle unicode escapes
                import codecs
                title_str = codecs.decode(title_str, 'unicode_escape')
            except:
                pass
            return title_str.strip()

        # Try og:title meta tag
        match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if match:
            title = match.group(1).replace(' | Netflix', '').strip()
            if title and title != 'Netflix':
                decoded = decode_title(title)
                self._cached_title = decoded
                return decoded

        # Try title tag
        match = re.search(r'<title[^>]*>([^<]+)</title>', html)
        if match:
            title = match.group(1).replace(' | Netflix', '').strip()
            if title and title != 'Netflix':
                decoded = decode_title(title)
                self._cached_title = decoded
                return decoded

        # Try to find title in JSON with better patterns
        # Look for title field near the title ID (most accurate)
        match = re.search(rf'{title_id}[^}}{{]{{0,200}}?"title":\s*"([^"]+)"', html)
        if match:
            title = match.group(1)
            if title and len(title) > 2 and title not in ['Netflix', 'Shows', 'Movies', 'My List']:
                decoded = decode_title(title)
                self._cached_title = decoded
                return decoded

        # Look for "name" field near the title ID
        match = re.search(rf'{title_id}[^}}{{]{{0,200}}?"name":\s*"([^"]+)"', html)
        if match:
            title = match.group(1)
            if title and len(title) > 2 and title not in ['Netflix', 'Shows', 'Movies', 'My List']:
                decoded = decode_title(title)
                self._cached_title = decoded
                return decoded

        # Try looking for video title with the ID as key
        match = re.search(rf'"{title_id}":\s*{{[^}}]{{0,500}}?"title":\s*"([^"]+)"', html)
        if match:
            title = match.group(1)
            if title and len(title) > 2 and title not in ['Netflix', 'Shows', 'Movies', 'My List']:
                decoded = decode_title(title)
                self._cached_title = decoded  # Cache for TMDB fallback
                return decoded

        # Cache the title for TMDB fallback (even if None)
        self._cached_title = None
        return None

    def _extract_year(self, html, title_id=None):
        """Extract release year from HTML, preferring most reliable sources first"""
        try:
            # Priority 0: Try to extract year near the actual title name (most reliable for collection pages)
            # This handles cases where Netflix pages show multiple titles with different release years
            if hasattr(self, '_cached_title') and self._cached_title:
                title = self._cached_title
                # Escape special regex characters in title
                escaped_title = re.escape(title)

                # Look for "title":"EXACT_TITLE" followed by releaseYear within 500 chars
                # Use a broader search window for better accuracy
                pattern = rf'"title"\s*:\s*"{escaped_title}"[^}}{{]*"releaseYear"\s*(?:\{{"?\$type"?:?"atom",?"?value"?:)?(\d{{4}})'
                matches = list(re.finditer(pattern, html, re.IGNORECASE | re.DOTALL))
                if matches:
                    # Use the last match (most likely to be the main title when page shows related titles)
                    year = int(matches[-1].group(1))
                    print(f"Found year from title-matched releaseYear: {year}")
                    return year

            # Priority 1: Try JSON-LD dateCreated (Netflix) - MOST RELIABLE
            # Format: "dateCreated": "2025-11-13"
            # This is the JSON-LD schema that Netflix provides
            match = re.search(r'"dateCreated"\s*:\s*"(\d{4})-', html)
            if match:
                year = int(match.group(1))
                print(f"Found year from JSON-LD dateCreated: {year}")
                return year

            # Priority 2: Try span.year pattern (from Netflix HTML display)
            # Pattern: <span class="year">(YYYY)</span>
            match = re.search(r'<span class="year">\((\d{4})\)</span>', html)
            if match:
                year = int(match.group(1))
                print(f"Found year from HTML: {year}")
                return year

            # Priority 3: Try JSON pattern: "releaseYear": YYYY (general search, get the LAST match)
            # When multiple titles are shown on a page, the last releaseYear is usually the main title
            matches = list(re.finditer(r'"releaseYear"\s*(?:\{{"?\$type"?:?"atom",?"?value"?:)?(\d{4})', html))
            if matches:
                year = int(matches[-1].group(1))
                print(f"Found year from last releaseYear match: {year}")
                return year

            # Priority 4: Try pattern: "productionYear": YYYY
            match = re.search(r'"productionYear":\s*(\d{4})', html)
            if match:
                year = int(match.group(1))
                print(f"Found year from productionYear: {year}")
                return year

            # Priority 5: Try meta tags
            match = re.search(r'<meta\s+property="og:title"\s+content="[^"]*\((\d{4})\)"', html)
            if match:
                year = int(match.group(1))
                print(f"Found year from og:title: {year}")
                return year

            # Priority 6: "year" pattern (generic, lower priority because can match currency data)
            # Only use if no other patterns matched
            match = re.search(r'"year":\s*(\d{4})', html)
            if match:
                year = int(match.group(1))
                print(f"Found year from generic year field: {year}")
                return year

            return None
        except Exception as e:
            print(f"Year extraction error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_poster(self, html, title_id=None):
        """Extract poster image URL from HTML

        IMPORTANT NOTE: Priority order is based on RELIABILITY, not speed.
        IMDb is most reliable (Priority 0) because Netflix metadata often points to wrong posters.
        Netflix sources are fallback only (Priority 1-5).
        """
        def decode_url(url_str):
            """Decode escaped characters in URL"""
            url_str = url_str.replace('\\x2F', '/')
            url_str = url_str.replace('\\x3F', '?')
            url_str = url_str.replace('\\x3D', '=')
            url_str = url_str.replace('\\x26', '&')
            return url_str

        # Priority 0: IMDb first (MOST RELIABLE)
        # Netflix sources have proven to be unreliable (e.g., returning wrong posters)
        # Using IMDb web scraping which is more accurate
        print("Trying IMDb poster extraction (Priority 0 - PREFERRED)...")
        imdb_poster = self._fetch_poster_from_tmdb()
        if imdb_poster:
            print(f"Found IMDb poster (Priority 0 - PREFERRED SOURCE)")
            return imdb_poster

        # Priority 1: Look for boxArt with poster dimensions (342w, 500w, 600w)
        # These are specifically sized for poster display
        if title_id:
            poster_dimension_patterns = [
                # boxArt with 342w (standard poster width)
                rf'"{title_id}"[^{{]*{{[^}}]*"boxArt"[^{{]*{{[^}}]*"342w":\s*"([^"]+)"',
                # boxArt with 500w
                rf'"{title_id}"[^{{]*{{[^}}]*"boxArt"[^{{]*{{[^}}]*"500w":\s*"([^"]+)"',
                # boxArt with 600w
                rf'"{title_id}"[^{{]*{{[^}}]*"boxArt"[^{{]*{{[^}}]*"600w":\s*"([^"]+)"',
            ]

            for pattern in poster_dimension_patterns:
                match = re.search(pattern, html)
                if match:
                    url = decode_url(match.group(1))
                    if url and ('nflx' in url.lower() or 'occ-' in url):
                        print(f"Found Netflix boxArt poster with dimensions (Priority 1 - Fallback)")
                        return url

        # Priority 2: Look for generic boxArt with url field
        if title_id:
            box_patterns = [
                # Generic boxArt pattern near title ID
                rf'"{title_id}"[^{{]*{{[^}}]*"boxArt"[^{{]*{{[^}}]*"url":\s*"([^"]+)"',
                # Alternative: look in broader context
                rf'"{title_id}"[^}}]{{0,500}}"boxArt"[^}}]{{0,200}}"url":\s*"([^"]+)"'
            ]

            for pattern in box_patterns:
                match = re.search(pattern, html)
                if match:
                    url = decode_url(match.group(1))
                    if url and ('nflx' in url.lower() or 'occ-' in url):
                        print(f"Found Netflix boxArt poster (Priority 2 - Fallback)")
                        return url

        # Priority 3: Try og:image meta tag (usually the large poster)
        # But validate it's from Netflix CDN
        match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if match:
            url = decode_url(match.group(1))
            # Strict validation: must be from Netflix CDN
            if url and ('nflx' in url.lower() or 'occ-' in url):
                print(f"Found og:image poster (Priority 3 - Fallback)")
                return url

        # Priority 4: Try twitter:image
        match = re.search(r'<meta name="twitter:image" content="([^"]+)"', html)
        if match:
            url = decode_url(match.group(1))
            if url and ('nflx' in url.lower() or 'occ-' in url):
                print(f"Found twitter:image poster (Priority 4 - Fallback)")
                return url

        # Priority 5: Fallback to find any other boxshot or poster URLs in JSON
        patterns = [
            r'"boxshot":\s*"([^"]+)"',
            r'"poster":\s*"([^"]+)"',
            r'"image":\s*"(https://[^"]*nflximg[^"]+)"',
            r'"url":\s*"(https://[^"]*occ-\d+-\d+\.nflxso[^"]+)"'
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                url = decode_url(match.group(1))
                if url and ('nflx' in url.lower() or 'occ-' in url):
                    print(f"Found generic Netflix poster (Priority 5 - Fallback)")
                    return url

        # No poster found from any source
        print("No poster found from any source")
        return None

    def _fetch_poster_from_tmdb(self):
        """
        Fetch poster from IMDb using web scraping.

        This is now the PRIMARY source (Priority 0) for poster extraction
        because Netflix metadata is unreliable and often points to wrong posters.
        Netflix sources are only used as fallback (Priority 1-5).

        Uses year information from Netflix metadata for accurate matching
        when multiple titles with the same name exist on IMDb.
        Also extracts correct year from IMDb if not available from Netflix.

        :return: Poster URL from IMDb or None
        """
        try:
            if not hasattr(self, '_cached_title'):
                return None

            title = self._cached_title
            if not title:
                return None

            # Try to extract year if present in title
            clean_title, year_from_title = extract_year_from_title(title)

            # Use year from Netflix metadata if available, otherwise from title
            year = getattr(self, '_cached_year', None) or year_from_title

            if year:
                print(f"IMDb search: '{clean_title}' ({year})")
            else:
                print(f"IMDb search: '{clean_title}'")

            # Get poster info using enhanced fetcher that also returns year
            poster_info = self.poster_fetcher.get_poster_info(clean_title, year)
            if poster_info:
                poster_url = poster_info.get('poster_url')

                # If IMDb provided a year and we don't have one from Netflix, cache it
                if not year and poster_info.get('year'):
                    imdb_year = poster_info.get('year')
                    print(f"Extracted year {imdb_year} from IMDb")
                    self._cached_year = imdb_year
                    year = imdb_year

                if year:
                    print(f"Found correct poster for '{title}' ({year}) from IMDb")
                else:
                    print(f"Found poster for '{title}' from IMDb")

                return poster_url

            return None
        except Exception as e:
            print(f"IMDb poster fetch failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_from_json(self, html, result, title_id):
        """Extract format info from embedded JSON data"""
        try:
            # Look for the delivery object near the title ID
            # Find all delivery objects and pick the one associated with this title
            delivery_pattern = r'"delivery":\s*\{("has[^}]+)\}'
            matches = re.finditer(delivery_pattern, html)

            for match in matches:
                delivery_str = '{' + match.group(1) + '}'
                try:
                    delivery = json.loads(delivery_str)

                    # Check if this delivery object is near our title ID
                    # Extract context around this match to verify it's for our title
                    match_pos = match.start()
                    context_start = max(0, match_pos - 1000)
                    context = html[context_start:match_pos]

                    # If we find the title ID in the context, this is our delivery object
                    if f'"{title_id}"' in context:
                        # Extract format information from delivery object
                        result['uhd'] = delivery.get('hasUltraHD', False)
                        result['4k'] = result['uhd']
                        result['hd'] = delivery.get('hasHD', False)
                        result['dolby_vision'] = delivery.get('hasDolbyVision', False)
                        result['hdr10'] = delivery.get('hasHDR', False)
                        result['atmos'] = delivery.get('hasDolbyAtmos', False)
                        result['spatial_audio'] = delivery.get('hasAudioSpatial', False)
                        result['dolby_digital'] = delivery.get('has51Audio', False)

                        # SDR (Standard Dynamic Range) and HDR are mutually exclusive
                        # If the title has any HDR format, it should NOT have SDR
                        # If it has no HDR formats, then SDR should be True (default assumption for standard content)
                        has_hdr = result['hdr10'] or result['dolby_vision']
                        if has_hdr:
                            result['sdr'] = False  # HDR means no SDR
                        else:
                            # No HDR detected, so default SDR to True (override Netflix's potentially unreliable hasSD)
                            result['sdr'] = True

                        print(f"Found delivery data: UHD={result['uhd']}, HD={result['hd']}, SDR={result['sdr']}, DV={result['dolby_vision']}, HDR={result['hdr10']}, Atmos={result['atmos']}, Spatial={result['spatial_audio']}, 5.1={result['dolby_digital']}")
                        return True

                except json.JSONDecodeError:
                    continue

            return False

        except Exception as e:
            print(f"JSON extraction error: {e}")
            return False

    def _extract_availability(self, html, result):
        """Extract availability status and coming date from HTML

        Detects if content is currently available or coming soon.
        Updates result dictionary with:
        - is_available: bool
        - availability_status: str (e.g., 'Available', 'Coming Soon')
        - coming_date: str or None (formatted date if coming soon)
        """
        try:
            # Look for "Coming Soon" patterns
            coming_patterns = [
                r'coming\s+soon',
                r'coming\s+([A-Za-z]+\s+\d+)',
                r'join\s+us\s+on\s+(\w+\s+\d+)',
                r'streaming\s+from\s+([A-Za-z]+\s+\d+)',
                r'available\s+([A-Za-z]+\s+\d+)',
                r'arrives?\s+([A-Za-z]+\s+\d+)',
            ]

            html_lower = html.lower()

            # Check for coming soon indicators
            for pattern in coming_patterns:
                match = re.search(pattern, html_lower, re.IGNORECASE)
                if match:
                    result['is_available'] = False
                    result['availability_status'] = 'Coming Soon'

                    # Try to extract the date
                    if len(match.groups()) > 0:
                        result['coming_date'] = match.group(1)
                    else:
                        # Look for date patterns near "coming soon"
                        date_match = re.search(r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})', html[max(0, match.start()-200):match.end()+200])
                        if date_match:
                            result['coming_date'] = date_match.group(1)
                    break

            # Look for "Available" or "Streaming Now" patterns
            if result['is_available']:
                available_patterns = [
                    r'streaming\s+now',
                    r'watch\s+now',
                    r'available\s+now',
                ]

                for pattern in available_patterns:
                    if re.search(pattern, html_lower, re.IGNORECASE):
                        result['is_available'] = True
                        result['availability_status'] = 'Available'
                        break

        except Exception as e:
            print(f"Availability extraction error: {e}")
            # Keep defaults: is_available=True, availability_status='Available'

    def _extract_content_type(self, html, result):
        """Extract content type (Movie vs. TV Series) from HTML

        Updates result dictionary with:
        - is_series: bool (True if TV Series, False if Movie)
        """
        try:
            html_lower = html.lower()

            # Look for series indicators
            series_patterns = [
                r'"type"\s*:\s*"series"',
                r'"isshow"\s*:\s*true',
                r'tvshow',
                r'tv series',
                r'seasons?',
                r'episodes?',
                r'"contenttype"\s*:\s*"series"',
            ]

            # Check for movie indicators (higher priority)
            movie_patterns = [
                r'"type"\s*:\s*"movie"',
                r'"type"\s*:\s*"film"',
                r'"isshow"\s*:\s*false',
                r'"contenttype"\s*:\s*"movie"',
            ]

            # Check movie first
            for pattern in movie_patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    result['is_series'] = False
                    return

            # Then check for series
            for pattern in series_patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    result['is_series'] = True
                    return

            # Default: assume Movie
            result['is_series'] = False

        except Exception as e:
            print(f"Content type extraction error: {e}")
            # Keep default: is_series=False

