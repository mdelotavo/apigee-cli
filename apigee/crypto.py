import base64
import gnupg

ENCRYPTED_HEADER_BEGIN = "-----BEGIN ENCRYPTED APIGEE CLI MESSAGE-----"
ENCRYPTED_HEADER_END = "-----END ENCRYPTED APIGEE CLI MESSAGE-----"


def _gpg():
    return gnupg.GPG()


def encrypt_message(secret, message, encoded=True):
    encrypted = _gpg().encrypt(message, symmetric="AES256", passphrase=secret, recipients=None)
    result = str(encrypted)

    if not encoded:
        return result

    return base64.b64encode(result.encode()).decode()


def is_encrypted(message):
    return message.startswith(ENCRYPTED_HEADER_BEGIN) and message.endswith(ENCRYPTED_HEADER_END)


def decrypt_message(secret, message, encoded=True):
    if not is_encrypted(message):
        return ""

    payload = message[len(ENCRYPTED_HEADER_BEGIN):-len(ENCRYPTED_HEADER_END)]

    if encoded:
        payload = base64.b64decode(payload).decode()

    return str(_gpg().decrypt(payload, passphrase=secret))
