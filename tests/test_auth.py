import unittest
from unittest.mock import patch, MagicMock

from apigee.auth import get_access_token_for_sso

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.auth = MagicMock()
        self.username = "test_user"
        self.password = "test_password"
        self.oauth_url = "https://example.com/oauth"
        self.post_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.session = MagicMock()

    @patch("apigee.auth.validate_refresh_token")
    @patch("apigee.auth.get_sso_temporary_authentication_code")
    @patch("builtins.open")
    def test_get_access_token_for_sso_no_refresh_token(self, mock_open, mock_get_sso_temporary_authentication_code, mock_validate_refresh_token):
        mock_validate_refresh_token.return_value = None
        mock_get_sso_temporary_authentication_code.return_value = "test_passcode"

        response_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token"
        }
        self.session.post.return_value.json.return_value = response_data

        result = get_access_token_for_sso(
            self.auth, self.username, self.password, self.oauth_url, self.post_headers, self.session, None
        )

        mock_get_sso_temporary_authentication_code.assert_called_once_with(f"https://{self.auth.zonename}.login.apigee.com/passcode")
        self.session.post.assert_called_once_with(
            f"https://{self.auth.zonename}.login.apigee.com/oauth/token", headers=self.post_headers, data="passcode=test_passcode&grant_type=password&response_type=token"
        )
        self.assertEqual(result, response_data)
        # mock_open.assert_not_called()
        mock_open.assert_called_once_with('/home/mdelotavo/.apigee/refresh_token', 'w')

    @patch("apigee.auth.validate_refresh_token")
    @patch("builtins.open")
    def test_get_access_token_for_sso_with_refresh_token(self, mock_open, mock_validate_refresh_token):
        mock_validate_refresh_token.return_value = "test_refresh_token"

        response_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token"
        }
        self.session.post.return_value.json.return_value = response_data

        result = get_access_token_for_sso(
            self.auth, self.username, self.password, self.oauth_url, self.post_headers, self.session, None
        )

        self.session.post.assert_called_once_with(
            f"https://{self.auth.zonename}.login.apigee.com/oauth/token", headers=self.post_headers, data="grant_type=refresh_token&refresh_token=test_refresh_token"
        )
        self.assertEqual(result, response_data)
        # mock_open.assert_called_once_with('/root/.apigee/refresh_token', 'w')
        mock_open.assert_not_called()

if __name__ == '__main__':
    unittest.main()