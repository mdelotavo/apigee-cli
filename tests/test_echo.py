import unittest
from unittest.mock import patch
from apigee.console import echo

class TestEcho(unittest.TestCase):
    @patch('builtins.print')
    @patch('sys.exit')
    def test_echo_silent(self, mock_exit, mock_print):
        echo('Hello', make_silent=True, exit_status=1)
        mock_print.assert_not_called()
        mock_exit.assert_called_once_with(1)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_echo_not_silent(self, mock_exit, mock_print):
        echo('Hello', make_silent=False)
        mock_print.assert_called_once_with('Hello', end='\n', flush=False)
        mock_exit.assert_not_called()

    @patch('builtins.print')
    @patch('sys.exit')
    def test_echo_verbosity(self, mock_exit, mock_print):
        echo('Hello', current_verbosity=1, expected_verbosity=0)
        mock_print.assert_called_once_with('Hello', end='\n', flush=False)
        mock_exit.assert_not_called()

    @patch('builtins.print')
    @patch('sys.exit')
    def test_echo_no_verbosity(self, mock_exit, mock_print):
        echo('Hello', current_verbosity=0, expected_verbosity=1)
        mock_print.assert_not_called()
        mock_exit.assert_not_called()

if __name__ == '__main__':
    unittest.main()