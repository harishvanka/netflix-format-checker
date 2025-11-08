# Netflix Format Checker (MSL-based)

Check available video and audio formats for Netflix titles, including Dolby Vision, HDR10, and Dolby Atmos support.

## Features

- ✅ **Accurate Format Detection** using Netflix's MSL API
- ✅ **Dolby Vision** detection with profile identification (Profile 4, 5, 7, 8)
- ✅ **HDR10** and **HDR10+** detection
- ✅ **Dolby Atmos** audio detection
- ✅ **Detailed Track Information** (resolution, bitrate, codec, language)
- ✅ **Web Interface** for easy title lookup
- ✅ **RESTful API** for programmatic access

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Netflix ESN

```bash
# Copy example config
cp config.example.py config.py

# Edit config.py and add your Netflix ESN
# See SETUP.md for how to get your ESN
```

### 3. Export Netflix Cookies

```bash
# Install browser extension: "Get cookies.txt"
# Log into Netflix
# Export cookies to cookies.txt
# Place cookies.txt in project directory
```

### 4. Run the Application

```bash
python app_msl.py
```

Visit http://127.0.0.1:5001

## Usage

### Web Interface

1. Enter a Netflix title URL or ID
2. Click "Check Formats"
3. View detailed format information

### Example Titles

- **Our Planet** (4K HDR10 Atmos): `80025384`
- **Stranger Things** (4K HDR10 Atmos): `80057281`
- **The Witcher** (4K DV Atmos): `80189685`

## How It Works

### MSL Protocol

1. **Authentication**: Uses your ESN and Netflix cookies
2. **Handshake**: Establishes encrypted session with Netflix
3. **Manifest Request**: Retrieves playback manifest with all available formats
4. **Format Detection**: Parses manifest to identify HDR, DV, Atmos, etc.

### vs HTML Scraping

| Feature | HTML Scraping (old) | MSL API (new) |
|---------|-------------------|---------------|
| Accuracy | ❌ Low | ✅ High |
| Detail | ❌ Limited | ✅ Complete |
| Reliability | ❌ Fragile | ✅ Stable |
| DV Profiles | ❌ No | ✅ Yes |
| Track Info | ❌ No | ✅ Yes |

## Requirements

- Python 3.7+
- Netflix account with valid cookies
- Netflix ESN (device identifier)
- Active internet connection

## Project Structure

```
nf-check/
├── app_msl.py              # Flask web application (MSL-based)
├── netflix_msl.py          # MSL protocol implementation
├── format_detector.py      # Manifest parsing and format detection
├── netflix_service.py      # High-level Netflix service wrapper
├── config.example.py       # Configuration template
├── requirements.txt        # Python dependencies
├── SETUP.md               # Detailed setup instructions
└── templates/
    ├── index.html         # Web interface
    └── result.html        # Results display
```

## Configuration

### config.py

```python
# Your Netflix ESN
NETFLIX_ESN = "NFCDCH-02-ABCD1234WXYZ5678..."
```

### Environment Variables

```bash
export NETFLIX_ESN="NFCDCH-02-..."
export PORT=5001
```

## API Reference

### POST /lookup

Check formats for a Netflix title.

**Request:**
```bash
curl -X POST http://localhost:5001/lookup \
  -d "url=81215567"
```

**Response:**
```json
{
  "id": "81215567",
  "dolby_vision": true,
  "hdr10": true,
  "atmos": true,
  "max_resolution": "3840x2160",
  "video_tracks": [...],
  "audio_tracks": [...]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "esn_configured": true,
  "cookies_exist": true
}
```

## Troubleshooting

### "Netflix ESN not configured"

1. Create `config.py` from `config.example.py`
2. Add your Netflix ESN
3. See SETUP.md for how to find your ESN

### "cookies.txt not found"

1. Install "Get cookies.txt" browser extension
2. Log into Netflix
3. Export cookies to cookies.txt
4. Place in project directory

### "MSL handshake failed"

1. Verify ESN is correct
2. Re-export cookies (they may be expired)
3. Clear cache: `rm -rf .cache/msl_keys.json`
4. Restart application

### "No format information found"

1. Title may not have 4K/HDR/Atmos
2. Account may not have 4K plan
3. Try a known 4K title: "Our Planet" (80025384)

## Legal Notice

⚠️ **For educational and personal use only**

This tool:
- ✅ Checks format metadata for titles you have access to
- ✅ Educational purposes only
- ❌ Does NOT download or decrypt content
- ❌ Does NOT bypass DRM

Use responsibly and in compliance with Netflix Terms of Service.

## Credits

Based on MSL implementation from [Vinetrimmer](https://github.com/widevineleak/Vinetrimmer-Playready-V1.0).

## License

Educational and personal use only.

## Support

For setup help, see [SETUP.md](SETUP.md)

For technical details, see source code comments.
