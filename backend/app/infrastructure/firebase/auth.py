"""
Firebase Authentication Token Verification & Identity Resolution Service.
Validates Firebase ID Tokens, extracts verified UIDs & email claims,
and resolves user identity context against database records.
"""

import json
import os
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger

class FirebaseAuthService:
    """
    Server-side Firebase Authentication verifier.
    Verifies Bearer ID Tokens via Google Identity Toolkit or Firebase Admin SDK.
    """

    @classmethod
    async def verify_id_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifies a Firebase ID token and returns decoded payload (uid, email, custom claims).
        Returns None if token is invalid or expired.
        """
        if not token:
            return None

        # 1. Try Firebase Admin SDK
        try:
            import firebase_admin
            from firebase_admin import auth as admin_auth

            if not firebase_admin._apps:
                try:
                    firebase_admin.initialize_app(options={"projectId": "hiring-ai-4ae76"})
                except Exception:
                    pass

            if firebase_admin._apps:
                decoded = admin_auth.verify_id_token(token, check_revoked=False)
                return {
                    "uid": decoded.get("uid") or decoded.get("user_id"),
                    "email": (decoded.get("email") or "").lower(),
                    "name": decoded.get("name") or decoded.get("email"),
                    "firebase": decoded,
                    "auth_provider": "firebase_admin",
                }
        except Exception as ex:
            logger.debug(f"[Firebase Auth] Admin SDK verify attempt: {ex}")

        # 2. Verify via Google Official id_token.verify_firebase_token (Public x509 certs)
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token

            req = google_requests.Request()
            decoded = google_id_token.verify_firebase_token(
                token,
                req,
                audience="hiring-ai-4ae76",
            )
            if decoded:
                email = decoded.get("email") or decoded.get("firebase", {}).get("identities", {}).get("email", [None])[0]
                uid = decoded.get("user_id") or decoded.get("sub") or decoded.get("uid")
                return {
                    "uid": uid,
                    "email": (email or "").lower(),
                    "name": decoded.get("name") or email,
                    "firebase": decoded,
                    "auth_provider": "google_verify_firebase_token",
                }
        except Exception as ex:
            logger.warning(f"[Firebase Auth] verify_firebase_token failed: {ex}")

        # 3. Verify via Google Public Token Info API (OAuth fallback)
        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    uid = data.get("user_id") or data.get("sub")
                    email = data.get("email")
                    if uid and email:
                        return {
                            "uid": uid,
                            "email": email.lower(),
                            "name": data.get("name") or data.get("email"),
                            "auth_provider": "google_oauth2_tokeninfo",
                        }
        except Exception as ex:
            logger.warning(f"[Firebase Auth] Tokeninfo verification failed: {ex}")

        return None
