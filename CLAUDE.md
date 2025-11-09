# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Latest Session Update (November 9, 2025 - SDR Logic Fix)

✅ **APPLICATION STATUS: PRODUCTION READY**

Recent improvements completed:
- Fixed SDR (Standard Dynamic Range) logic to be mutually exclusive with HDR
  - When HDR10 or Dolby Vision detected: SDR = False
  - When no HDR formats detected: SDR = True (default for standard content)
  - Applied fix to both JSON extraction path and fallback text pattern matching path
  - Verified with test cases: Telusu Kada (SDR=True), The Witcher (SDR=False)
- Fixed syntax warning in poster_fetcher.py (docstring raw string)
- Verified all features working correctly:
  - Year extraction for collections (Don 2022 issue fixed)
  - IMDb year-based poster search (±1 year tolerance)
  - UI displays Release Year in metadata section
  - Blueprint routing fixed (main.* endpoints)
  - Audio format detection working (5.1 Dolby, Spatial Audio)
- All Python files compile without errors
- All Flask routes tested and working (GET /, GET /health, POST /lookup)
- Created documentation: docs/APP_STATUS.md, docs/SESSION_COMPLETION.md

**Status**: All features tested and working correctly

---

## Project Overview

**Netflix Format Checker** - A Flask web application that checks Netflix title format capabilities (4K, HDR, Dolby Vision, Dolby Atmos) using simple HTML scraping from Netflix title pages.

### Key Technologies
- **Backend**: Flask 3.0.0, Python 3.12
- **Encryption**: pycryptodomex (RSA-2048, AES-256-CBC, HMAC-SHA256)
- **HTTP**: requests library
- **Frontend**: HTML templates with CSS

## Architecture

### Core Components

1. **[app_simple.py](app_simple.py)** (198 lines) - **ACTIVE APPLICATION**
   - Flask web application with simple HTML scraping approach
   - Routes: `GET /` (index), `POST /lookup` (format check), `GET /health` (status)
   - Loads Netflix cookies from `cookies.txt`
   - Displays poster images and format support with resolution classification
   - No external dependencies beyond requests library

2. **[netflix_scraper.py](netflix_scraper.py)** (320+ lines)
   - Pure HTML scraping of Netflix title pages (no API calls needed)
   - Extracts title name and poster image from page metadata
   - 5-tier poster extraction strategy:
     1. Title-specific boxArt from JSON
     2. og:image meta tag
     3. twitter:image meta tag
     4. Generic boxArt/poster patterns
     5. **IMDb fallback** for reliable poster images
   - JSON extraction for delivery object with format capabilities
   - Fallback text pattern matching for format detection
   - Methods: `check_formats()`, `_extract_title()`, `_extract_poster()`, `_extract_from_json()`, `_detect_audio_formats()`, `_fetch_poster_from_tmdb()`

3. **[poster_fetcher.py](poster_fetcher.py)** (150+ lines) - *NEW*
   - Fetches movie/TV show posters from IMDb as fallback source
   - Uses IMDb search and web scraping (no API key required)
   - Extracts Amazon CDN image URLs from IMDb title pages
   - Methods: `fetch_poster()`, `_fetch_from_imdb()`, `get_poster_info()`
   - Utility: `extract_year_from_title()` for year extraction from titles

4. **[netflix_msl.py](netflix_msl.py)** (518 lines) - *Alternative/Advanced*
   - Implements Netflix MSL protocol for authenticated manifest requests
   - Handles RSA-2048 key exchange, AES-256-CBC encryption, HMAC-SHA256 signing
   - Manages 10-hour MSL key caching in `.cache/msl_keys.json`
   - Used by app_msl.py for more detailed format data

5. **[format_detector.py](format_detector.py)** (360 lines) - *Alternative/Advanced*
   - Parses DASH manifests from MSL API responses
   - Detects video formats, audio formats, codecs
   - Resolution classification: UHD (4K), QHD (1440p), FHD (1080p), HD (720p), SD (480p)
   - Used by app_msl.py and NetflixService

### Data Flow (Simple Scraping - Active)

```
User Input (title ID/URL)
    ↓
app_simple.py validates & extracts title ID
    ↓
netflix_scraper.py fetches Netflix title page
    ↓
Scraper extracts:
  1. Title & poster from metadata tags
  2. Format data from embedded JSON delivery object
  3. Fallback: text pattern matching if JSON unavailable
    ↓
Scraper returns detection results
  - title, poster URL
  - dolby_vision, hdr10, atmos, uhd (4K)
    ↓
app_simple.py renders result.html with format info
```

### Data Flow (Advanced MSL - Alternative)

```
User Input (title ID/URL)
    ↓
app_msl.py validates & extracts ID
    ↓
NetflixService loads cookies & calls netflix_msl.py
    ↓
netflix_msl.py performs MSL authentication & requests manifest
    ↓
format_detector.py parses manifest, classifies resolution
    ↓
Returns detailed format analysis with track information
```

## Setup & Running

### Initial Setup (Simple Scraping Approach - Recommended)
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Export Netflix cookies (while logged in)
# Use browser extension: "Get cookies.txt LOCALLY" (Chrome) or "cookies.txt" (Firefox)
# Save to cookies.txt in project root
```

### Run Application (Simple)
```bash
source venv/bin/activate
python app_simple.py
# Opens on http://127.0.0.1:5001
```

### Advanced Setup (MSL API Approach - Optional)
If you prefer more detailed format information:
```bash
# 3. Configure ESN (from browser dev tools Network tab)
cp config.example.py config.py
# Edit config.py and add your Netflix ESN: NFCDCH-02-...

# 4. Run advanced version
python app_msl.py
```

### Test Titles for Verification
- **Our Planet** (80025384): 4K, HDR10, Atmos
- **Stranger Things** (80057281): 4K, HDR10, Atmos
- **The Witcher** (80189685): 4K, Dolby Vision, Atmos
- **6 Underground** (81001887): 4K, Dolby Vision, Atmos

## Development Commands

### Common Tasks
```bash
# Activate virtual environment (always first)
source venv/bin/activate

# Run simple scraping app (recommended)
python app_simple.py

# Run advanced MSL-based app
python app_msl.py

# Check if app is running
curl http://127.0.0.1:5001/health

# Test a title via API
curl -X POST http://127.0.0.1:5001/lookup -d "url=80025384"

# Re-export cookies (use while logged into Netflix)
# Then use browser extension: "Get cookies.txt LOCALLY" (Chrome) or "cookies.txt" (Firefox)

# Clear MSL key cache (only needed for app_msl.py)
rm -rf .cache/msl_keys.json && python app_msl.py

# Upgrade dependencies
pip install --upgrade -r requirements.txt

# Reset virtual environment (if experiencing issues)
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

### `cookies.txt` (Required - Not in Git)
- Mozilla/Netscape format (exported from browser extension)
- Must be logged into Netflix when exporting
- Auto-loaded on app startup for both simple and MSL versions
- Export using: "Get cookies.txt LOCALLY" (Chrome) or "cookies.txt" (Firefox)

### `config.py` (Optional - Only for MSL version)
```python
NETFLIX_ESN = "NFCDCH-02-YOUR_ACTUAL_ESN"
```
- Only needed if running app_msl.py
- ESN obtained from Netflix browser dev tools (Network tab → MSL request → Payload)
- Can also be set via environment variable: `export NETFLIX_ESN="..."`

### `.cache/msl_keys.json` (Auto-generated - MSL version only)
- Caches MSL encryption keys for 10 hours
- Only created when using app_msl.py
- Safe to delete if experiencing authentication issues

## Important Files

### Active Application Files
- **app_simple.py** - Main Flask application (HTML scraping approach)
- **netflix_scraper.py** - HTML scraping and format detection logic
- **poster_fetcher.py** - IMDb-based poster image fetching (fallback source)

### Advanced/Alternative Application Files
- **app_msl.py** - Advanced Flask application (MSL API approach)
- **netflix_service.py** - Service wrapper for MSL approach
- **netflix_msl.py** - MSL protocol implementation
- **format_detector.py** - DASH manifest parsing and format detection

### Legacy Files (Reference/Testing Only)
- **app_old.py** - Original implementation (deprecated)
- **netflix_simple.py** - Simplified fetch logic
- **check.py** - CLI utility (minimal)

### UI Files
- **templates/index.html** - Web form for title lookup
- **templates/result.html** - Format detection results page with logo, poster, resolution classification, and detailed format breakdown
- **static/style.css** - Modern glass-morphism styling with dark mode, responsive design, and animations

### Documentation
- **README.md** - Basic overview
- **QUICK_START.md** - 3-minute setup guide
- **SETUP.md** - Comprehensive setup & troubleshooting
- **README_MSL.md** - MSL architecture details
- **IMPLEMENTATION_GUIDE.md** - Original implementation notes
- **IMPLEMENTATION_SUMMARY.md** - Summary of MSL approach

## Key Design Decisions

1. **Simple Scraping Over Complex APIs**: `app_simple.py` uses HTML scraping which requires only cookies (no ESN setup). Simpler to deploy and use for most users.

2. **Dual Approach**: Keep both simple (app_simple.py) and advanced (app_msl.py) versions available. Users choose based on needs:
   - Simple: Quick setup, fewer dependencies, basic format info
   - Advanced: More detailed format data, codec info, resolution details

3. **JSON-First Detection**: In netflix_scraper.py, prioritize extracting data from embedded JSON (delivery objects) before falling back to text pattern matching. JSON is more reliable.

4. **Multi-Tier Poster Extraction**: Implement 5-tier fallback strategy for poster images:
   - Priority 1-4: Netflix sources (JSON boxArt, og:image, twitter:image, generic patterns)
   - Priority 5: IMDb web scraping via `poster_fetcher.py` when Netflix extraction fails
   - IMDb approach requires no API keys and retrieves Amazon CDN URLs reliably
   - Ensures users always see a poster image when available

5. **SDR/HDR Mutual Exclusivity**: SDR (Standard Dynamic Range) and HDR are mutually exclusive - content is in either SDR or HDR format, never both:
   - If HDR10 OR Dolby Vision detected → SDR = False
   - If NO HDR formats detected → SDR = True (default for standard content)
   - Applied in both JSON extraction and fallback text pattern matching paths
   - Ensures logically correct format representation

6. **Resolution Classification**: Convert raw resolutions (3840x2160) to user-friendly labels (UHD/4K) based on height thresholds. Classification supports UHD (≥2160p), QHD (≥1440p), FHD (≥1080p), HD (≥720p), and SD (≥480p).

7. **Cookie-Based Authentication**: Both apps use Netflix cookies for authentication. No need for complex OAuth or API keys—just login in browser and export cookies.

8. **MSL Protocol (Advanced)**: For `app_msl.py`, implement MSL with RSA key exchange and AES encryption for authenticated manifest requests. Cache keys 10 hours to reduce overhead.

## Troubleshooting

### MSL Handshake Failed
- Verify ESN format: `NFCDCH-02-...` (not generic or invalid)
- Re-export cookies while logged into Netflix
- Clear cache: `rm -rf .cache/msl_keys.json`

### "No Netflix authentication cookies found"
- Ensure logged into Netflix when exporting cookies
- Use browser extension: "Get cookies.txt LOCALLY" (Chrome) or "cookies.txt" (Firefox)
- Save in Mozilla/Netscape format (not JSON)
- Verify `cookies.txt` exists in project root

### No Format Information Returned
- Title may not have 4K available in your region
- Account may need 4K subscription tier
- Try known 4K title: `80025384` (Our Planet)

### Virtual Environment Issues
- `deactivate` current venv, then: `rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

## Maintaining CLAUDE.md

**This file should be updated whenever features are added, removed, or significantly modified.**

### When Adding a Feature
1. Update the **Architecture** section if a new core component is created
2. Update **Important Files** section if new files are added
3. Update **Data Flow** diagram if processing changes
4. Add new **Development Commands** if there are new common tasks
5. Update **Key Design Decisions** if architectural choices are made

### When Removing a Feature
1. Remove from **Architecture** or **Important Files** sections
2. Remove or update affected **Data Flow** sections
3. Remove related **Development Commands** if obsolete
4. Remove deprecated **Key Design Decisions** if applicable

### When Modifying Existing Features
1. Update **Core Components** descriptions if functionality changes
2. Update **Data Flow** if request handling changes
3. Update **Setup & Running** section if new configuration steps are needed
4. Update **Development Commands** if execution steps change
5. Update **Troubleshooting** if new issues arise

### File Structure Guidelines
- Keep component descriptions to 3-4 bullet points max
- Always include file path as a link: `**[filename.py](filename.py)**`
- Update line counts when files are significantly modified (optional but helpful)
- Maintain the distinction between "active" components and "reference only" files
- Keep the data flow diagram as ASCII art for easy readability without rendering

## Security Notes

- **Sensitive Files**: `config.py`, `cookies.txt`, `.cache/msl_keys.json` are in `.gitignore` - never commit these
- **Legal Use**: Tool is for personal use checking metadata only. Does not download or decrypt video content
- **Cookie Security**: Cookies are session tokens; keep `cookies.txt` private and safe
