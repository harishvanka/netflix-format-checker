"""
Routes for Netflix Format Checker application
Handles all HTTP endpoints
"""

from flask import render_template, request, Blueprint
import re
import os
import logging
from app.models import NetflixScraper

bp = Blueprint('main', __name__)

logger = logging.getLogger(__name__)

# Define constants
INDEX_TEMPLATE = 'index.html'
RESULT_TEMPLATE = 'result.html'


def extract_title_id(url_or_id: str):
    """Extract numeric Netflix title id from various URL formats"""
    if not url_or_id:
        return None

    url_or_id = url_or_id.strip()

    # Pattern 1: /title/NUMBER
    m = re.search(r"/title/(\d+)", url_or_id)
    if m:
        return m.group(1)

    # Pattern 2: jbv=NUMBER (browse URLs)
    m = re.search(r"[?&]jbv=(\d+)", url_or_id)
    if m:
        return m.group(1)

    # Pattern 3: /watch/NUMBER
    m = re.search(r"/watch/(\d+)", url_or_id)
    if m:
        return m.group(1)

    # Pattern 4: /latest/NUMBER
    m = re.search(r"/latest/(\d+)", url_or_id)
    if m:
        return m.group(1)

    # Pattern 5: bare NUMBER
    if re.fullmatch(r"\d+", url_or_id):
        return url_or_id

    return None


@bp.route('/', methods=['GET'])
def index():
    """Main page"""
    return render_template(INDEX_TEMPLATE)


@bp.route('/lookup', methods=['POST'])
def lookup():
    """Look up Netflix title format information"""
    url = request.form.get('url')
    logger.info(f"Received lookup request: '{url}'")

    # Extract title ID
    title_id = extract_title_id(url)
    logger.info(f"Extracted title ID: {title_id}")

    if not title_id:
        return render_template(INDEX_TEMPLATE, error=(
            f'Could not extract a Netflix title ID from the input: {url}\n\n'
            'Supported formats:\n'
            '- https://www.netflix.com/title/81215567\n'
            '- https://www.netflix.com/browse?jbv=81215567\n'
            '- https://www.netflix.com/watch/81215567\n'
            '- 81215567 (just the ID)'
        ))

    try:
        # Check for cookies file
        # Try cookies/ folder first, then fall back to root
        cookies_path = os.path.join(os.getcwd(), "cookies", "cookies.txt")
        if not os.path.exists(cookies_path):
            # Fallback to root directory for backward compatibility
            cookies_path = os.path.join(os.getcwd(), "cookies.txt")

        if not os.path.exists(cookies_path):
            return render_template(INDEX_TEMPLATE, error=(
                "⚠️ cookies.txt not found!\n\n"
                "Please follow these steps:\n\n"
                "1. Install 'Get cookies.txt' extension for your browser\n"
                "   Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc\n"
                "2. Log into Netflix in your browser\n"
                "3. Click the extension icon while on Netflix\n"
                "4. Click 'Export' to save cookies.txt\n"
                "5. Place cookies.txt in the cookies/ folder (or project root)"
            ))

        # Check formats using HTML scraping
        logger.info(f"Checking formats for title {title_id}...")
        scraper = NetflixScraper(cookies_path)
        analysis = scraper.check_formats(title_id)

        logger.info(f"Analysis complete: DV={analysis.get('dolby_vision')}, HDR={analysis.get('hdr10')}, Atmos={analysis.get('atmos')}")

        # Determine resolution label from analysis data
        max_resolution_label = None
        if analysis.get('uhd'):
            max_resolution_label = 'UHD (4K)'
        elif analysis.get('hd'):
            max_resolution_label = 'FHD (1080p)'
        elif analysis.get('available'):
            # If we know it's available but no specific resolution detected, assume at least SD
            max_resolution_label = None
        else:
            max_resolution_label = None

        # Convert analysis to template format
        data = {
            'id': title_id,
            'title': analysis.get('title'),
            'year': analysis.get('year'),
            'poster': analysis.get('poster'),
            'dolby_vision': analysis.get('dolby_vision', False),
            'hdr': analysis.get('hdr10', False),
            'hd': analysis.get('hd', False),
            'sd': analysis.get('sd', False),
            'atmos': analysis.get('atmos', False),
            'dolby_digital': analysis.get('dolby_digital', False),
            'spatial_audio': analysis.get('spatial_audio', False),
            'uhd': analysis.get('uhd', False),
            'max_resolution_label': max_resolution_label,
            'video_tracks': [],
            'audio_tracks': [],
            # Availability status
            'is_available': analysis.get('is_available', True),
            'availability_status': analysis.get('availability_status', 'Available'),
            'coming_date': analysis.get('coming_date', None),
            'is_series': analysis.get('is_series', False)
        }

        # Build simple format list
        formats = []
        if max_resolution_label:
            formats.append(max_resolution_label)
        if data['dolby_vision']:
            formats.append('Dolby Vision')
        if data['hdr']:
            formats.append('HDR10')
        if data['atmos']:
            formats.append('Dolby Atmos')

        data['formats'] = formats

        # Check if we got useful data
        if not any([data['dolby_vision'], data['hdr'], data['atmos'], data['uhd']]):
            warning = (
                'No premium format information found.\n\n'
                'Possible reasons:\n'
                '1. The title may not have 4K/HDR/Dolby Vision/Atmos support\n'
                '2. Your account may not have access to 4K content\n'
                '3. The title page format may have changed\n\n'
                'Try checking with a known 4K title first (e.g., 80025384 - Our Planet)'
            )
            return render_template(RESULT_TEMPLATE, data=data, warning=warning)

        return render_template(RESULT_TEMPLATE, data=data)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return render_template(INDEX_TEMPLATE, error=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return render_template(INDEX_TEMPLATE, error=f'An error occurred: {str(e)}')


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    cookies_path = os.path.join(os.getcwd(), "cookies", "cookies.txt")
    if not os.path.exists(cookies_path):
        cookies_path = os.path.join(os.getcwd(), "cookies.txt")

    status = {
        'status': 'ok',
        'cookies_exist': os.path.exists(cookies_path)
    }
    return status
