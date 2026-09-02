import hmac
import hashlib
import ipaddress
import secrets
import urllib.parse
from datetime import datetime, UTC

PRIVATE_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]

def generate_webhook_secret() -> str:
    """Generates a cryptographically secure random webhook secret with prefix 'whsec_'."""
    return f"whsec_{secrets.token_hex(24)}"

def validate_webhook_url(url: str, allow_http: bool = False) -> str:
    """
    Validates webhook target destination URL and enforces SSRF protections.
    Blocks private IP ranges, loopback, cloud metadata endpoints, and non-HTTP protocols.
    """
    if not url:
        raise ValueError("Webhook endpoint URL cannot be empty.")

    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme not in ["https", "http"]:
        raise ValueError(f"Invalid URL protocol '{scheme}'. Webhooks require HTTPS.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: Missing hostname.")

    # Check IP address format first for SSRF Protection Guard
    try:
        ip = ipaddress.ip_address(hostname)
        for net in PRIVATE_IP_NETWORKS:
            if ip in net:
                raise ValueError(f"SSRF Protection Guard: Target IP {hostname} is in a restricted private/local network range.")
    except ValueError as e:
        if "SSRF Protection Guard" in str(e):
            raise
        # Hostname is a domain string (not a raw IP literal)

    if scheme == "http" and not allow_http:
        # Check if local test environment or explicit HTTP setting
        if hostname not in ["localhost", "127.0.0.1", "testserver", "test"]:
            raise ValueError("Insecure protocol 'http://' is not allowed for webhooks in production. HTTPS required.")

    return url

def compute_hmac_signature(secret: str, timestamp: str, payload_body: str) -> str:
    """
    Computes HMAC-SHA256 signature over timestamp and raw payload body.
    Canonical signing string format: timestamp + '.' + payload_body
    Returns signature string formatted as 'sha256=<hex_digest>'
    """
    to_sign = f"{timestamp}.{payload_body}".encode()
    sig = hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).hexdigest()
    return f"sha256={sig}"

def verify_hmac_signature(secret: str, timestamp: str, payload_body: str, signature_header: str, tolerance_seconds: int = 300) -> bool:
    """
    Verifies HMAC-SHA256 signature using constant-time comparison and enforces timestamp replay window.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    # Check timestamp replay window
    try:
        ts_val = int(timestamp)
        now_ts = int(datetime.now(UTC).timestamp())
        if abs(now_ts - ts_val) > tolerance_seconds:
            return False
    except ValueError:
        return False

    expected = compute_hmac_signature(secret, timestamp, payload_body)
    return hmac.compare_digest(expected, signature_header)
