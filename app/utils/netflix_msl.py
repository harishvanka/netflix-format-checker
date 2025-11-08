"""
Netflix MSL (Message Security Layer) Client
Simplified implementation for Netflix format checking
Based on Vinetrimmer MSL implementation
"""

import base64
import gzip
import json
import logging
import os
import random
import ssl
import time
import zlib
from datetime import datetime
from io import BytesIO

import requests
from Cryptodome.Cipher import AES, PKCS1_OAEP
from Cryptodome.Hash import HMAC, SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util import Padding
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.util import ssl_


class MSLKeys:
    """Stores MSL encryption/signing keys and master token"""
    def __init__(self, encryption=None, sign=None, rsa=None, mastertoken=None):
        self.encryption = encryption
        self.sign = sign
        self.rsa = rsa
        self.mastertoken = mastertoken


class NetflixMSL:
    """Netflix MSL Client for authenticated API communication"""

    CIPHERS = (
        "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:"
        "ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:"
        "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA"
    )

    def __init__(self, esn, cookies_dict, endpoint="https://www.netflix.com/api/shakti/msl", cache_path=None):
        """
        Initialize Netflix MSL client

        :param esn: Electronic Serial Number (Netflix device identifier)
        :param cookies_dict: Dictionary with 'nflxid' and 'securenflxid' cookies
        :param endpoint: Netflix MSL endpoint URL
        :param cache_path: Path to cache MSL keys (optional)
        """
        self.log = logging.getLogger("NetflixMSL")
        self.esn = esn
        self.cookies = cookies_dict
        self.endpoint = endpoint
        self.cache_path = cache_path
        self.message_id = random.randint(0, pow(2, 52))

        # Create session with custom TLS adapter
        self.session = self._create_session()

        # Load or perform handshake
        self.keys = self._load_cache() if cache_path and os.path.exists(cache_path) else None
        if not self.keys:
            self._handshake()

    def _create_session(self):
        """Create requests session with custom TLS configuration"""
        class TlsAdapter(HTTPAdapter):
            def __init__(self, ssl_options=0, **kwargs):
                self.ssl_options = ssl_options
                super().__init__(**kwargs)

            def init_poolmanager(self, *pool_args, **pool_kwargs):
                ctx = ssl_.create_urllib3_context(
                    ciphers=NetflixMSL.CIPHERS,
                    cert_reqs=ssl.CERT_REQUIRED,
                    options=self.ssl_options
                )
                self.poolmanager = PoolManager(*pool_args, ssl_context=ctx, **pool_kwargs)

        session = requests.Session()
        adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
        session.mount("https://", adapter)
        return session

    def _handshake(self):
        """Perform MSL handshake to establish encrypted session"""
        self.log.info("Performing MSL handshake...")

        # Generate RSA key pair for key exchange
        self.keys = MSLKeys()
        self.keys.rsa = RSA.generate(2048)

        # Prepare key exchange request
        keyrequestdata = {
            "scheme": "ASYMMETRIC_WRAPPED",
            "keydata": {
                "keypairid": "superKeyPair",
                "mechanism": "JWK_RSA",
                "publickey": base64.b64encode(
                    self.keys.rsa.publickey().export_key(format="DER")
                ).decode("utf-8")
            }
        }

        # Note: User authentication data should NOT be included in the handshake
        # It will be added to subsequent messages after the master token is established

        # Generate handshake message
        header_data = {
            "messageid": self.message_id,
            "renewable": True,
            "handshake": True,
            "capabilities": {
                "compressionalgos": ["GZIP"],
                "languages": ["en-US"],
                "encoderformats": ["JSON"]
            },
            "timestamp": int(time.time()),
            "sender": self.esn,
            "nonreplayable": False,
            "recipient": "Netflix",
            "keyrequestdata": [keyrequestdata]
        }

        # Build handshake request
        data = json.dumps({
            "entityauthdata": {
                "scheme": "NONE",
                "authdata": {"identity": self.esn}
            },
            "headerdata": base64.b64encode(
                json.dumps(header_data).encode("utf-8")
            ).decode("utf-8"),
            "signature": ""
        })
        data += json.dumps({
            "payload": base64.b64encode(json.dumps({
                "messageid": self.message_id,
                "data": "",
                "sequencenumber": 1,
                "endofmsg": True
            }).encode("utf-8")).decode("utf-8"),
            "signature": ""
        })

        # Send handshake request
        try:
            r = self.session.post(self.endpoint, data=data)
            r.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"MSL handshake failed: {e}")

        # Parse handshake response
        key_exchange = r.json()
        if "errordata" in key_exchange:
            error = json.loads(base64.b64decode(key_exchange["errordata"]).decode())
            raise Exception(f"MSL handshake error: {error.get('errormsg')}")

        # Extract crypto keys
        header_response = json.loads(
            base64.b64decode(key_exchange["headerdata"]).decode("utf-8")
        )
        key_response_data = header_response["keyresponsedata"]

        if key_response_data["scheme"] != "ASYMMETRIC_WRAPPED":
            raise Exception("Key exchange scheme mismatch")

        key_data = key_response_data["keydata"]
        cipher_rsa = PKCS1_OAEP.new(self.keys.rsa)

        # Decrypt encryption key
        self.keys.encryption = self._base64key_decode(
            json.loads(
                cipher_rsa.decrypt(base64.b64decode(key_data["encryptionkey"])).decode("utf-8")
            )["k"]
        )

        # Decrypt signing key
        self.keys.sign = self._base64key_decode(
            json.loads(
                cipher_rsa.decrypt(base64.b64decode(key_data["hmackey"])).decode("utf-8")
            )["k"]
        )

        # Store master token
        self.keys.mastertoken = key_response_data["mastertoken"]

        # Cache keys if path provided
        if self.cache_path:
            self._save_cache()

        self.log.info("MSL handshake successful")

    def _load_cache(self):
        """Load cached MSL keys"""
        if not self.cache_path or not os.path.exists(self.cache_path):
            return None

        try:
            with open(self.cache_path, 'r') as f:
                data = json.load(f)

            keys = MSLKeys()
            keys.encryption = base64.b64decode(data['encryption'])
            keys.sign = base64.b64decode(data['sign'])
            keys.rsa = RSA.import_key(data['rsa'])
            keys.mastertoken = data['mastertoken']

            # Check if master token is expired
            token_data = json.loads(
                base64.b64decode(keys.mastertoken["tokendata"]).decode("utf-8")
            )
            expiration = datetime.utcfromtimestamp(int(token_data["expiration"]))
            hours_remaining = (expiration - datetime.now()).total_seconds() / 3600

            if hours_remaining < 10:
                self.log.info("Cached MSL keys are expired")
                return None

            self.log.info("Using cached MSL keys")
            return keys
        except Exception as e:
            self.log.warning(f"Failed to load cached keys: {e}")
            return None

    def _save_cache(self):
        """Save MSL keys to cache"""
        if not self.cache_path:
            return

        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        data = {
            'encryption': base64.b64encode(self.keys.encryption).decode(),
            'sign': base64.b64encode(self.keys.sign).decode(),
            'rsa': self.keys.rsa.export_key().decode(),
            'mastertoken': self.keys.mastertoken
        }

        with open(self.cache_path, 'w') as f:
            json.dump(data, f)

    @staticmethod
    def _base64key_decode(payload):
        """Decode base64-encoded key with proper padding"""
        length = len(payload) % 4
        if length == 2:
            payload += "=="
        elif length == 3:
            payload += "="
        elif length != 0:
            raise ValueError("Invalid base64 string")
        return base64.urlsafe_b64decode(payload.encode("utf-8"))

    @staticmethod
    def _gzip_compress(data):
        """Compress data with gzip"""
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as fd:
            fd.write(data)
        return base64.b64encode(out.getvalue())

    def _encrypt(self, plaintext):
        """Encrypt plaintext with AES-CBC"""
        iv = get_random_bytes(16)

        sequence_number = json.loads(
            base64.b64decode(self.keys.mastertoken["tokendata"]).decode("utf-8")
        )["sequencenumber"]

        return json.dumps({
            "ciphertext": base64.b64encode(
                AES.new(
                    self.keys.encryption,
                    AES.MODE_CBC,
                    iv
                ).encrypt(
                    Padding.pad(plaintext.encode("utf-8"), 16)
                )
            ).decode("utf-8"),
            "keyid": f"{self.esn}_{sequence_number}",
            "sha256": "AA==",
            "iv": base64.b64encode(iv).decode("utf-8")
        })

    def _sign(self, text):
        """Sign text with HMAC-SHA256"""
        return base64.b64encode(
            HMAC.new(self.keys.sign, text.encode("utf-8"), SHA256).digest()
        )

    def _decrypt_payload_chunks(self, payload_chunks):
        """Decrypt and extract data from payload chunks"""
        raw_data = ""

        for payload_chunk in payload_chunks:
            # Decode payload
            payload_chunk = json.loads(
                base64.b64decode(payload_chunk["payload"]).decode("utf-8")
            )

            # Decrypt
            payload_decrypted = AES.new(
                key=self.keys.encryption,
                mode=AES.MODE_CBC,
                iv=base64.b64decode(payload_chunk["iv"])
            ).decrypt(base64.b64decode(payload_chunk["ciphertext"]))

            payload_decrypted = Padding.unpad(payload_decrypted, 16)
            payload_decrypted = json.loads(payload_decrypted.decode("utf-8"))

            # Decompress if needed
            payload_data = base64.b64decode(payload_decrypted["data"])
            if payload_decrypted.get("compressionalgo") == "GZIP":
                payload_data = zlib.decompress(payload_data, 16 + zlib.MAX_WBITS)

            raw_data += payload_data.decode("utf-8")

        data = json.loads(raw_data)

        if "error" in data:
            error = data["error"]
            raise Exception(f"MSL error: {error.get('display')} - {error.get('detail')}")

        return data.get("result", data)

    def send_message(self, application_data, include_user_auth=True):
        """Send encrypted MSL message and return decrypted response"""
        self.message_id += 1

        # Create header with user authentication
        header_data = {
            "messageid": self.message_id,
            "renewable": True,
            "handshake": False,
            "capabilities": {
                "compressionalgos": ["GZIP"],
                "languages": ["en-US"],
                "encoderformats": ["JSON"]
            },
            "timestamp": int(time.time()),
            "sender": self.esn,
            "nonreplayable": False,
            "recipient": "Netflix"
        }

        # Add user authentication data for manifest requests
        if include_user_auth:
            netflixid = self.cookies.get("NetflixId") or self.cookies.get("nflxid")
            securenetflixid = self.cookies.get("SecureNetflixId") or self.cookies.get("securenflxid")

            if not netflixid or not securenetflixid:
                raise Exception(
                    "Netflix authentication cookies not found. "
                    "Please re-export cookies.txt while logged into Netflix."
                )

            header_data["userauthdata"] = {
                "scheme": "NETFLIXID",
                "authdata": {
                    "netflixid": netflixid,
                    "securenetflixid": securenetflixid
                }
            }

        headerdata = self._encrypt(json.dumps(header_data))

        header = json.dumps({
            "headerdata": base64.b64encode(headerdata.encode("utf-8")).decode("utf-8"),
            "signature": self._sign(headerdata).decode("utf-8"),
            "mastertoken": self.keys.mastertoken
        })

        # Create payload
        payload_chunk = self._encrypt(json.dumps({
            "messageid": self.message_id,
            "data": self._gzip_compress(json.dumps(application_data).encode("utf-8")).decode("utf-8"),
            "compressionalgo": "GZIP",
            "sequencenumber": 1,
            "endofmsg": True
        }))

        payload = json.dumps({
            "payload": base64.b64encode(payload_chunk.encode("utf-8")).decode("utf-8"),
            "signature": self._sign(payload_chunk).decode("utf-8")
        })

        message = header + payload

        # Send request
        try:
            r = self.session.post(self.endpoint, data=message)
            r.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"MSL message send failed: {e}")

        # Parse response
        parsed_message = json.loads("[{}]".format(r.text.replace("}{", "},{")))
        header_response = parsed_message[0]

        if "errordata" in header_response:
            error = json.loads(base64.b64decode(header_response["errordata"]).decode())
            raise Exception(f"MSL response error: {error.get('errormsg')}")

        payload_chunks = parsed_message[1:] if len(parsed_message) > 1 else []

        if payload_chunks:
            return self._decrypt_payload_chunks(payload_chunks)

        return {}

    def get_manifest(self, viewable_id, profiles=None):
        """
        Request playback manifest for a Netflix title

        :param viewable_id: Netflix title ID (e.g., "81215567")
        :param profiles: List of video/audio profiles to request (optional)
        :return: Manifest data including DASH MPD
        """
        if profiles is None:
            # Request a comprehensive set of profiles to detect all formats
            profiles = [
                # Video - H.264
                "playready-h264mpl30-dash",
                "playready-h264mpl31-dash",
                "playready-h264hpl30-dash",
                "playready-h264hpl31-dash",
                # Video - HEVC SDR
                "hevc-main-L30-dash-cenc",
                "hevc-main-L31-dash-cenc",
                "hevc-main10-L30-dash-cenc",
                "hevc-main10-L31-dash-cenc",
                "hevc-main10-L40-dash-cenc",
                "hevc-main10-L41-dash-cenc",
                "hevc-main10-L50-dash-cenc",
                "hevc-main10-L51-dash-cenc",
                # Video - HEVC HDR10
                "hevc-hdr-main10-L30-dash-cenc",
                "hevc-hdr-main10-L31-dash-cenc",
                "hevc-hdr-main10-L40-dash-cenc",
                "hevc-hdr-main10-L41-dash-cenc",
                "hevc-hdr-main10-L50-dash-cenc",
                "hevc-hdr-main10-L51-dash-cenc",
                # Video - Dolby Vision
                "hevc-dv-main10-L30-dash-cenc",
                "hevc-dv-main10-L31-dash-cenc",
                "hevc-dv-main10-L40-dash-cenc",
                "hevc-dv-main10-L41-dash-cenc",
                "hevc-dv-main10-L50-dash-cenc",
                "hevc-dv-main10-L51-dash-cenc",
                "hevc-dv5-main10-L30-dash-cenc",
                "hevc-dv5-main10-L31-dash-cenc",
                "hevc-dv5-main10-L40-dash-cenc",
                "hevc-dv5-main10-L41-dash-cenc",
                "hevc-dv5-main10-L50-dash-cenc",
                "hevc-dv5-main10-L51-dash-cenc",
                # Audio
                "heaac-2-dash",
                "heaac-2hq-dash",
                "ddplus-2.0-dash",
                "ddplus-5.1-dash",
                "ddplus-5.1hq-dash",
                "dd-5.1-dash",
                "ddplus-atmos-dash",
                # Subtitles
                "webvtt-lssdh-ios8",
                "dfxp-ls-sdh"
            ]

        # Build manifest request
        request_data = {
            "version": 2,
            "url": "/manifest",
            "id": int(time.time() * 1000),
            "esn": self.esn,
            "languages": ["en-US"],
            "uiVersion": "shakti-v4bf615c3",
            "clientVersion": "6.0033.511.011",
            "params": {
                "type": "standard",
                "viewableId": str(viewable_id),
                "profiles": profiles,
                "flavor": "STANDARD",
                "drmType": "widevine",
                "drmVersion": 25,
                "usePsshBox": True,
                "isBranching": False,
                "useHttpsStreams": True,
                "imageSubtitleHeight": 1080,
                "uiVersion": "shakti-v4bf615c3",
                "clientVersion": "6.0033.511.011",
                "supportsPreReleasePin": True,
                "supportsWatermark": True,
                "showAllSubDubTracks": False,
                "videoOutputInfo": [
                    {
                        "type": "DigitalVideoOutputDescriptor",
                        "outputType": "unknown",
                        "supportedHdcpVersions": ["2.2"],
                        "isHdcpEngaged": True
                    }
                ],
                "preferAssistiveAudio": False,
                "isNonMember": False
            }
        }

        self.log.info(f"Requesting manifest for viewable ID: {viewable_id}")
        response = self.send_message(request_data)

        return response
