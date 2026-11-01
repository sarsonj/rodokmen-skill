import contextlib
import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ebadatelna


class RetryStatusTests(unittest.TestCase):
    def test_transient_http_error_reports_retry_and_returns_response(self):
        error = urllib.error.HTTPError("https://example.test", 503, "unavailable", {}, None)
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b"ok"
        response.geturl.return_value = "https://example.test"
        output = io.StringIO()

        with mock.patch.object(ebadatelna.time, "sleep"), \
                mock.patch.object(ebadatelna._op, "open", side_effect=[error, response]), \
                contextlib.redirect_stderr(output):
            body, url = ebadatelna.get("https://example.test")

        self.assertEqual((body, url), ("ok", "https://example.test"))
        self.assertIn("HTTP 503", output.getvalue())
        self.assertIn("další pokus za 2 s (2/4)", output.getvalue())

    def test_timeout_reports_retry(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b"ok"
        response.geturl.return_value = "https://example.test"
        output = io.StringIO()

        with mock.patch.object(ebadatelna.time, "sleep"), \
                mock.patch.object(ebadatelna._op, "open", side_effect=[TimeoutError("timed out"), response]), \
                contextlib.redirect_stderr(output):
            body, _ = ebadatelna.get("https://example.test")

        self.assertEqual(body, "ok")
        self.assertIn("portál neodpovídá", output.getvalue())
        self.assertIn("další pokus za 2 s (2/4)", output.getvalue())


if __name__ == "__main__":
    unittest.main()
