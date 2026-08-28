"""
Manejador de Base de Datos SQLite para FloydIA AI Rankings & Local API Observatory.
Garantiza inmutabilidad con snapshots criptográficos SHA256, pragmas WAL concurrentes
y saneamiento estricto de secretos antes de persistir (Fix V-07, V-16).
"""

import sqlite3
import hashlib
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator
from config.settings import DB_PATH, scrub_secrets


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Crea o retorna conexión a la base de datos SQLite con soporte WAL y timeout seguro."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    # FIX V-07: PRAGMAs de concurrencia y seguridad
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Inicializa el esquema de la base de datos relacional."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Tabla de snapshots crudos de APIs (inmutable con SHA256)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots_raw (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                endpoint_url TEXT NOT NULL,
                payload TEXT NOT NULL,
                sha256_hash TEXT NOT NULL UNIQUE,
                fetch_status INTEGER NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Catálogo maestro de modelos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                tier TEXT NOT NULL, -- frontier, workhorse, coding, edge
                provider TEXT NOT NULL,
                context_window INTEGER DEFAULT 128000,
                max_output INTEGER DEFAULT 8192,
                is_free_tier BOOLEAN DEFAULT 0,
                input_cost_per_m REAL DEFAULT 0.0,
                output_cost_per_m REAL DEFAULT 0.0,
                supports_tools BOOLEAN DEFAULT 0,
                supports_vision BOOLEAN DEFAULT 0,
                supports_reasoning BOOLEAN DEFAULT 0,
                aliases_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Evaluaciones y benchmarks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL,
                source TEXT NOT NULL,
                benchmark_name TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                score REAL NOT NULL,
                unit TEXT DEFAULT 'points',
                rank_position INTEGER,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models (id)
            )
        """)
        
        # 4. Estado verificado de APIs Locales (Sonda)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS local_api_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_name TEXT NOT NULL,
                model_identifier TEXT NOT NULL,
                canonical_id TEXT,
                account_email TEXT,
                account_key TEXT,
                is_functional BOOLEAN NOT NULL,
                status_code INTEGER,
                status_message TEXT,
                latency_ms REAL,
                detected_context_window INTEGER,
                supports_tools BOOLEAN DEFAULT 0,
                supports_vision BOOLEAN DEFAULT 0,
                supports_reasoning BOOLEAN DEFAULT 0,
                is_free_tier BOOLEAN DEFAULT 0,
                cost_input_m REAL DEFAULT 0.0,
                cost_output_m REAL DEFAULT 0.0,
                verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Mediciones detalladas por pilar y procedencia (C-1 / D-3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_id TEXT NOT NULL,
                pillar TEXT NOT NULL,
                measured BOOLEAN NOT NULL DEFAULT 0,
                n_obs INTEGER NOT NULL DEFAULT 0,
                score REAL,
                source TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (canonical_id) REFERENCES models (id)
            )
        """)

        # 6. Grados de certeza de modelos (C-6 / D-3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_grades (
                canonical_id TEXT PRIMARY KEY,
                fci REAL,
                confidence REAL NOT NULL,
                grade TEXT NOT NULL,
                measured_pillars_count INTEGER NOT NULL DEFAULT 0,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (canonical_id) REFERENCES models (id)
            )
        """)

        # 7. Rankings públicos consolidados (D-1 / D-3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rankings (
                canonical_id TEXT PRIMARY KEY,
                global_rank INTEGER,
                fci REAL,
                ci_lower REAL,
                ci_upper REAL,
                confidence REAL NOT NULL,
                evidence_grade TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (canonical_id) REFERENCES models (id)
            )
        """)

        # 8. Sonda activa y micro-benchmarks locales (M-3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS probe_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_id TEXT NOT NULL,
                kind TEXT NOT NULL, -- canary, arithmetic, minihumaneval, json_follow
                ttft_ms REAL,
                total_ms REAL,
                ok BOOLEAN NOT NULL,
                error TEXT
            )
        """)

        # 9. Tabla de Nonces para verificación HMAC anti-replay (M-2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_nonces (
                nonce TEXT PRIMARY KEY,
                ts INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 10. Tabla de Eventos de Drift y Deprecación de APIs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drift_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                event_type TEXT NOT NULL, -- price_change, latency_degradation, context_window_change, deprecation_candidate
                metric_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                severity TEXT DEFAULT 'warning', -- info, warning, critical
                details_json TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_drift_model ON drift_events (model_id, detected_at)
        """)

        # Migraciones automáticas de columnas faltantes
        cursor.execute("PRAGMA table_info(local_api_checks)")
        lac_cols = [r["name"] for r in cursor.fetchall()]
        if "supports_reasoning" not in lac_cols:
            cursor.execute("ALTER TABLE local_api_checks ADD COLUMN supports_reasoning BOOLEAN DEFAULT 0")
        if "account_email" not in lac_cols:
            cursor.execute("ALTER TABLE local_api_checks ADD COLUMN account_email TEXT")
        if "account_key" not in lac_cols:
            cursor.execute("ALTER TABLE local_api_checks ADD COLUMN account_key TEXT")

        cursor.execute("PRAGMA table_info(models)")
        m_cols = [r["name"] for r in cursor.fetchall()]
        if "supports_reasoning" not in m_cols:
            cursor.execute("ALTER TABLE models ADD COLUMN supports_reasoning BOOLEAN DEFAULT 0")
        if "is_synthetic" not in m_cols:
            cursor.execute("ALTER TABLE models ADD COLUMN is_synthetic INTEGER DEFAULT 0")

        cursor.execute("PRAGMA table_info(evaluations)")
        e_cols = [r["name"] for r in cursor.fetchall()]
        if "provenance" not in e_cols:
            cursor.execute("ALTER TABLE evaluations ADD COLUMN provenance TEXT DEFAULT 'live'")
        if "run_date" not in e_cols:
            cursor.execute("ALTER TABLE evaluations ADD COLUMN run_date TEXT DEFAULT ''")
            cursor.execute("UPDATE evaluations SET run_date = DATE(recorded_at) WHERE run_date IS NULL OR run_date = ''")

        cursor.execute("""
            DELETE FROM evaluations WHERE id NOT IN (
                SELECT MAX(id) FROM evaluations
                GROUP BY model_id, benchmark_name, source, run_date
            )
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_evaluations_dedup
            ON evaluations (model_id, benchmark_name, source, run_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_checks_canonical ON local_api_checks (canonical_id)
        """)
        
        conn.commit()


def save_raw_snapshot(source: str, endpoint_url: str, payload_str: str, status_code: int = 200) -> str:
    """Guarda un snapshot crudo en SQLite asegurando deduplicación por SHA256 y scrub de secretos."""
    sanitized_payload = scrub_secrets(payload_str)
    sha256 = hashlib.sha256(sanitized_payload.encode("utf-8")).hexdigest()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO snapshots_raw (source, endpoint_url, payload, sha256_hash, fetch_status)
            VALUES (?, ?, ?, ?, ?)
        """, (source, endpoint_url, sanitized_payload, sha256, status_code))
        conn.commit()
    return sha256


def upsert_model(model_data: Dict[str, Any]):
    """Inserta o actualiza un modelo en el catálogo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO models (
                id, canonical_name, tier, provider, context_window, max_output,
                is_free_tier, input_cost_per_m, output_cost_per_m,
                supports_tools, supports_vision, supports_reasoning,
                aliases_json, is_synthetic, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                canonical_name=excluded.canonical_name,
                tier=excluded.tier,
                provider=excluded.provider,
                context_window=excluded.context_window,
                max_output=excluded.max_output,
                is_free_tier=excluded.is_free_tier,
                input_cost_per_m=excluded.input_cost_per_m,
                output_cost_per_m=excluded.output_cost_per_m,
                supports_tools=excluded.supports_tools,
                supports_vision=excluded.supports_vision,
                supports_reasoning=excluded.supports_reasoning,
                aliases_json=excluded.aliases_json,
                is_synthetic=excluded.is_synthetic,
                updated_at=CURRENT_TIMESTAMP
        """, (
            model_data["id"],
            model_data["canonical_name"],
            model_data.get("tier", "workhorse"),
            model_data.get("provider", "Unknown"),
            model_data.get("context_window", 128000),
            model_data.get("max_output", 8192),
            1 if model_data.get("is_free_tier") else 0,
            model_data.get("input_cost_per_m", 0.0),
            model_data.get("output_cost_per_m", 0.0),
            1 if model_data.get("supports_tools") else 0,
            1 if model_data.get("supports_vision") else 0,
            1 if model_data.get("supports_reasoning") else 0,
            json.dumps(model_data.get("aliases", [])),
            1 if model_data.get("is_synthetic") else 0
        ))
        conn.commit()


def save_evaluation(model_id: str, source: str, benchmark_name: str, score: float, category: str = "general", rank_position: Optional[int] = None, unit: str = "points", provenance: str = "live"):
    """Guarda una métrica de evaluación para un modelo con procedencia y fecha de corrida."""
    from datetime import date
    if provenance not in ("live", "snapshot", "fallback"):
        provenance = "live"
    run_date = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO evaluations (model_id, source, benchmark_name, category, score, unit, rank_position, provenance, run_date, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (model_id, source, benchmark_name, category, score, unit, rank_position, provenance, run_date))
        conn.commit()


def record_local_api_check(check_result: Dict[str, Any]):
    """Registra la comprobación de salud y capacidades de una API local sanitizando mensajes de error."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO local_api_checks (
                provider_name, model_identifier, canonical_id, account_email, account_key,
                is_functional, status_code, status_message, latency_ms, detected_context_window,
                supports_tools, supports_vision, supports_reasoning, is_free_tier, cost_input_m, cost_output_m
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            check_result["provider_name"],
            check_result["model_identifier"],
            check_result.get("canonical_id"),
            check_result.get("account_email"),
            check_result.get("account_key"),
            1 if check_result.get("is_functional") else 0,
            check_result.get("status_code", 200),
            scrub_secrets(check_result.get("status_message", "OK")),
            check_result.get("latency_ms", 0.0),
            check_result.get("detected_context_window", 128000),
            1 if check_result.get("supports_tools") else 0,
            1 if check_result.get("supports_vision") else 0,
            1 if check_result.get("supports_reasoning") else 0,
            1 if check_result.get("is_free_tier") else 0,
            check_result.get("cost_input_m", 0.0),
            check_result.get("cost_output_m", 0.0)
        ))
        conn.commit()


def get_latest_local_verified_models() -> List[Dict[str, Any]]:
    """Obtiene el último estado verificado de cada API local con JOIN tolerante (canonical_id o model_identifier)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, m.canonical_name, m.tier, m.is_synthetic
            FROM local_api_checks c
            LEFT JOIN models m ON (c.canonical_id = m.id OR c.model_identifier = m.id)
            WHERE c.id IN (
                SELECT MAX(id) FROM local_api_checks GROUP BY provider_name, model_identifier
            )
            ORDER BY c.is_functional DESC, c.latency_ms ASC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_local_functional_model_keys() -> Dict[str, Dict[str, Any]]:
    """
    Retorna un diccionario mapeando todas las posibles claves (canonical_id, model_identifier, alias)
    para cada check local funcional, evitando fallos de join de clave única.
    Solo cuenta modelos realmente sondados con latencia (excluye catálogo descubierto sin probe
    y modelos sintéticos no mapeados).
    """
    keys: Dict[str, Dict[str, Any]] = {}
    for row in get_latest_local_verified_models():
        if not row.get("is_functional"):
            continue
        if row.get("latency_ms") is None:
            continue
        if row.get("is_synthetic"):
            continue
        for k in (row.get("canonical_id"), row.get("model_identifier")):
            if k and k not in keys:
                keys[k] = row
    return keys


def get_all_models_count() -> int:
    """Devuelve la cantidad total de modelos registrados en el catálogo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM models")
        row = cursor.fetchone()
        return row[0] if row else 0


def record_drift_event(
    model_id: str,
    provider: str,
    event_type: str,
    metric_name: str,
    old_value: Optional[str],
    new_value: Optional[str],
    severity: str = "warning",
    details: Optional[Dict[str, Any]] = None
):
    """Registra un evento de drift o variación en la base de datos."""
    details_str = json.dumps(details) if details else "{}"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO drift_events (model_id, provider, event_type, metric_name, old_value, new_value, severity, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (model_id, provider, event_type, metric_name, str(old_value) if old_value is not None else None, str(new_value) if new_value is not None else None, severity, details_str))
        conn.commit()


def get_recent_drift_events(limit: int = 50, severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene los eventos de drift más recientes registrados."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if severity:
            cursor.execute("""
                SELECT * FROM drift_events
                WHERE severity = ?
                ORDER BY id DESC LIMIT ?
            """, (severity, limit))
        else:
            cursor.execute("""
                SELECT * FROM drift_events
                ORDER BY id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("details_json"):
                try:
                    d["details"] = json.loads(d["details_json"])
                except Exception:
                    d["details"] = {}
            result.append(d)
        return result


# Inicializar y aplicar migraciones automáticamente al importar
init_db()


