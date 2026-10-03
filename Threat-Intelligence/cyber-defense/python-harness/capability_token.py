import hmac
import hashlib
import json
import time
import base64
from typing import Dict, List, Optional, Any

class CapabilityToken:
    """
    Cryptographically signed, caveat-bounded capability token (Macaroon-inspired).
    Enforces Principle of Least Authority (PoLA) with strict TTL and path binding.
    """
    def __init__(self, root_key: bytes, identifier: str, target_service: str):
        self.root_key = root_key
        self.identifier = identifier
        self.target_service = target_service
        self.caveats: List[Dict[str, Any]] = []
        self._tag = self._compute_initial_tag()

    def _compute_initial_tag(self) -> bytes:
        message = f"id:{self.identifier}|srv:{self.target_service}".encode('utf-8')
        return hmac.new(self.root_key, message, hashlib.sha256).digest()

    def add_caveat(self, predicate: str, value: Any) -> 'CapabilityToken':
        """Attenuates the token by appending a first-party caveat and hashing the new tag."""
        caveat = {"predicate": predicate, "value": value}
        self.caveats.append(caveat)
        caveat_bytes = json.dumps(caveat, sort_keys=True).encode('utf-8')
        self._tag = hmac.new(self._tag, caveat_bytes, hashlib.sha256).digest()
        return self

    def serialize(self) -> str:
        """Serializes the token to a portable base64 string."""
        payload = {
            "identifier": self.identifier,
            "target_service": self.target_service,
            "caveats": self.caveats,
            "signature": base64.b64encode(self._tag).decode('ascii')
        }
        return base64.b64encode(json.dumps(payload).encode('utf-8')).decode('ascii')

    @classmethod
    def verify_and_parse(cls, serialized_token: str, root_key: bytes, context: Dict[str, Any]) -> bool:
        """
        Verifies cryptographic integrity and evaluates all runtime caveats against current execution context.
        """
        try:
            raw_json = base64.b64decode(serialized_token.encode('ascii')).decode('utf-8')
            payload = json.loads(raw_json)
            
            # Reconstruct and verify cryptographic HMAC chain
            current_tag = hmac.new(
                root_key, 
                f"id:{payload['identifier']}|srv:{payload['target_service']}".encode('utf-8'),
                hashlib.sha256
            ).digest()

            for caveat in payload["caveats"]:
                caveat_bytes = json.dumps(caveat, sort_keys=True).encode('utf-8')
                current_tag = hmac.new(current_tag, caveat_bytes, hashlib.sha256).digest()

            claimed_signature = base64.b64decode(payload["signature"].encode('ascii'))
            if not hmac.compare_digest(current_tag, claimed_signature):
                return False  # Signature mismatch or tampering

            # Evaluate Caveat Predicates
            now = time.time()
            for caveat in payload["caveats"]:
                pred = caveat["predicate"]
                val = caveat["value"]

                if pred == "expires_at":
                    if now > float(val):
                        return False  # Token expired
                elif pred == "allowed_method":
                    if context.get("method") != val:
                        return False
                elif pred == "allowed_path_prefix":
                    if not context.get("path", "").startswith(val):
                        return False
                elif pred == "bound_client_ip":
                    if context.get("client_ip") != val:
                        return False
                elif pred == "max_calls":
                    if context.get("invocation_count", 0) > int(val):
                        return False

            return True
        except Exception:
            return False
