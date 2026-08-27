"""
Tests unitarios para escritura atómica, backups rotativos y validación de sintaxis (V-05, V-18, V-19).
"""

import unittest
import json
import os
from pathlib import Path
from src.core.engine_injector import atomic_write, _validate_json, _validate_yaml, SecurityError


class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("/tmp/floydia_test_atomic")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.target_file = self.test_dir / "test_config.json"

    def tearDown(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_atomic_write_success_and_permissions(self):
        valid_json = '{"app": "floydia", "version": 9.5}'
        out_path = atomic_write(self.target_file, valid_json, mode=0o600, validator=_validate_json)
        self.assertTrue(out_path.exists())
        self.assertEqual(out_path.read_text(encoding="utf-8"), valid_json)
        
        # Verificar permisos 600
        mode = out_path.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_atomic_write_backup_rotation(self):
        # Escribir v1
        atomic_write(self.target_file, '{"v": 1}', validator=_validate_json)
        # Escribir v2 (genera backup)
        atomic_write(self.target_file, '{"v": 2}', validator=_validate_json)
        
        backups = list(self.test_dir.glob("test_config.json.*.bak"))
        self.assertGreaterEqual(len(backups), 1)

    def test_atomic_write_aborts_on_invalid_syntax(self):
        atomic_write(self.target_file, '{"v": 1}', validator=_validate_json)
        
        # Intentar escribir JSON inválido
        invalid_json = '{"v": 2, syntax_error}'
        with self.assertRaises(Exception):
            atomic_write(self.target_file, invalid_json, validator=_validate_json)
        
        # El archivo original debe permanecer intacto
        self.assertEqual(self.target_file.read_text(encoding="utf-8"), '{"v": 1}')

    def test_atomic_write_rejects_symlink(self):
        real_file = self.test_dir / "real.json"
        real_file.write_text('{"real": true}', encoding="utf-8")
        link_file = self.test_dir / "link.json"
        link_file.symlink_to(real_file)

        with self.assertRaises(SecurityError):
            atomic_write(link_file, '{"hacked": true}')


if __name__ == "__main__":
    unittest.main()
