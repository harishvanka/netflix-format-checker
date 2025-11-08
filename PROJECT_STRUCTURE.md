# Netflix Format Checker - Project Structure (Updated)

## 📁 Modern Flask App Directory Layout

```
nf-check/
│
├── 📄 app.py                           # ⭐ MAIN ENTRY POINT - Start here
├── requirements.txt                     # Python dependencies
├── config.example.py                    # Example configuration
├── config.py                            # User configuration (git ignored)
├── .gitignore                           # Git ignore rules
├── PROJECT_STRUCTURE.md                 # This file
│
├── 📂 app/                              # 🚀 Flask Application Package
│   ├── __init__.py                      # App factory (create_app())
│   ├── routes.py                        # All HTTP endpoints/routes
│   │
│   ├── 📂 models/                       # Core data models & scrapers
│   │   ├── __init__.py
│   │   ├── netflix_scraper.py           # Netflix HTML scraping logic
│   │   └── poster_fetcher.py            # IMDb poster fetching
│   │
│   └── 📂 utils/                        # Utility modules
│       ├── __init__.py
│       ├── netflix_msl.py               # MSL protocol (alternative)
│       ├── format_detector.py           # DASH manifest parsing
│       ├── netflix_simple.py            # Legacy API wrapper
│       ├── debug_netflix_posters.py     # Debug tool
│       └── test_poster_fetcher.py       # Test utilities
│
├── 📂 templates/                        # HTML templates
│   ├── index.html                       # Search form page
│   └── result.html                      # Results display page
│
├── 📂 static/                           # Static files (CSS, JS, images)
│   └── style.css                        # Modern glass-morphism design
│
├── 📂 cookies/                          # 🔐 Cookies storage (NEW)
│   └── cookies.txt                      # Netflix cookies (git ignored)
│
├── 📂 .cache/                           # Cache directory (auto-created)
│   └── msl_keys.json                    # MSL keys cache (MSL only)
│
└── 📂 docs/                             # Documentation
    ├── INDEX.md                         # Documentation index
    ├── README.md                        # Project overview
    ├── QUICK_START.md                   # 3-minute setup
    ├── SETUP.md                         # Detailed setup
    ├── CLAUDE.md                        # Architecture guide
    │
    ├── IMPLEMENTATION_GUIDE.md
    ├── IMPLEMENTATION_SUMMARY.md
    ├── IMPLEMENTATION_CHANGES.md
    ├── README_MSL.md
    │
    ├── POSTER_FETCHER_INTEGRATION.md
    ├── POSTER_FETCHER_FIX.md
    ├── POSTER_OPTIMIZATION_COMPLETE.md
    ├── POSTER_PRIORITY_CONFIG.md
    └── PERFORMANCE_COMPARISON.txt
```

---

## 📊 Project Organization Summary

### Root Level (Clean & Organized)
- **Entry Point**: `app.py` - Single main file to run the application
- **Configuration**: `config.py`, `config.example.py` - Settings
- **Dependencies**: `requirements.txt` - Python packages
- **Documentation**: `docs/` folder - All guides

### App Package (`app/`)
Modern Flask application structure following best practices:

#### `app/__init__.py` - Application Factory
- `create_app()` function - Creates Flask instance
- Configures logging, blueprints, and middleware
- Enables clean testing and deployment

#### `app/routes.py` - HTTP Routes
- GET `/` - Main search page
- POST `/lookup` - Format checking endpoint
- GET `/health` - Health check endpoint

#### `app/models/` - Core Business Logic
- `netflix_scraper.py` - HTML parsing & format detection
- `poster_fetcher.py` - IMDb poster extraction
- **These are the main modules your app depends on**

#### `app/utils/` - Alternative & Support Tools
- `netflix_msl.py` - MSL protocol (advanced alternative)
- `format_detector.py` - DASH manifest parsing
- `netflix_simple.py` - Legacy API wrapper
- `debug_netflix_posters.py` - Debugging tool
- `test_poster_fetcher.py` - Test utilities

### Static Assets
- `templates/` - HTML templates (2 files)
- `static/` - CSS styling (1 file)

### Credentials & Secrets
- `cookies/` - NEW folder for Netflix cookies
- `config.py` - User settings (git ignored)

### Documentation
- `docs/` - Complete documentation (14 files)
- Organized by topic: Setup, Architecture, Features, etc.

---

## 🗑️ Files Removed (Cleanup)

Unused/deprecated files were removed to follow Flask best practices:

| File | Reason |
|------|--------|
| `app_simple.py` | Merged into `app.py` + `app/routes.py` |
| `app_msl.py` | Advanced alternative (reference in docs only) |
| `app_old.py` | Original deprecated implementation |
| `check.py` | Minimal CLI utility (not used) |
| `netflix_service.py` | Unnecessary service wrapper |
| Root `*.py` files | Moved to `app/` package |

**Benefit**: Cleaner project structure, fewer root-level files to navigate

---

## 📈 File Count Summary

| Category | Count | Location |
|----------|-------|----------|
| Application Code | 7 | `app/` |
| Documentation | 14 | `docs/` |
| Templates | 2 | `templates/` |
| Styling | 1 | `static/` |
| Configuration | 3 | Root |
| **Total** | **27** | Organized |

---

## 🚀 How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Export cookies to cookies/cookies.txt
# (Instructions in docs/SETUP.md)

# Run the app
python app.py

# Visit http://127.0.0.1:5001
```

---

## 📋 Best Practices Implemented

✅ **Application Factory Pattern**
- `create_app()` in `app/__init__.py`
- Enables testing and flexibility

✅ **Blueprint-based Routing**
- Routes in `app/routes.py`
- Easy to extend with more endpoints

✅ **Organized Package Structure**
- `models/` for business logic
- `utils/` for utilities
- Clear separation of concerns

✅ **Configuration Management**
- `config.py` for settings
- `config.example.py` as template
- Environment variables supported

✅ **Secure Credentials**
- Cookies moved to `cookies/` folder
- Gitignored (not in version control)
- Separate from code

✅ **Clean Root Directory**
- Only essential files at root
- App code in `app/` package
- Documentation in `docs/` folder

---

## 🔄 File Locations Quick Reference

### Running the App
```
app.py → app/__init__.py → app/routes.py → app/models/
```

### HTML & CSS
```
templates/index.html, result.html
static/style.css
```

### Core Logic
```
app/models/netflix_scraper.py → Extracts formats
app/models/poster_fetcher.py → Fetches posters
```

### Alternatives (Reference)
```
app/utils/netflix_msl.py → Advanced approach
app/utils/format_detector.py → DASH parsing
```

### Testing & Debugging
```
app/utils/test_poster_fetcher.py → Tests
app/utils/debug_netflix_posters.py → Debugging
```

### Documentation
```
docs/INDEX.md → Start here
docs/QUICK_START.md → 3-minute setup
docs/SETUP.md → Detailed guide
```

---

## ✨ What's New in This Reorganization

| Feature | Benefit |
|---------|---------|
| **App Package** | Professional Flask structure |
| **Routes Module** | Easy to add new endpoints |
| **Models Separation** | Clean business logic |
| **Utils Folder** | Optional/alternative tools |
| **Cookies Folder** | Organized credential storage |
| **Clean Root** | Easier to navigate project |
| **App Factory** | Testable and flexible |

---

## 📝 Notes

- **Backward Compatibility**: The app checks both `cookies/cookies.txt` and root `cookies.txt`
- **Migration**: Old files removed but all functionality preserved
- **Expandable**: Easy to add new routes, models, or utilities
- **Deployment Ready**: Follows production Flask best practices

---

## 🎯 Navigation Tips

### For Users
1. Start: `python app.py`
2. Place cookies in `cookies/cookies.txt`
3. Visit http://127.0.0.1:5001

### For Developers
1. Entry point: `app.py`
2. Routes: `app/routes.py`
3. Core logic: `app/models/`
4. Add features: Create new routes or models

### For Documentation
1. Start: `docs/INDEX.md`
2. Quick setup: `docs/QUICK_START.md`
3. Full setup: `docs/SETUP.md`
4. Architecture: `docs/CLAUDE.md`

---

*Last updated: November 9, 2024*
