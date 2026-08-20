import unittest

from fastapi.testclient import TestClient

from api.main import create_app


class UploadApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_upload_without_description_returns_frontend_payload(self):
        response = self.client.post(
            "/upload",
            files={"file": ("hello.txt", b"hello world", "text/plain")},
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["file_name"], "hello.txt")
        self.assertEqual(payload["description"], "")
        self.assertEqual(payload["chunks_added"], 1)
        self.assertEqual(payload["status"], "success")
        self.assertIn("uploaded", payload["message"].lower())
        self.assertEqual(payload["content_preview"], "hello world")


if __name__ == "__main__":
    unittest.main()