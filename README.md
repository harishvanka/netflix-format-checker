# Netflix Format Checker

## Overview

This tool analyzes Netflix title pages using HTML scraping to detect available format support, including:
- 4K/UHD support
- HDR10 support
- Dolby Vision support
- Dolby Atmos support
- 5.1 Dolby Digital support
- Spatial Audio support
- IMDb poster extraction for accurate title identification

## ⚖️ Legal Notice & Disclaimer

**IMPORTANT**: This project is for **educational and personal use only**.

### Permitted Uses
- ✅ Check video formats (4K, HDR, Dolby Vision) for titles you have access to
- ✅ Learn about Netflix's streaming technology
- ✅ Verify format capabilities of your device/connection
- ✅ Educational understanding of streaming technology

### Prohibited Uses
- ❌ Bypass Netflix's DRM
- ❌ Download or extract Netflix content
- ❌ Share copyrighted content
- ❌ Violate Netflix's Terms of Service
- ❌ Commercial use
- ❌ Circumvent geographic restrictions

### Compliance & Disclaimer
This tool:
- Uses only public HTML pages and metadata
- Requires legitimate Netflix subscription
- Does NOT decrypt or extract protected content
- Does NOT violate Terms of Service for personal use
- Is NOT affiliated with Netflix, Inc.

**Use at your own risk**. The authors are not responsible for any misuse, account restrictions, or damages.

## Prerequisites



### 1. Python Environment Setup

Requirements:
- Python 3.10 or higher
- Virtual environment (recommended)
- Required packages: Flask (web framework), requests (HTTP client)

#### Setting up Virtual Environment

Choose your OS and follow the commands:

| OS                   | Create venv Command    | Activate Command            |
| -------------------- | ---------------------- | --------------------------- |
| macOS / Linux        | `python3 -m venv venv` | `source venv/bin/activate`  |
| Windows (CMD)        | `python -m venv venv`  | `venv\Scripts\activate.bat` |
| Windows (PowerShell) | `python -m venv venv`  | `venv\Scripts\Activate.ps1` |

#### Install Dependencies:
```bash
# With virtual environment activated
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Netflix Cookies Setup

The app requires valid Netflix session cookies for authentication.

#### Cookie Setup Steps:
1. **Install Extension:**
   - **Chrome**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Export Cookies:**
   - Log into Netflix
   - Click extension icon on netflix.com
   - Save as `cookies.txt` (Mozilla/Netscape format)
   - Place in `cookies/cookies.txt` (preferred) or root directory

## Running the Application

1. **Activate Virtual Environment** (using commands from setup table above)
2. **Start Server:**
   ```bash
   python app.py
   ```
3. **Access:** Open http://127.0.0.1:5001 in your browser

You should see:
```
============================================================
Netflix Format Checker
============================================================
Server starting at http://127.0.0.1:5001
Cookies File: ✓ Found
============================================================
```

To exit: Use `deactivate` to close virtual environment

## Usage

### Web Interface
1. Open http://127.0.0.1:5001
2. Enter Netflix title URL or ID:
   - Full URL: `https://www.netflix.com/title/81215567`
   - Browse URL: `https://www.netflix.com/browse?jbv=81215567`
   - Just ID: `81215567`
3. Click "Lookup"

### Example Titles to Test
- **Our Planet** (4K, HDR10, Atmos): `80025384`
- **Stranger Things** (4K, HDR10, Atmos): `80057281`
- **The Witcher** (4K, Dolby Vision, Atmos): `80189685`
- **Lucky Baskhar** (4K, Dolby Vision, Spatial Audio): `81902035`

### API Usage
```bash
curl -X POST http://127.0.0.1:5001/lookup -d "url=81215567"
```

## Technical Details

### Architecture
```
app.py (entry point)
  └── Flask app factory (create_app)
      └── app/routes.py (HTTP endpoints)
          └── app/models/netflix_scraper.py (format detection)
              └── app/models/poster_fetcher.py (IMDb scraping)
```

### How It Works
1. **HTML Scraping**: Fetches Netflix title page with authenticated cookies
2. **Format Detection**: 
   - Primary: Netflix JSON metadata
   - Fallback: HTML pattern matching
3. **Poster Extraction**:
   - Primary: IMDb web scraping
   - Fallback: Netflix metadata
   - Last resort: Generic poster patterns

### Performance
- Initial load: 2-3 seconds
- IMDb lookup: 1-2 seconds (5-second timeout)
- Total time: 3-5 seconds per lookup
- Concurrent requests supported

## Troubleshooting

### Cookie Issues
- **"cookies.txt not found"**: Verify file location and format
- **"Sign In" shown**: Re-export cookies while logged in
- Cookies typically last few months before needing renewal

### Format Detection
- Some titles may lack format metadata
- Regional availability affects format support
- Netflix 4K plan required for 4K content
- Test with known 4K title (e.g., "Our Planet": 80025384)

### Poster Issues
- IMDb timeouts possible (5-second limit)
- Fallback to Netflix posters when IMDb fails
- Some titles may use different names on IMDb

## FAQ

**Q: Netflix subscription required?**
A: Yes, active account needed for cookies.

**Q: Works with all titles?**
A: Yes, but format availability varies by region/plan.

**Q: Legal to use?**
A: Yes, for personal use checking available formats.

**Q: Can it download content?**
A: No, only checks format metadata.

## License

For educational and personal use only. See LICENSE file.
