# Netflix Format Checker - Implementation Guide

## Current Status

Your current implementation (`app.py`) uses HTML scraping which is:
- ❌ Unreliable (HTML structure changes frequently)
- ❌ Incomplete (public pages lack detailed format specs)
- ❌ Keyword-based detection (not accurate)

## Recommended Approach: Netflix MSL API

Based on the Vinetrimmer repository analysis, here's how to properly implement format detection:

### Architecture Overview

```
User Input (Title ID)
    ↓
Netflix MSL Authentication
    ↓
Request Playback Manifest (DASH MPD)
    ↓
Parse Manifest for Video/Audio Tracks
    ↓
Display Available Formats
```

### Required Components

#### 1. Netflix MSL (Message Security Layer) Client

The MSL protocol provides:
- Encrypted communication with Netflix API
- Device authentication via ESN (Electronic Serial Number)
- User authentication via Netflix cookies
- Manifest retrieval

**Key Files from Vinetrimmer:**
- `vinetrimmer/utils/MSL/__init__.py` - Core MSL implementation
- `vinetrimmer/utils/MSL/schemes/UserAuthentication.py` - Cookie-based auth
- `vinetrimmer/utils/MSL/schemes/EntityAuthentication.py` - Device auth

#### 2. Manifest Parser

Parse DASH MPD manifests to extract:

**Video Track Detection:**
```python
# From vinetrimmer/parsers/mpd.py
- Codec detection: h264, hevc (H.265), vp9, av1
- HDR detection:
  - HDR10: Look for "dvhe" or "hev1" codec with PQ transfer
  - Dolby Vision: "dvhe" or "dvh1" codec profiles (4, 5, 7, 8)
  - HLG: "hlg" supplemental property
- Resolution: width x height (1920x1080, 3840x2160)
- Bitrate: in kbps
```

**Audio Track Detection:**
```python
# From vinetrimmer/objects/tracks.py
- Codec: AAC, AC3, EAC3, AAC-128k, EAC3-384k
- Dolby Atmos: EAC3-JOC (Joint Object Coding)
- Channels: 2.0, 5.1, 7.1
- Bitrate: in kbps
```

#### 3. Authentication Flow

```python
# Simplified flow
1. Load Netflix cookies (nflxid, secnflxid) from cookies.txt
2. Initialize MSL client with:
   - ESN (Electronic Serial Number) - unique device identifier
   - Cookies for user authentication
3. Perform MSL handshake to establish encrypted session
4. Request manifest for title ID
5. Parse DASH MPD response
```

### What You Need

#### Required Information:

1. **Netflix ESN (Electronic Serial Number)**
   - Format: `NFCDCH-02-XXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
   - This identifies your "device" to Netflix
   - Can extract from browser or Netflix app

2. **Netflix Cookies** (you already have this)
   - `NetflixId` / `nflxid`
   - `SecureNetflixId` / `secnflxid`

3. **Netflix API Endpoint**
   - MSL endpoint: `https://www.netflix.com/nq/msl_v1/cadmium/...`
   - Varies by client type

#### Netflix MSL Request Structure:

```json
{
  "version": 2,
  "url": "/manifest",
  "id": 12345,
  "esn": "NFCDCH-02-...",
  "languages": ["en-US"],
  "uiVersion": "shakti-v123",
  "params": {
    "type": "standard",
    "viewableId": "81215567",  // Title ID
    "profiles": [
      "playready-h264mpl30-dash",
      "playready-h264mpl31-dash",
      "playready-h264hpl30-dash",
      "heaac-2-dash",
      "dfxp-ls-sdh"
    ],
    "flavor": "STANDARD",
    "drmType": "widevine",
    "usePsshBox": true,
    "videoOutputInfo": [{
      "type": "DigitalVideoOutputDescriptor",
      "outputType": "unknown",
      "supportedHdcpVersions": ["2.2"],
      "isHdcpEngaged": true
    }]
  }
}
```

**Key Parameters:**
- `profiles`: List of supported codecs/formats you want to check
  - `hevc-main10-L50-dash`: HEVC SDR
  - `hevc-main10-L51-dash-cenc`: HEVC SDR with encryption
  - `hevc-hdr-main10-L50-dash-cenc`: HDR10
  - `hevc-dv-main10-L50-dash-cenc`: Dolby Vision
  - `hevc-dv5-main10-L51-dash-cenc`: DV Profile 5
  - `dd-5.1-dash`: Dolby Digital 5.1
  - `ddplus-5.1-dash`: Dolby Digital Plus 5.1
  - `ddplus-atmos-dash`: Dolby Atmos

### Response Structure

Netflix returns a DASH MPD manifest like:

```xml
<MPD>
  <Period>
    <AdaptationSet contentType="video">
      <Representation
        bandwidth="12000000"
        codecs="hev1.2.4.L150.B0"
        width="3840"
        height="2160">
        <!-- HDR10 or Dolby Vision based on codec -->
      </Representation>
    </AdaptationSet>

    <AdaptationSet contentType="audio">
      <Representation
        bandwidth="768000"
        codecs="ec-3"
        audioChannelConfiguration="JOC">
        <!-- Dolby Atmos (JOC = Joint Object Coding) -->
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>
```

### Codec Detection Rules

#### Video:

| Codec String | Format |
|--------------|--------|
| `hev1.1.*` or `hvc1.1.*` | HEVC SDR |
| `hev1.2.*` or `hvc1.2.*` | HEVC HDR10 (Main 10) |
| `dvhe.04.*` or `dvh1.04.*` | Dolby Vision Profile 4 (HDR10 base layer) |
| `dvhe.05.*` or `dvh1.05.*` | Dolby Vision Profile 5 (SDR base layer) |
| `dvhe.07.*` or `dvh1.07.*` | Dolby Vision Profile 7 (EL + BL) |
| `dvhe.08.*` or `dvh1.08.*` | Dolby Vision Profile 8 (LL mode) |

#### Audio:

| Codec String | Format |
|--------------|--------|
| `mp4a.40.2` | AAC Stereo |
| `ac-3` | Dolby Digital 5.1 |
| `ec-3` | Dolby Digital Plus 5.1/7.1 |
| `ec-3` + `JOC` attribute | Dolby Atmos |

### Simplified Implementation

Here's a simplified approach for your use case (format checking only, no downloading):

```python
# netflix_formats.py

import requests
import json
from http.cookiejar import MozillaCookieJar
import xml.etree.ElementTree as ET

class NetflixFormatChecker:
    def __init__(self, cookies_path):
        self.cookies = self._load_cookies(cookies_path)
        self.esn = "NFCDCH-02-YOURESN..."  # You need to get this
        self.session = requests.Session()

    def _load_cookies(self, path):
        jar = MozillaCookieJar(path)
        jar.load(ignore_discard=True, ignore_expires=True)
        return {c.name: c.value for c in jar}

    def get_manifest(self, title_id):
        """
        Request DASH manifest from Netflix MSL API
        Note: This is simplified - actual implementation requires
        MSL encryption/decryption from Vinetrimmer
        """
        # This would use the MSL protocol to:
        # 1. Authenticate with ESN + cookies
        # 2. Request manifest for title_id
        # 3. Decrypt MSL response
        # 4. Return DASH MPD XML
        pass

    def parse_manifest(self, mpd_xml):
        """Parse DASH manifest for available formats"""
        root = ET.fromstring(mpd_xml)

        formats = {
            'video': [],
            'audio': [],
            'dolby_vision': False,
            'hdr10': False,
            'atmos': False
        }

        # Parse video tracks
        for adapt_set in root.findall('.//{*}AdaptationSet[@contentType="video"]'):
            for rep in adapt_set.findall('.//{*}Representation'):
                codec = rep.get('codecs', '')
                width = rep.get('width')
                height = rep.get('height')
                bandwidth = rep.get('bandwidth')

                # Detect formats
                if codec.startswith('dvhe') or codec.startswith('dvh1'):
                    formats['dolby_vision'] = True
                    profile = codec.split('.')[1] if '.' in codec else 'unknown'
                    formats['video'].append({
                        'type': f'Dolby Vision Profile {profile}',
                        'resolution': f'{width}x{height}',
                        'bitrate': bandwidth
                    })
                elif codec.startswith('hev1.2') or codec.startswith('hvc1.2'):
                    formats['hdr10'] = True
                    formats['video'].append({
                        'type': 'HDR10',
                        'resolution': f'{width}x{height}',
                        'bitrate': bandwidth
                    })
                elif codec.startswith('hev1') or codec.startswith('hvc1'):
                    formats['video'].append({
                        'type': 'SDR (HEVC)',
                        'resolution': f'{width}x{height}',
                        'bitrate': bandwidth
                    })

        # Parse audio tracks
        for adapt_set in root.findall('.//{*}AdaptationSet[@contentType="audio"]'):
            for rep in adapt_set.findall('.//{*}Representation'):
                codec = rep.get('codecs', '')

                # Check for Atmos
                joc = adapt_set.find('.//{*}SupplementalProperty[@value="JOC"]')
                if codec == 'ec-3' and joc is not None:
                    formats['atmos'] = True
                    formats['audio'].append({
                        'type': 'Dolby Atmos',
                        'codec': 'EAC3-JOC',
                        'bitrate': rep.get('bandwidth')
                    })
                elif codec == 'ec-3':
                    formats['audio'].append({
                        'type': 'Dolby Digital Plus',
                        'codec': 'EAC3',
                        'bitrate': rep.get('bandwidth')
                    })

        return formats

    def check_title(self, title_id):
        """Check available formats for a title"""
        manifest = self.get_manifest(title_id)
        return self.parse_manifest(manifest)
```

### Integration with Your Flask App

Update your `app.py` to use the MSL-based approach instead of HTML scraping:

```python
from netflix_formats import NetflixFormatChecker

@app.route('/lookup', methods=['POST'])
def lookup():
    url = request.form.get('url')
    title_id = extract_title_id(url)

    if not title_id:
        return render_template(INDEX_TEMPLATE, error='Invalid title ID')

    try:
        checker = NetflixFormatChecker('cookies.txt')
        formats = checker.check_title(title_id)

        return render_template('result.html', data={
            'id': title_id,
            'dolby_vision': formats['dolby_vision'],
            'hdr': formats['hdr10'],
            'atmos': formats['atmos'],
            'video_tracks': formats['video'],
            'audio_tracks': formats['audio']
        })
    except Exception as e:
        return render_template(INDEX_TEMPLATE, error=str(e))
```

## Next Steps

### Option A: Quick Fix (Keep HTML Scraping)

If you want to improve your current approach without MSL:

1. **Better JSON extraction**: Look for `reactContext` or Netflix API responses in `<script>` tags
2. **Check multiple patterns**: Netflix embeds data differently on different pages
3. **Use unofficial APIs**: Some third-party services aggregate this data

### Option B: Proper Implementation (Recommended)

1. **Extract required components from Vinetrimmer:**
   - Copy `vinetrimmer/utils/MSL/` directory
   - Copy `vinetrimmer/parsers/mpd.py`
   - Copy necessary authentication code

2. **Get Netflix ESN:**
   - Use browser developer tools on netflix.com
   - Look for MSL requests in Network tab
   - Extract ESN from request payload

3. **Implement MSL client:**
   - Create `netflix_msl.py` with authentication
   - Implement manifest request function
   - Add manifest parsing

4. **Update Flask app:**
   - Replace HTML scraping with MSL API calls
   - Display detailed format information

## Legal Considerations

⚠️ **Important Notes:**

1. **Terms of Service**: Using Netflix's MSL API directly may violate their ToS
2. **Personal Use**: Checking formats for content you have access to is generally acceptable
3. **No Distribution**: Don't distribute Netflix content or bypass DRM
4. **Educational**: This is for learning how Netflix's technology works

Your current use case (checking available formats) is less invasive than downloading content, but be aware of the legal implications.

## Questions?

Key questions to address:

1. **Do you want to implement the MSL approach?** (More complex but accurate)
2. **Or improve HTML scraping?** (Simpler but less reliable)
3. **Do you have a Netflix ESN?** (Required for MSL)
4. **What's your technical comfort level?** (MSL requires crypto knowledge)

Let me know which direction you'd like to pursue!
