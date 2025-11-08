# Netflix Format Checker

## ⚖️ Legal Notice & Disclaimer

**IMPORTANT**: This project is for **educational and personal use only**.

### Copyright & Terms of Service Compliance

- ✅ **Educational Purpose**: This tool is designed for learning about Netflix's streaming format capabilities
- ✅ **Personal Use Only**: Use only to check format availability for titles in your own Netflix account
- ✅ **No Content Distribution**: This tool does NOT download, decrypt, or distribute any Netflix content
- ✅ **Metadata Only**: This tool only inspects publicly available metadata and format information
- ✅ **Public Information**: Format information (4K, HDR, Dolby Vision, etc.) is publicly displayed on Netflix's website

### What You CAN Do

- ✅ Check what video formats (4K, HDR, Dolby Vision) are available for titles you have access to
- ✅ Learn how Netflix encodes and streams different video formats
- ✅ Educational understanding of streaming technology
- ✅ Personal use to verify format capabilities of your internet connection/device

### What You CANNOT Do

- ❌ Do NOT use this tool to bypass Netflix's DRM (Digital Rights Management)
- ❌ Do NOT download or extract any Netflix video content
- ❌ Do NOT distribute or share copyrighted Netflix content
- ❌ Do NOT violate Netflix's Terms of Service
- ❌ Do NOT use this for commercial purposes
- ❌ Do NOT use this to circumvent Netflix's geographic restrictions

### Compliance Statement

This tool:
- **Does NOT** violate Netflix's Terms of Service for personal, non-commercial use
- **Does NOT** access Netflix's proprietary APIs (uses public HTML pages only)
- **Does NOT** decrypt or extract protected content
- **Only** analyzes publicly available metadata
- **Respects** all copyright and intellectual property laws
- **Requires** you to be a legitimate Netflix subscriber with valid login credentials

### Disclaimer

**Use at your own risk**. The authors of this tool are not responsible for:
- Any violation of Netflix's Terms of Service
- Any legal issues arising from misuse of this tool
- Bans or account restrictions from Netflix
- Any damages or losses caused by this tool

Netflix is a trademark of Netflix, Inc. This project is not affiliated with, endorsed by, or approved by Netflix, Inc.

---

**By using this tool, you agree to use it only for legitimate educational and personal purposes in compliance with all applicable laws and Netflix's Terms of Service.**

---

## Quick Start (5 Minutes)

Want to get running quickly? Skip to **Installation** section below, then **Running the Application**.

---

## Overview

This tool analyzes Netflix title pages using HTML scraping to detect available format support, including:
- 4K/UHD support
- HDR10 support
- Dolby Vision support
- Dolby Atmos support
- 5.1 Dolby Digital support
- Spatial Audio support
- IMDb poster extraction for accurate title identification

## Prerequisites

### 1. Python Environment Setup

It's recommended to use a virtual environment to avoid conflicts with system Python packages.

#### Create Virtual Environment:

```bash
# Navigate to the project directory
cd /path/to/netflix-format-checker

# Create a virtual environment(MacOs/Linux)
python3 -m venv venv

# Create a virtual environment(Windows)
python -m venv venv
```

#### Activate Virtual Environment - Choose Your OS:

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

#### Verify Activation:

After running the activation command, your terminal prompt should show `(venv)` prefix:
```
(venv) username@macbook netflix-format-checker %     # macOS/Linux
(venv) C:\path\to\netflix-format-checker>             # Windows
```

#### Install Dependencies:

```bash
# Make sure virtual environment is activated (you should see (venv) in prompt)
pip install --upgrade pip
pip install -r requirements.txt
```

Required packages (see requirements.txt):
- **Flask** (web framework)
- **requests** (HTTP client for Netflix & IMDb)

#### Deactivate Virtual Environment (when done):

```bash
# To exit the virtual environment
deactivate
```

### 2. Netflix Cookies

You need valid Netflix session cookies for authentication. The app uses HTML scraping, which requires an authenticated Netflix session.

#### How to Get Cookies:

1. **Install a cookie exporter extension:**
   - **Chrome**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Log into Netflix** in your browser

3. **Export cookies:**
   - Click the extension icon while on netflix.com
   - Export/Save as `cookies.txt`
   - Use **Mozilla/Netscape format** (not JSON)

4. **Place cookies.txt** in the project directory:
   - **Recommended**: `cookies/cookies.txt` (supports multiple versions)
   - **Alternative**: `cookies.txt` (in root directory, for backward compatibility)

#### Cookie File Location:

The app checks for cookies in this order:
1. `cookies/cookies.txt` (preferred location)
2. `cookies.txt` (root directory, fallback)

## Installation

### Complete Setup Steps (macOS/Linux):

```bash
# 1. Clone/download the project
cd /path/to/netflix-format-checker

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Export Netflix cookies
# Use browser extension to export cookies.txt
# Place in cookies/cookies.txt or root cookies.txt

# 6. Verify setup
ls -la cookies/cookies.txt  # or cookies.txt
```

### Complete Setup Steps (Windows):

```bash
# 1. Navigate to project directory
cd C:\path\to\netflix-format-checker

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Export Netflix cookies using browser extension
# Place cookies.txt in project root or cookies/ folder

# 6. Verify setup
dir cookies.txt
```

## Running the Application

### Start the server:

**Step 1: Activate Virtual Environment**

macOS/Linux:
```bash
source venv/bin/activate
```

Windows (Command Prompt):
```bash
venv\Scripts\activate
```

Windows (PowerShell):
```powershell
venv\Scripts\Activate.ps1
```

**Step 2: Run Application**

```bash
python app.py
```

The server will start on **http://127.0.0.1:5001**

### Check startup output:

When starting, you'll see:
```
============================================================
Netflix Format Checker
============================================================

Server starting at http://127.0.0.1:5001
Cookies File: ✓ Found

============================================================
```

If you see warnings about missing cookies, check your configuration.

## Usage

### Web Interface:

1. Open http://127.0.0.1:5001 in your browser
2. Enter a Netflix title URL or ID:
   - Full URL: `https://www.netflix.com/title/81215567`
   - Browse URL: `https://www.netflix.com/browse?jbv=81215567`
   - Just the ID: `81215567`
3. Click "Lookup"
4. View the format information and poster

### Example Title IDs to Test:

- **Our Planet** (4K, HDR10, Atmos): `80025384`
- **Stranger Things** (4K, HDR10, Atmos): `80057281`
- **The Witcher** (4K, Dolby Vision, Atmos): `80189685`
- **Lucky Baskhar** (4K, Dolby Vision, Spatial Audio): `81902035`

### API Endpoint:

```bash
curl -X POST http://127.0.0.1:5001/lookup \
  -d "url=81215567"
```

## Troubleshooting

### "cookies.txt not found"

- Export cookies while logged into Netflix
- Save as `cookies.txt` in the project directory
- Or place in `cookies/cookies.txt` folder
- Use Mozilla/Netscape format (not JSON)
- Make sure you're logged into Netflix when exporting

### "Sign In" page shown (not logged in)

- Cookies may be expired - re-export them
- Make sure you exported while logged into Netflix
- Check that NetflixId and SecureNetflixId are in the cookies

### No format information found

- Some titles may not have format metadata
- Title may not have 4K/HDR/Dolby support in your region
- Try a known supported title like "Our Planet" (80025384)
- Check that your Netflix account has the 4K plan

### Poster not showing

- IMDb web scraping may timeout (5-second limit)
- Some titles may not have posters on IMDb
- The title may use a non-standard name on IMDb
- App uses Netflix poster as fallback

### "Could not extract a Netflix title ID"

- Make sure you entered a valid Netflix URL or title ID
- Supported formats:
  - `https://www.netflix.com/title/81215567`
  - `https://www.netflix.com/browse?jbv=81215567`
  - `81215567` (just the ID)

## Technical Details

### How It Works:

1. **HTML Scraping**: Fetches the Netflix title page using authenticated cookies
2. **Format Detection**: Searches Netflix's embedded JSON metadata for format capabilities
3. **Pattern Matching**: Falls back to keyword matching for additional audio formats
4. **Poster Extraction**:
   - First tries IMDb web scraping (most reliable)
   - Falls back to Netflix metadata if IMDb unavailable
5. **Year-Based Matching**: Uses title year to disambiguate duplicate titles on IMDb

### Architecture:

```
app.py (entry point)
  └── Flask app factory (create_app)
      └── app/routes.py (HTTP endpoints)
          └── app/models/netflix_scraper.py (format detection)
              └── app/models/poster_fetcher.py (IMDb scraping)
```

### Detection Priority:

**Format Detection:**
1. Netflix delivery object (JSON metadata) - MOST RELIABLE
2. Pattern matching in HTML - FALLBACK

**Poster Extraction:**
1. IMDb web scraping - MOST RELIABLE
2. Netflix metadata - FALLBACK
3. Generic poster patterns - LAST RESORT

## Supported URL Formats

The app supports multiple Netflix URL formats:

```
https://www.netflix.com/title/81215567
https://www.netflix.com/browse?jbv=81215567
https://www.netflix.com/watch/81215567
https://www.netflix.com/latest/81215567
81215567 (bare ID)
```

## Performance Considerations

- **Startup Time**: 2-3 seconds (Netflix page fetch + parsing)
- **IMDb Lookup**: 1-2 seconds (with 5-second timeout)
- **Total Time**: Typically 3-5 seconds per lookup
- **Concurrent Requests**: Supported (Flask threaded mode)

## Support

### Frequently Asked Questions:

**Q: Do I need a Netflix subscription?**
A: Yes, you need an active Netflix account with valid session cookies.

**Q: Does this work with all Netflix titles?**
A: It works with titles available in your region. Format availability depends on your account tier (4K plan required for 4K content).

**Q: Is this legal?**
A: Checking metadata for content you have access to is generally acceptable for personal use. However, be aware of Netflix's Terms of Service.

**Q: Can I use this to download Netflix content?**
A: No, this tool only checks format information. It does not download or decrypt any video content.

**Q: Why do I get "not logged in" error?**
A: Your cookies may be expired. Re-export cookies while logged into Netflix.

**Q: How often do I need to update cookies?**
A: Cookies typically last a few months. If you get "not logged in" errors, re-export them.

## License

For educational and personal use only. See LICENSE file for details.
