"""
Netflix Format Checker - Main Entry Point

A Flask web application for checking Netflix content format support.
Supports: 4K/UHD, HDR10, Dolby Vision, Dolby Atmos, 5.1 Dolby Digital, Spatial Audio

Usage:
    python app.py

The app will start at http://127.0.0.1:5001
"""

import os
import logging
from app import create_app

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create Flask app
app = create_app()


def main():
    """Main entry point"""
    # Determine port
    port = int(os.environ.get('PORT', 5001))

    # Check for cookies file (both locations)
    cookies_path_new = os.path.join(os.getcwd(), "cookies", "cookies.txt")
    cookies_path_old = os.path.join(os.getcwd(), "cookies.txt")
    cookies_exist = os.path.exists(cookies_path_new) or os.path.exists(cookies_path_old)

    # Print startup banner
    print("\n" + "="*60)
    print("Netflix Format Checker")
    print("="*60)
    print(f"\nServer starting at http://127.0.0.1:{port}")
    print(f"Cookies File: {'✓ Found' if cookies_exist else '✗ Not Found'}")

    if not cookies_exist:
        print("\n⚠️  WARNING: cookies.txt not found!")
        print("   Export Netflix cookies and save to cookies/ folder\n")

    print("="*60 + "\n")

    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=port, threaded=True)


if __name__ == '__main__':
    main()
