"""
Manejador de Base de Datos SQLite para FloydIA AI Rankings & Local API Observatory.
Garantiza inmutabilidad con snapshots criptográficos SHA256 y esquemas normalizados.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.settings import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Crea o retorna conexión a la base de datos SQLite con soporte para Row dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
                is_functional BOOLEAN NOT NULL,
                status_code INTEGER,
                status_message TEXT,
                latency_ms REAL,
                detected_context_window INTEGER,
                supports_tools BOOLEAN DEFAULT 0,
                supports_vision BOOLEAN DEFAULT 0,
                is_free_tier BOOLEAN DEFAULT 0,
                cost_input_m REAL DEFAULT 0.0,
                cost_output_m REAL DEFAULT 0.0,
                verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()


def save_raw_snapshot(source: str, endpoint_url: str, payload_str: str, status_code: int = 200) -> str:
    """Guarda un snapshot crudo en SQLite asegurando deduplicación por SHA256."""
    sha256 = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO snapshots_raw (source, endpoint_url, payload, sha256_hash, fetch_status)
            VALUES (?, ?, ?, ?, ?)
        """, (source, endpoint_url, payload_str, sha256, status_code))
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
                aliases_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
            json.dumps(model_data.get("aliases", []))
        ))
        conn.commit()


def save_evaluation(model_id: str, source: str, benchmark_name: str, score: float, category: str = "general", rank_position: Optional[int] = None, unit: str = "points"):
    """Guarda una métrica de evaluación para un modelo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evaluations (model_id, source, benchmark_name, category, score, unit, rank_position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (model_id, source, benchmark_name, category, score, unit, rank_position))
        conn.commit()


def record_local_api_check(check_result: Dict[str, Any]):
    """Registra la comprobación de salud y capacidades de una API local."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO local_api_checks (
                provider_name, model_identifier, canonical_id, is_functional,
                status_code, status_message, latency_ms, detected_context_window,
                supports_tools, supports_vision, is_free_tier, cost_input_m, cost_output_m
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            check_result["provider_name"],
            check_result["model_identifier"],
            check_result.get("canonical_id"),
            1 if check_result.get("is_functional") else 0,
            check_result.get("status_code", 200),
            check_result.get("status_message", "OK"),
            check_result.get("latency_ms", 0.0),
            check_result.get("detected_context_window", 128000),
            1 if check_result.get("supports_tools") else 0,
            1 if check_result.get("supports_vision") else 0,
            1 if check_result.get("is_free_tier") else 0,
            check_result.get("cost_input_m", 0.0),
            check_result.get("cost_output_m", 0.0)
        ))
        conn.commit()


def get_latest_local_verified_models() -> List[Dict[str, Any]]:
    """Obtiene el último estado verificado de cada API local."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, m.canonical_name, m.tier
            FROM local_api_checks c
            LEFT JOIN models m ON c.canonical_id = m.id
            WHERE c.id IN (
                SELECT MAX(id) FROM local_api_checks GROUP BY provider_name, model_identifier
            )
            ORDER BY c.is_functional DESC, c.latency_ms ASC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_all_models_count() -> int:
    """Devuelve la cantidad total de modelos registrados en el catálogo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM models")
        row = cursor.fetchone()
        return row[0] if row else 0


# Inicializar tablas al importar
init_db()
