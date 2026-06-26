import base64
import gnupg

ENCRYPTED_HEADER_BEGIN = "-----BEGIN ENCRYPTED APIGEE CLI MESSAGE-----"
ENCRYPTED_HEADER_END = "-----END ENCRYPTED APIGEE CLI MESSAGE-----"


def _gpg():
    return gnupg.GPG()


def encrypt(secret, message, encoded=True):
    encrypted = _gpg().encrypt(message, symmetric="AES256", passphrase=secret)

    result = str(encrypted)
    if not encoded:
        return result

    return base64.b64encode(result.encode()).decode()


def has_encrypted_header(message):
    return isinstance(message, str) and (message.startswith(ENCRYPTED_HEADER_BEGIN) and message.endswith(ENCRYPTED_HEADER_END))


def decrypt(secret, message, encoded=True):
    if not has_encrypted_header(message):
        return ""

    payload = message[len(ENCRYPTED_HEADER_BEGIN):-len(ENCRYPTED_HEADER_END)]

    if encoded:
        payload = base64.b64decode(payload).decode()

    decrypted = _gpg().decrypt(payload, passphrase=secret)
    return str(decrypted)
