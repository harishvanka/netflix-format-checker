# Quick Start Guide

## 3-Minute Setup

### Step 1: Get Your Netflix ESN (2 min)

1. Open Netflix in Chrome/Firefox
2. Press F12 (Developer Tools)
3. Go to **Network** tab
4. Play any video
5. Filter by "msl"
6. Click a request → **Payload** tab
7. Find `"esn": "NFCDCH-02-..."` and copy it

### Step 2: Export Cookies (1 min)

1. Install: [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. While on Netflix, click extension icon
3. Click "Export"
4. Save as `cookies.txt` in project folder

### Step 3: Configure & Run (1 min)

```bash
# Create virtual environment (recommended on macOS)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy config template
cp config.example.py config.py

# Edit config.py - add your ESN
# NETFLIX_ESN = "NFCDCH-02-YOUR_ESN_HERE"

# Run!
python app.py
```

### Step 4: Test

1. Open http://127.0.0.1:5001
2. Enter: `80025384` (Our Planet - 4K/HDR/Atmos)
3. Click "Check Formats"
4. See results!

## Troubleshooting One-Liners

```bash
# Activate virtual environment first (if using venv)
source venv/bin/activate

# ESN not configured?
echo 'NETFLIX_ESN = "NFCDCH-02-YOUR_ESN"' > config.py

# Cookies expired?
# Re-export from browser while logged into Netflix

# MSL errors?
rm -rf .cache/msl_keys.json && python app.py

# Dependencies issue?
pip install --upgrade -r requirements.txt

# Virtual environment issues?
deactivate  # Exit current venv
rm -rf venv  # Remove old venv
python3 -m venv venv  # Create new venv
source venv/bin/activate  # Activate
pip install -r requirements.txt  # Reinstall
```

## Test Titles

| Title | ID | Formats |
|-------|----|----- ---|
| Our Planet | 80025384 | 4K, HDR10, Atmos |
| Stranger Things | 80057281 | 4K, HDR10, Atmos |
| The Witcher | 80189685 | 4K, DV Profile 5, Atmos |
| 6 Underground | 81001887 | 4K, DV, Atmos |

## Need Help?

- Setup details: [SETUP.md](SETUP.md)
- Full documentation: [README_MSL.md](README_MSL.md)
- Implementation details: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## Common Errors

**"Netflix ESN not configured"**
→ Create config.py with your ESN

**"cookies.txt not found"**
→ Export cookies while logged into Netflix

**"MSL handshake failed"**
→ Check ESN format & re-export cookies

**"No format information"**
→ Try title 80025384 first (known 4K title)

That's it! 🎬
