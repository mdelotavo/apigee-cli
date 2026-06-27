import unittest
from unittest.mock import MagicMock, patch

from apigee.auth import (
  get_access_token_for_sso,
  APIGEE_CLI_REFRESH_TOKEN_FILE,
  APIGEE_SAML_LOGIN_URL,
  APIGEE_ZONENAME_OAUTH_URL,
)


class TestAuth(unittest.TestCase):

    def setUp(self):
        self.auth = MagicMock()
        self.auth.zonename = "test-zone"

        self.session = MagicMock()

    @patch("apigee.auth.validate_refresh_token")
    @patch("apigee.auth.get_sso_temporary_authentication_code")
    @patch("builtins.open")
    def test_get_access_token_for_sso_no_refresh_token(
      self,
      mock_open,
      mock_get_sso_temporary_authentication_code,
      mock_validate_refresh_token,
    ):
        # No refresh token available
        mock_validate_refresh_token.return_value = None
        mock_get_sso_temporary_authentication_code.return_value = "test_passcode"

        response_data = {
          "access_token": "test_access_token",
          "refresh_token": "test_refresh_token",
        }

        mock_response = MagicMock()
        mock_response.json.return_value = response_data
        self.session.post.return_value = mock_response

        result = get_access_token_for_sso(self.auth, self.session, None)

        expected_passcode_url = APIGEE_SAML_LOGIN_URL.format(zonename="test-zone")
        mock_get_sso_temporary_authentication_code.assert_called_once_with(expected_passcode_url)

        expected_oauth_url = APIGEE_ZONENAME_OAUTH_URL.format(zonename="test-zone")

        self.session.post.assert_called_once()
        args, kwargs = self.session.post.call_args

        self.assertEqual(args[0], expected_oauth_url)
        self.assertEqual(kwargs["data"], "passcode=test_passcode&;grant_type=password&;response_type=token")

        self.assertEqual(result, response_data)

        # Verify refresh token is written
        mock_open.assert_called_once_with(APIGEE_CLI_REFRESH_TOKEN_FILE, "w")
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.write.assert_called_once_with("test_refresh_token")

    @patch("apigee.auth.validate_refresh_token")
    @patch("builtins.open")
    def test_get_access_token_for_sso_with_refresh_token(
      self,
      mock_open,
      mock_validate_refresh_token,
    ):
        # Refresh token exists
        mock_validate_refresh_token.return_value = "test_refresh_token"

        response_data = {
          "access_token": "test_access_token",
          "refresh_token": "test_refresh_token",
        }

        mock_response = MagicMock()
        mock_response.json.return_value = response_data
        self.session.post.return_value = mock_response

        result = get_access_token_for_sso(self.auth, self.session, None)

        expected_oauth_url = APIGEE_ZONENAME_OAUTH_URL.format(zonename="test-zone")

        self.session.post.assert_called_once()
        args, kwargs = self.session.post.call_args

        self.assertEqual(args[0], expected_oauth_url)
        self.assertEqual(kwargs["data"], "grant_type=refresh_token&;refresh_token=test_refresh_token")

        self.assertEqual(result, response_data)

        # No file write when using refresh token
        mock_open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
