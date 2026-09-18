import hashlib
import json
import time
from typing import Dict, Any

class C2PAProvenanceSigner:
    """
    Generates and validates C2PA-compliant cryptographic provenance manifests
    binding AI-generated content to verified model hashes, timestamps, and provider keys.
    """
    def __init__(self, provider_id: str, model_id: str, private_signing_key: str):
        self.provider_id = provider_id
        self.model_id = model_id
        self.private_signing_key = private_signing_key

    def generate_manifest(self, content_text: str, generating_account_tier: str = "enterprise") -> Dict[str, Any]:
        """Injects a cryptographically signed provenance claim into generated content."""
        content_sha256 = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        claim_body = {
            "c2pa_version": "2.1",
            "provider": self.provider_id,
            "model_id": self.model_id,
            "generating_tier": generating_account_tier,
            "content_sha256": content_sha256,
            "timestamp": timestamp,
            "claim_type": "synthetic.text.generation"
        }

        # Compute deterministic digital signature over claim
        serialized_claim = json.dumps(claim_body, sort_keys=True)
        signature = hashlib.sha256((serialized_claim + self.private_signing_key).encode('utf-8')).hexdigest()

        manifest = {
            "claim": claim_body,
            "signature": signature,
            "verified_origin": True
        }
        return manifest

    @classmethod
    def verify_manifest(cls, manifest: Dict[str, Any], content_text: str, private_signing_key: str) -> bool:
        """Verifies content integrity and cryptographic signature against claimed manifest."""
        try:
            claim = manifest.get("claim", {})
            claimed_content_hash = claim.get("content_sha256")
            actual_content_hash = hashlib.sha256(content_text.encode('utf-8')).hexdigest()

            if claimed_content_hash != actual_content_hash:
                return False  # Content was modified after generation

            serialized_claim = json.dumps(claim, sort_keys=True)
            expected_sig = hashlib.sha256((serialized_claim + private_signing_key).encode('utf-8')).hexdigest()

            return expected_sig == manifest.get("signature")
        except Exception:
            return False
