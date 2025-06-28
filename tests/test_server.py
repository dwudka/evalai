import os
import json
import unittest
from app.server import app, fake_api_check

class ServerTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_add_watch(self):
        payload = {
            "campsite": "Crystal Cove",
            "campsite_type": "cottage",
            "check_time": "08:00",
            "email": "test@example.com"
        }
        response = self.client.post('/watch', json=payload)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('message', data)

    def test_fake_api(self):
        # fake_api_check should return bool
        result = fake_api_check('Site', 'type')
        self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()
