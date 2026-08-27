"""
Tests unitarios para configuración segura, accessor de secretos y sanitización (V-01, V-04, V-15, V-16).
"""

import unittest
from pathlib import Path
from config.settings import (
    get_secret, scrub_secrets, load_env_file, _PRIVATE_SECRETS
)


class TestSettingsAndSecurity(unittest.TestCase):
    def test_scrub_secrets(self):
        # Tokens de Google, OpenAI, GitHub, HuggingFace
        raw_text = "Google AIzaSyB12345678901234567890, OpenAI sk-1234567890abcdef1234567890, GitHub ghp_1234567890abcdef1234567890"
        scrubbed = scrub_secrets(raw_text)
        self.assertNotIn("AIzaSyB12345678901234567890", scrubbed)
        self.assertNotIn("sk-1234567890abcdef1234567890", scrubbed)
        self.assertNotIn("ghp_1234567890abcdef1234567890", scrubbed)
        self.assertIn("[REDACTED]", scrubbed)

    def test_get_secret_accessor(self):
        _PRIVATE_SECRETS["TEST_INTERNAL_KEY"] = "secret_value_12345"
        val = get_secret("TEST_INTERNAL_KEY")
        self.assertEqual(val, "secret_value_12345")

    def test_symlink_rejection_in_load_env(self):
        # Simular un symlink
        fake_link = Path("/tmp/fake_env_symlink")
        fake_target = Path("/tmp/fake_env_target")
        fake_target.write_text("DUMMY=1", encoding="utf-8")
        if fake_link.exists() or fake_link.is_symlink():
            fake_link.unlink()
        fake_link.symlink_to(fake_target)

        res = load_env_file(fake_link)
        self.assertEqual(res, {})

        fake_link.unlink(missing_ok=True)
        fake_target.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
