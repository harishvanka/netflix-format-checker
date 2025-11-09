"""
Poster Fetcher
Fetches movie/TV show posters from various open-source APIs
Uses web scraping from IMDb and fallbacks for poster extraction
Provides fallback mechanism for failed Netflix poster extraction
"""

import requests
import logging
from typing import Optional
import re
from urllib.parse import quote

logger = logging.getLogger("PosterFetcher")


class PosterFetcher:
    """Fetch movie/TV show posters from various sources"""

    def __init__(self, timeout=5):
        """
        Initialize poster fetcher

        :param timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_poster(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """
        Fetch poster URL for given title using multiple sources

        :param title: Movie/TV show title
        :param year: Optional release year for better matching
        :return: Full poster URL or None if not found
        """
        if not title or not title.strip():
            logger.debug("Empty title provided")
            return None

        try:
            # Try IMDb first (more reliable)
            poster_url = self._fetch_from_imdb(title, year)
            if poster_url:
                logger.info(f"Found poster for '{title}' from IMDb")
                return poster_url

            logger.debug(f"Could not find poster for '{title}' in any source")
            return None

        except Exception as e:
            logger.warning(f"Poster fetch failed for '{title}': {e}")
            return None

    def _fetch_from_imdb(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """
        Fetch poster from IMDb using IMDb search with year filtering

        :param title: Movie/TV show title
        :param year: Optional release year (for accurate matching when multiple titles exist)
        :return: Poster URL or None
        """
        try:
            # Build search query
            query = title
            if year:
                query = f"{title} {year}"

            # Use IMDb search URL
            search_url = f"https://www.imdb.com/find?q={quote(query)}&s=tt"

            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()

            # Extract IMDb IDs and years from search results
            # Look for pattern: /title/(tt\d+)/ with year info
            if year:
                # When year is provided, try to find matching result with that year
                imdb_id = self._find_matching_result_by_year(response.text, year)
                if not imdb_id:
                    # Fallback: use first result if year-specific match not found
                    match = re.search(r'/title/(tt\d+)/', response.text)
                    if match:
                        imdb_id = match.group(1)
                    else:
                        return None
            else:
                # No year provided, use first result
                match = re.search(r'/title/(tt\d+)/', response.text)
                if match:
                    imdb_id = match.group(1)
                else:
                    return None

            # Get the title page which has poster image
            title_url = f"https://www.imdb.com/title/{imdb_id}/"

            title_response = self.session.get(title_url, timeout=self.timeout)
            title_response.raise_for_status()

            # Look for poster image URL in the page
            # IMDb typically has images in format: https://m.media-amazon.com/images/...
            poster_match = re.search(
                r'"image"\s*:\s*\{"url"\s*:\s*"([^"]*amazon[^"]*\.jpg)',
                title_response.text
            )
            if poster_match:
                poster_url = poster_match.group(1)
                # Fix escaped characters
                poster_url = poster_url.replace('\\/', '/')
                logger.info(f"Found poster for '{title}' (IMDb ID: {imdb_id})")
                return poster_url

            # Fallback: look for any Amazon image
            amazon_match = re.search(
                r'https://m\.media-amazon\.com/images/[^"]*\.jpg',
                title_response.text
            )
            if amazon_match:
                logger.info(f"Found poster for '{title}' using fallback pattern (IMDb ID: {imdb_id})")
                return amazon_match.group(0)

            return None

        except Exception as e:
            logger.debug(f"IMDb search failed: {e}")
            return None

    def _extract_year_from_imdb(self, title: str, year: Optional[int] = None) -> Optional[int]:
        """
        Extract release year from IMDb title page

        :param title: Movie/TV show title
        :param year: Optional hint year (not used in extraction, only for searching)
        :return: Release year or None
        """
        try:
            # Build search query
            query = title
            if year:
                query = f"{title} {year}"

            # Use IMDb search URL
            search_url = f"https://www.imdb.com/find?q={quote(query)}&s=tt"

            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()

            # Get first IMDb result
            match = re.search(r'/title/(tt\d+)/', response.text)
            if not match:
                return None

            imdb_id = match.group(1)

            # Fetch the title page
            title_url = f"https://www.imdb.com/title/{imdb_id}/"
            title_response = self.session.get(title_url, timeout=self.timeout)
            title_response.raise_for_status()

            # Try multiple patterns to extract year
            patterns = [
                r'"releaseYear"\s*:\s*(\d{4})',
                r'"datePublished"\s*:\s*"(\d{4})',
                r'"birthDate"\s*:\s*"(\d{4})',
                r'<span>(\d{4})</span>',
            ]

            for pattern in patterns:
                year_match = re.search(pattern, title_response.text)
                if year_match:
                    extracted_year = int(year_match.group(1))
                    # Filter unrealistic years (prevent matching years like 1918 from currency data)
                    if 1900 <= extracted_year <= 2100:
                        logger.debug(f"Extracted year {extracted_year} from IMDb for '{title}'")
                        return extracted_year

            return None

        except Exception as e:
            logger.debug(f"IMDb year extraction failed: {e}")
            return None

    def _find_matching_result_by_year(self, search_html: str, year: int) -> Optional[str]:
        r"""
        Find IMDb ID from search results that matches the given year

        :param search_html: HTML content from IMDb search results
        :param year: Release year to match
        :return: IMDb ID (tt\d+) if found, None otherwise
        """
        try:
            # Pattern to extract IMDb IDs with year information from search results
            # Look for patterns like: /title/(tt\d+).*?(\d{4})'
            # This pattern finds title links followed by year in search results

            # Extract all title links with context around them
            pattern = r'/title/(tt\d+)/[^>]*>([^<]+)</a>\s*\((\d{4})\)'
            matches = re.finditer(pattern, search_html)

            for match in matches:
                imdb_id = match.group(1)
                result_year = int(match.group(3))

                # Match if year is exact or within 1 year (accounting for release date variations)
                if result_year == year or abs(result_year - year) <= 1:
                    logger.debug(f"Found matching IMDb ID {imdb_id} for year {year}")
                    return imdb_id

            logger.debug(f"No exact year match found for year {year}")
            return None

        except Exception as e:
            logger.debug(f"Year matching failed: {e}")
            return None

    def get_poster_info(self, title: str, year: Optional[int] = None) -> dict:
        """
        Get detailed poster information including year extraction from IMDb

        :param title: Movie/TV show title
        :param year: Optional release year
        :return: Dictionary with poster info (url, title, year, source) or empty dict
        """
        try:
            poster_url = self.fetch_poster(title, year)
            if poster_url:
                # Try to extract year from IMDb page if not provided
                extracted_year = year
                if not extracted_year:
                    extracted_year = self._extract_year_from_imdb(title, year)

                return {
                    'poster_url': poster_url,
                    'title': title,
                    'year': extracted_year,
                    'source': 'imdb'
                }
            return {}
        except Exception as e:
            logger.warning(f"Poster info fetch failed: {e}")
            return {}


def extract_year_from_title(title: str) -> tuple:
    """
    Extract year from title if present (e.g., "Movie Title (2024)")

    :param title: Title string
    :return: Tuple of (cleaned_title, year) or (title, None)
    """
    import re

    match = re.search(r'\((\d{4})\)$', title.strip())
    if match:
        year = int(match.group(1))
        clean_title = title[:match.start()].strip()
        return clean_title, year

    return title, None
