import unittest

from apigee.encryption_utils import (ENCRYPTED_HEADER_BEGIN, ENCRYPTED_HEADER_END,
                           decrypt_message_with_gpg, encrypt_message_with_gpg)

class TestEncryptionUtils(unittest.TestCase):
    ciphertext = None

    @classmethod
    def setUpClass(cls):
        cls.secret = "password123!"
        cls.plaintext = "Hello, World!"
        cls.ciphertext = f"{ENCRYPTED_HEADER_BEGIN}{encrypt_message_with_gpg(cls.secret, cls.plaintext)}{ENCRYPTED_HEADER_END}"

    def test_decrypt_message_with_gpg_encoded(self):
        result = decrypt_message_with_gpg(self.secret, self.ciphertext, encoded=True)
        self.assertEqual(result, self.plaintext)

    def test_decrypt_message_with_gpg_encoded_plaintext_none(self):
        result = decrypt_message_with_gpg(self.secret, None, encoded=True)
        self.assertEqual(result, "")

    def test_decrypt_message_with_gpg_encoded_plaintext_empty(self):
        result = decrypt_message_with_gpg(self.secret, "", encoded=True)
        self.assertEqual(result, "")

    def test_decrypt_message_with_gpg_no_encrypted_header(self):
        result = decrypt_message_with_gpg(self.secret, self.plaintext)
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()
