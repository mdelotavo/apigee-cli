import base64
import gnupg
import sys

# Constants
ENCRYPTED_HEADER_BEGIN = "-----BEGIN ENCRYPTED APIGEE CLI MESSAGE-----"
ENCRYPTED_HEADER_END = "-----END ENCRYPTED APIGEE CLI MESSAGE-----"


def _safe_base64_decode(data: str) -> bytes:
    """
    Safely decodes a base64 string, adding missing padding if necessary.
    Strips whitespace and newlines to maintain backward compatibility.
    """
    data = data.strip().replace("\n", "")
    missing_padding = len(data) % 4
    if missing_padding:
        data += "=" * (4 - missing_padding)
    return base64.b64decode(data)


class _EncryptionHelper:
    """
    Internal helper for GPG encryption and decryption.
    """

    def __init__(self, secret: str):
        self.secret = secret
        self.gpg = gnupg.GPG()

    def encrypt(self, message: str, encoded: bool = True) -> str:
        """
        Encrypts a message using symmetric AES256 GPG encryption.
        Optionally returns base64-encoded result.
        Matches original behavior (no header/footer added).
        """
        try:
            encrypted = self.gpg.encrypt(
                message, symmetric="AES256", passphrase=self.secret, recipients=None
            )
            if not encrypted.ok:
                raise ValueError(f"GPG encryption failed: {encrypted.status}")
            result = str(encrypted)
            if encoded:
                result = base64.b64encode(result.encode()).decode()
            return result
        except Exception as e:
            sys.exit(f"Encryption error: {e}")

    def decrypt(self, message: str, encoded: bool = True) -> str:
        """
        Decrypts a message using symmetric AES256 GPG decryption.
        Returns empty string if message has no encrypted header.
        """
        if not has_encrypted_header(message):
            return ""
        try:
            # Strip header/footer for backward compatibility
            payload = message[len(ENCRYPTED_HEADER_BEGIN) : -len(ENCRYPTED_HEADER_END)]
            if encoded:
                payload_bytes = _safe_base64_decode(payload)
                payload = payload_bytes.decode()
            decrypted = self.gpg.decrypt(payload, passphrase=self.secret)
            if not decrypted.ok:
                raise ValueError(f"GPG decryption failed: {decrypted.status}")
            return str(decrypted)
        except Exception as e:
            sys.exit(f"Decryption error: {e}")


# ---------------------------
# Public API (Backward Compatible)
# ---------------------------

def encrypt_message_with_gpg(secret: str, message: str, encoded: bool = True) -> str:
    helper = _EncryptionHelper(secret)
    return helper.encrypt(message, encoded=encoded)


def decrypt_message_with_gpg(secret: str, message: str, encoded: bool = True) -> str:
    helper = _EncryptionHelper(secret)
    return helper.decrypt(message, encoded=encoded)


def has_encrypted_header(message: str) -> bool:
    if not isinstance(message, str):
        return False
    return message.startswith(ENCRYPTED_HEADER_BEGIN) and message.endswith(ENCRYPTED_HEADER_END)
