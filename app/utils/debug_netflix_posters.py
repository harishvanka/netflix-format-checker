#!/usr/bin/env python3
"""
Debug script to analyze Netflix poster data structures
Run this with a Netflix title ID to see what poster data is available
"""

import requests
import re
import json
from http.cookiejar import MozillaCookieJar
import sys

def analyze_netflix_posters(title_id, cookies_path=None):
    """Analyze poster data from Netflix page"""

    try:
        # Determine cookies path
        if cookies_path is None:
            import os
            cookies_path = os.path.join(os.getcwd(), "cookies", "cookies.txt")
            if not os.path.exists(cookies_path):
                cookies_path = os.path.join(os.getcwd(), "cookies.txt")

        # Load cookies
        jar = MozillaCookieJar(cookies_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        cookies = {c.name: c.value for c in jar}

        # Fetch page
        url = f"https://www.netflix.com/title/{title_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        print(f"Fetching: {url}\n")
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        html = response.text

        print("=" * 80)
        print("ANALYZING NETFLIX POSTER SOURCES")
        print("=" * 80)

        # 1. Check og:image meta tag
        print("\n1. OG:IMAGE META TAG")
        print("-" * 80)
        match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if match:
            og_image = match.group(1)
            print(f"Found: {og_image[:100]}")
            print(f"Domain: {'netflix' if 'nflx' in og_image.lower() or 'occ-' in og_image else 'OTHER'}")
        else:
            print("Not found")

        # 2. Check twitter:image
        print("\n2. TWITTER:IMAGE META TAG")
        print("-" * 80)
        match = re.search(r'<meta name="twitter:image" content="([^"]+)"', html)
        if match:
            tw_image = match.group(1)
            print(f"Found: {tw_image[:100]}")
            print(f"Domain: {'netflix' if 'nflx' in tw_image.lower() or 'occ-' in tw_image else 'OTHER'}")
        else:
            print("Not found")

        # 3. Check boxArt in JSON - look for all instances
        print("\n3. BOXART IN JSON (All instances)")
        print("-" * 80)

        # Find all boxArt patterns
        boxart_pattern = r'"boxArt"\s*:\s*\{([^}]+)\}'
        matches = re.finditer(boxart_pattern, html)
        boxart_count = 0

        for i, match in enumerate(matches, 1):
            boxart_count += 1
            boxart_data = '{' + match.group(1) + '}'
            print(f"\nboxArt #{i}:")
            print(f"  Raw: {boxart_data[:150]}")

            # Try to parse it
            try:
                parsed = json.loads(boxart_data)
                for key in parsed:
                    if isinstance(parsed[key], str) and 'http' in parsed[key]:
                        print(f"  {key}: {parsed[key][:80]}")
                    else:
                        print(f"  {key}: {str(parsed[key])[:80]}")
            except:
                print(f"  (Could not parse as JSON)")

        if boxart_count == 0:
            print("No boxArt found")

        # 4. Look for image URLs near title ID
        print("\n4. IMAGES NEAR TITLE ID IN JSON")
        print("-" * 80)

        # Find context around title ID
        context_pattern = rf'"{title_id}"[^}}{{]{{0,800}}"(image|poster|boxArt|boxshot|artwork)"[^}}{{]*"(url|342w|500w)":\s*"([^"]+)"'
        matches = re.finditer(context_pattern, html)
        match_count = 0

        for match in matches:
            match_count += 1
            field = match.group(1)
            size = match.group(2)
            url = match.group(3)
            print(f"\nMatch #{match_count}:")
            print(f"  Field: {field}")
            print(f"  Size: {size}")
            print(f"  URL: {url[:80]}")
            print(f"  Domain: {'netflix' if 'nflx' in url.lower() or 'occ-' in url else 'OTHER'}")

        if match_count == 0:
            print("No images found near title ID")

        # 5. Generic image/poster field search
        print("\n5. GENERIC IMAGE/POSTER FIELDS")
        print("-" * 80)

        # Look for image URLs that are from Netflix
        netflix_image_pattern = r'(https?://[^"]*(?:nflx|occ-)[^"]*\.(?:jpg|jpeg|png))'
        matches = re.finditer(netflix_image_pattern, html, re.IGNORECASE)
        image_count = 0
        urls_found = set()

        for match in matches:
            url = match.group(1)
            if url not in urls_found:  # Skip duplicates
                image_count += 1
                urls_found.add(url)
                if image_count <= 10:  # Show first 10
                    print(f"\n#{image_count}: {url[:80]}")

        if image_count > 10:
            print(f"\n... and {image_count - 10} more Netflix image URLs")
        elif image_count == 0:
            print("No Netflix image URLs found")

        # 6. Summary
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        print("""
Priority order for most reliable Netflix poster:
1. boxArt with 342w or 500w dimensions (title-specific, poster-sized)
2. boxArt with url field (generic, any size)
3. og:image (if from Netflix CDN)
4. twitter:image (if from Netflix CDN)
5. Other image/poster fields
6. IMDb fallback (only if Netflix has nothing)
        """)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python debug_netflix_posters.py <TITLE_ID>")
        print("Example: python debug_netflix_posters.py 80189685")
        sys.exit(1)

    title_id = sys.argv[1]
    analyze_netflix_posters(title_id)
