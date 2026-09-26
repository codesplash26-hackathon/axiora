import json
import logging
from typing import Any, Dict, List
from starlette.types import ASGIApp, Scope, Receive, Send

from backend.privacy_rules import (
    NETWORK_IDENTIFIER_HEADERS,
    sanitize_patient_payload
)

logger = logging.getLogger("cardiorecourse.privacy")


MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MB maximum body size limit


class PrivacySanitizationMiddleware:
    """
    Stateless Edge De-Identification ASGI Middleware.
    
    Enforces HIPAA Safe Harbor (45 CFR § 164.514) and Sri Lanka PDPA No. 9 of 2022
    by stripping Protected Health Information (PHI) and client network signatures
    before inbound payloads reach application endpoints or the ML inference engine.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path.startswith("/auth") or path.startswith("/api/auth") or path.startswith("/doctor") or path.startswith("/api/doctor"):
            await self.app(scope, receive, send)
            return

        # 1. Network-Level Identifier Stripping
        original_headers = scope.get("headers", [])
        cleaned_headers = []
        for k, v in original_headers:
            k_bytes = k.lower() if isinstance(k, bytes) else str(k).lower().encode("utf-8")
            if k_bytes not in NETWORK_IDENTIFIER_HEADERS:
                cleaned_headers.append((k, v))
        scope["headers"] = cleaned_headers

        # 2. Client Socket Anonymization
        scope["client"] = ("0.0.0.0", 0)

        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["is_deidentified"] = True
        scope["state"]["purged_phi_keys"] = []

        # 3. Payload Body De-Identification with 2MB DoS Guard
        body_chunks = []
        more_body = True
        total_bytes = 0
        while more_body:
            message = await receive()
            chunk = message.get("body", b"")
            total_bytes += len(chunk)
            if total_bytes > MAX_BODY_BYTES:
                logger.warning(
                    f"[PrivacySanitizer] Inbound payload exceeded {MAX_BODY_BYTES} bytes limit ({total_bytes} bytes). Rejecting with 413."
                )
                await send({
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"x-privacy-policy", b"HIPAA-SafeHarbor,SriLanka-PDPA-2022"),
                    ],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail": "Payload Too Large: Maximum allowed request body is 2MB."}',
                    "more_body": False,
                })
                return

            body_chunks.append(chunk)
            more_body = message.get("more_body", False)

        raw_body = b"".join(body_chunks)
        sanitized_body = raw_body
        purged_keys: List[str] = []

        if raw_body:
            try:
                decoded_text = raw_body.decode("utf-8")
                payload = json.loads(decoded_text)
                
                if isinstance(payload, dict):
                    sanitized_payload, purged_keys = sanitize_patient_payload(payload)
                    scope["state"]["purged_phi_keys"] = purged_keys
                    if purged_keys:
                        logger.info(
                            f"[PrivacySanitizer] Purged {len(purged_keys)} direct PHI identifiers: {purged_keys}"
                        )
                    sanitized_body = json.dumps(sanitized_payload).encode("utf-8")
                else:
                    sanitized_body = raw_body

            except Exception as exc:
                # Fail-closed security: reject malformed or non-JSON payloads with 400 Bad Request
                # prevents raw un-sanitized PHI payloads from leaking downstream
                logger.warning(f"[PrivacySanitizer] Malformed non-JSON payload rejected: {str(exc)}")
                await send({
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"x-privacy-policy", b"HIPAA-SafeHarbor,SriLanka-PDPA-2022"),
                    ],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail": "Bad Request: Malformed JSON payload cannot be safely sanitized."}',
                    "more_body": False,
                })
                return

        # 4. Construct Sanitized In-Memory Stream Receive Callable
        stream_sent = False

        async def sanitized_receive() -> Dict[str, Any]:
            nonlocal stream_sent
            if not stream_sent:
                stream_sent = True
                return {
                    "type": "http.request",
                    "body": sanitized_body,
                    "more_body": False
                }
            return {
                "type": "http.request",
                "body": b"",
                "more_body": False
            }

        # 5. Append Privacy Compliance Response Headers
        async def custom_send(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-privacy-policy", b"HIPAA-SafeHarbor,SriLanka-PDPA-2022"))
                resp_headers.append((b"x-phi-purged-count", str(len(purged_keys)).encode("utf-8")))
                message["headers"] = resp_headers
            await send(message)

        await self.app(scope, sanitized_receive, custom_send)