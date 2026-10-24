import unittest
from unittest.mock import patch

import main


class CompatibilityAddonTests(unittest.TestCase):
    def test_manifest_has_no_lossless_device_gate(self):
        import asyncio

        response = asyncio.run(main.manifest())
        self.assertNotIn("checkValidLossless", response.body.decode())
        self.assertIn('"resources":["search","stream"]', response.body.decode())

    @patch("main.upstream_get")
    def test_stream_preserves_upstream_metadata(self, upstream_get):
        import asyncio
        from starlette.requests import Request

        upstream_get.return_value = {
            "url": "https://example.invalid/audio.flac",
            "format": "flac",
            "quality": "Hi-Res Lossless",
            "atmos": True,
        }
        request = Request({"type": "http", "method": "GET", "path": "/stream/a", "query_string": b"quality=hires"})
        response = asyncio.run(main.stream("track-1", request))
        self.assertEqual(response.status_code, 200)
        self.assertIn('"atmos":true', response.body.decode())
        self.assertIn('"format":"flac"', response.body.decode())


if __name__ == "__main__":
    unittest.main()
