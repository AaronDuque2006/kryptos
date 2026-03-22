import logging
import unittest
from dataclasses import dataclass
from typing import Any, cast

from core.crypto import VaultCrypto
from core.logging_config import LOGGER_NAME
from services.vault_service import VaultService


@dataclass
class CredentialStub:
    id: int
    user_id: int
    title: str
    nonce: bytes
    encrypted_payload: bytes
    title_nonce: bytes | None = None
    encrypted_title: bytes | None = None


class CredentialRepositoryStub:
    def __init__(self):
        self.created_items = []
        self.credentials = []
        self.updated_titles = []
        self.deleted_calls = []

    def create_credential(self, **kwargs):
        self.created_items.append(kwargs)
        return kwargs

    def get_credentials_by_user(self, user_id: int):
        return [c for c in self.credentials if c.user_id == user_id]

    def update_title_encryption(
        self,
        credential_id: int,
        user_id: int,
        placeholder_title: str,
        title_nonce: bytes,
        encrypted_title: bytes,
    ):
        self.updated_titles.append(
            {
                "credential_id": credential_id,
                "user_id": user_id,
                "placeholder_title": placeholder_title,
                "title_nonce": title_nonce,
                "encrypted_title": encrypted_title,
            }
        )
        return True

    def delete_credential(self, credential_id: int, user_id: int):
        self.deleted_calls.append({"credential_id": credential_id, "user_id": user_id})
        return True


class VaultServiceSecurityTests(unittest.TestCase):
    def setUp(self):
        self.repo = CredentialRepositoryStub()
        self.crypto = VaultCrypto("master-pass", b"0123456789abcdef")
        self.service = VaultService(
            self.crypto,
            cast(Any, self.repo),
            current_user_id=7,
        )

    def test_add_entry_stores_encrypted_title(self):
        self.service.add_entry(
            title="Github",
            username_used="alice",
            password_used="secret",
            url="https://github.com",
            notes="work",
        )

        self.assertEqual(len(self.repo.created_items), 1)
        created = self.repo.created_items[0]
        self.assertIsNotNone(created["title_nonce"])
        self.assertIsNotNone(created["encrypted_title"])
        self.assertEqual(created["title"], "[encrypted-title]")

    def test_get_entries_uses_encrypted_title_when_available(self):
        payload_nonce, payload = self.crypto.encrypt_credential(
            {
                "username": "alice",
                "password": "secret",
                "url": "",
                "notes": "",
            }
        )
        title_nonce, encrypted_title = self.crypto.encrypt_credential({"title": "Bank"})

        self.repo.credentials = [
            CredentialStub(
                id=1,
                user_id=7,
                title="LEGACY",
                nonce=payload_nonce,
                encrypted_payload=payload,
                title_nonce=title_nonce,
                encrypted_title=encrypted_title,
            )
        ]

        entries = self.service.get_all_entries_decrypted()
        self.assertEqual(entries[0]["title"], "Bank")
        self.assertEqual(len(self.repo.updated_titles), 0)

    def test_get_entries_migrates_legacy_plaintext_title(self):
        payload_nonce, payload = self.crypto.encrypt_credential(
            {
                "username": "alice",
                "password": "secret",
                "url": "",
                "notes": "",
            }
        )
        self.repo.credentials = [
            CredentialStub(
                id=2,
                user_id=7,
                title="LegacyTitle",
                nonce=payload_nonce,
                encrypted_payload=payload,
            )
        ]

        entries = self.service.get_all_entries_decrypted()
        self.assertEqual(entries[0]["title"], "LegacyTitle")
        self.assertEqual(len(self.repo.updated_titles), 1)
        self.assertEqual(self.repo.updated_titles[0]["user_id"], 7)

    def test_delete_entry_scopes_to_current_user(self):
        self.service.delete_entry(credential_id=9)
        self.assertEqual(self.repo.deleted_calls, [{"credential_id": 9, "user_id": 7}])

    def test_integrity_error_log_does_not_leak_secret_content(self):
        logger = logging.getLogger(LOGGER_NAME)

        payload_nonce, payload = self.crypto.encrypt_credential(
            {
                "username": "alice",
                "password": "super-secret-password",
                "url": "",
                "notes": "",
            }
        )
        tampered_payload = payload[:-1] + bytes([payload[-1] ^ 0x01])
        self.repo.credentials = [
            CredentialStub(
                id=3,
                user_id=7,
                title="Bank",
                nonce=payload_nonce,
                encrypted_payload=tampered_payload,
            )
        ]

        with self.assertLogs(logger, level="WARNING") as captured:
            entries = self.service.get_all_entries_decrypted()

        self.assertEqual(entries, [])
        combined_logs = "\n".join(captured.output)
        self.assertIn("vault_integrity_error", combined_logs)
        self.assertNotIn("super-secret-password", combined_logs)
        self.assertNotIn("Integridad comprometida", combined_logs)


if __name__ == "__main__":
    unittest.main()
