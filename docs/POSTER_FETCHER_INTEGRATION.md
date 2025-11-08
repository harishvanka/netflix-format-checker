# Poster Fetcher Integration Guide

## Overview

The Netflix Format Checker now includes robust poster image fetching with a 5-tier fallback strategy, ensuring users always see movie/TV show posters when available.

## Problem Statement

The original poster extraction from Netflix's HTML and embedded JSON metadata was unreliable:
- Netflix's boxArt JSON might be missing or not match the display poster
- og:image meta tag sometimes pointed to non-poster images
- Some titles had no readily available poster URLs in Netflix's page markup

## Solution: Multi-Tier Fallback Strategy

### Extraction Tiers (in order of priority)

1. **Netflix JSON - Title-Specific boxArt (342w)**
   - Most accurate, extracted from embedded JSON delivery data
   - Contains dimensions (342w) optimized for poster display

2. **Netflix JSON - Generic boxArt**
   - Fallback JSON extraction with flexible pattern matching

3. **og:image Meta Tag**
   - Open Graph image metadata from Netflix page
   - High quality, intended for social media sharing

4. **twitter:image Meta Tag**
   - Twitter card image metadata
   - Reliable alternative meta tag

5. **IMDb Web Scraping** ← **NEW: poster_fetcher.py**
   - IMDb search to find the title
   - Extract Amazon CDN poster URL from IMDb title page
   - Works for any movie/TV show with IMDb entry
   - No API key required

## Implementation Details

### New Files

#### `poster_fetcher.py` (150+ lines)
```python
class PosterFetcher:
    """Fetch movie/TV show posters from IMDb"""

    def fetch_poster(title: str, year: Optional[int] = None) -> Optional[str]
    def _fetch_from_imdb(title: str, year: Optional[int] = None) -> Optional[str]
    def get_poster_info(title: str, year: Optional[int] = None) -> dict
```

**Key Features:**
- No API key required
- Handles year extraction from titles: "Avatar (2009)" → searches with year
- Returns Amazon CDN URLs from IMDb's image hosting
- Graceful error handling and logging

### Integration Points

#### `netflix_scraper.py` Changes:
1. Import: `from poster_fetcher import PosterFetcher, extract_year_from_title`
2. Init: `self.poster_fetcher = PosterFetcher()`
3. New method: `_fetch_poster_from_tmdb()` (name kept for historical reasons)
   - Caches title during extraction
   - Calls fetcher with title and year
   - Returns IMDb poster URL as fallback
4. Updated: `_extract_poster()` calls IMDb fallback as Priority 5
5. Updated: Title extraction caches title for IMDb lookup: `self._cached_title = decoded`

#### `app_simple.py` Changes:
- No changes needed! Poster_fetcher is handled transparently by netflix_scraper.py

#### `requirements.txt` Changes:
- Added documentation comments about TMDB (for future reference)
- No new package dependencies (uses existing `requests` library)

## How It Works

### User Flow
```
User enters title ID → app_simple.py → netflix_scraper.check_formats()
  ↓
Extract title name from Netflix page
  ↓
Extract poster (5-tier strategy):
  1. Try Netflix boxArt (JSON)
  2. Try og:image meta
  3. Try twitter:image meta
  4. Try generic boxArt patterns
  5. If all fail, call poster_fetcher.fetch_poster(title)
     → Search IMDb
     → Extract Amazon CDN poster URL
  ↓
Return poster URL (or None)
  ↓
Display in result.html
```

### Example IMDb Extraction
```
Input: "The Witcher"
  ↓
Search IMDb: https://www.imdb.com/find?q=The+Witcher&s=tt
  ↓
Extract IMDb ID: tt5180504
  ↓
Fetch: https://www.imdb.com/title/tt5180504/
  ↓
Extract Amazon image URL from page
  ↓
Return: https://m.media-amazon.com/images/M/MV5BOTQzMzNmMzUtODgwNS00...
```

## Testing

### Manual Test
```bash
python3 test_poster_fetcher.py
```

Output shows successful poster fetching for:
- The Witcher
- Stranger Things
- Our Planet
- Breaking Bad
- The Crown
- Avatar (with year)
- Inception

### Testing with Netflix App
1. Start the app: `python app_simple.py`
2. Search for a Netflix title that had poster issues
3. Verify the correct poster displays (from IMDb fallback)

## Performance Considerations

- **IMDb fallback only triggers** if Netflix extraction fails (no unnecessary overhead)
- **Timeout**: 5 seconds per IMDb request (configurable in PosterFetcher init)
- **No caching**: Each lookup is fresh (could be enhanced with caching later)
- **Graceful degradation**: If IMDb fails, show no poster (not an error)

## Limitations & Future Enhancements

### Current Limitations
1. **IMDb title matching** relies on first search result (could match wrong year)
   - Mitigation: Extract year from title when available
2. **No image caching** - fetches fresh on each lookup
3. **Single source fallback** - could add more sources

### Potential Future Enhancements
1. Add TVDB (The TV Database) as additional source
2. Implement response caching (Redis or file-based)
3. Better title matching with fuzzy search
4. Support for multiple years (show alternatives)
5. Direct TMDB API integration with user's own API key
6. Cache Amazon image URLs in database

## Security Notes

- **No sensitive data** involved (poster URLs are public)
- **Browser-like headers** to avoid blocking by IMDb
- **Timeouts** prevent hanging requests
- **No credentials** stored or transmitted
- **Amazon CDN URLs** are static, immutable resources

## Troubleshooting

### "No poster found" for a known title
- Title might not be in IMDb
- Netflix might have removed the title
- Try searching IMDb manually: https://www.imdb.com/find?q=YourTitle

### Slow poster loading
- Check network connectivity
- IMDb might be rate-limited (rare)
- Verify timeout setting in poster_fetcher.py (default 5s)

### Wrong poster displayed
- IMDb search returned wrong year
- Include year in title: "Movie Name (2020)"
- Check Netflix directly for correct poster

## API Reference

### PosterFetcher Class

```python
fetcher = PosterFetcher(timeout=5)

# Fetch poster URL
url = fetcher.fetch_poster("The Witcher")
url = fetcher.fetch_poster("Avatar", year=2009)

# Get detailed info
info = fetcher.get_poster_info("Inception")
# Returns: {'poster_url': '...', 'title': '...', 'source': 'imdb'}
```

### extract_year_from_title Function

```python
from poster_fetcher import extract_year_from_title

title, year = extract_year_from_title("Avatar (2009)")
# Returns: ("Avatar", 2009)

title, year = extract_year_from_title("The Crown")
# Returns: ("The Crown", None)
```

## Contributing

When modifying poster fetcher:
1. Ensure timeout prevents hanging
2. Add logging for debugging
3. Maintain graceful error handling
4. Test with diverse titles
5. Update CLAUDE.md documentation

## References

- IMDb Search: https://www.imdb.com/find
- Amazon Image CDN: https://m.media-amazon.com/images/
- Web Scraping Ethics: Respect robots.txt and rate limits
