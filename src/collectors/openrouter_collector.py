"""
Recolector de métricas, catálogo y precios de OpenRouter en Vivo (M-1 Cache & Schema Validation).
Extrae precios por token, longitud de contexto y metadatos de modelos.
"""

import json
import time
import jsonschema
import requests
from typing import Dict, Any, Optional
from pathlib import Path

from src.collectors.base import BaseCollector
from src.core.normalizer import normalizer
from src.core.db import upsert_model
from config.settings import BASE_DIR, RAW_SNAPSHOTS_DIR

CACHE_DIR = BASE_DIR / "cache"
SCHEMAS_DIR = BASE_DIR / "schemas"


class OpenRouterCollector(BaseCollector):
    def __init__(self):
        super().__init__("OpenRouter")
        self.models_url = "https://openrouter.ai/api/v1/models"
        self.snapshot_file = RAW_SNAPSHOTS_DIR / "openrouter_models_snapshot.json"
        self.cache_file = CACHE_DIR / "openrouter_models.json"
        self.schema_file = SCHEMAS_DIR / "openrouter_models.schema.json"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_schema(self) -> Optional[Dict[str, Any]]:
        if self.schema_file.exists():
            try:
                with open(self.schema_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ [OpenRouter] Error leyendo schema JSON: {e}")
        return None

    def _validate_payload(self, payload: Any) -> bool:
        schema = self._load_schema()
        if not schema:
            return isinstance(payload, dict) and "data" in payload
        try:
            jsonschema.validate(instance=payload, schema=schema)
            return True
        except jsonschema.ValidationError as ve:
            print(f"❌ [OpenRouter] Error de validación de schema: {ve.message}")
            return False

    def collect(self) -> int:
        """Descarga el catálogo completo de modelos de OpenRouter y sus precios en vivo con validación de schema."""
        print("🌐 [OpenRouter] Consultando catálogo y precios en vivo...")
        data = None
        is_stale = False
        now_ts = time.time()
        
        # 1. Intentar descargar en vivo
        try:
            resp = requests.get(self.models_url, timeout=12)
            if resp.status_code == 200:
                candidate = resp.json()
                if self._validate_payload(candidate):
                    data = candidate
                    # Guardar snapshot y cache validado
                    with open(self.snapshot_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    with open(self.cache_file, "w", encoding="utf-8") as f:
                        json.dump({"ts": now_ts, "payload": data}, f, ensure_ascii=False, indent=2)
                    print("📦 [OpenRouter] Snapshot y caché validados actualizados.")
                else:
                    print("⚠️ [OpenRouter] Schema inválido en respuesta en vivo. Conmutando a caché conocido...")
            else:
                print(f"⚠️ [OpenRouter] HTTP {resp.status_code}. Conmutando a caché conocido...")
        except Exception as e:
            print(f"⚠️ [OpenRouter] Error de conexión: {e}. Conmutando a caché conocido...")

        # 2. Fallback a caché validado si el fetch en vivo falló o schema es inválido
        if not data and self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cached_entry = json.load(f)
                    candidate = cached_entry.get("payload")
                    if self._validate_payload(candidate):
                        data = candidate
                        is_stale = True
                        print("⚠️ [OpenRouter] Usando último-known-good «stale-cache ⚠».")
            except Exception as e:
                print(f"❌ [OpenRouter] Error leyendo cache: {e}")

        # 3. Fallback adicional a snapshot histórico
        if not data and self.snapshot_file.exists():
            try:
                with open(self.snapshot_file, "r", encoding="utf-8") as f:
                    candidate = json.load(f)
                    if self._validate_payload(candidate):
                        data = candidate
                        is_stale = True
                        print("⚠️ [OpenRouter] Usando snapshot de emergencia «stale-cache ⚠».")
            except Exception as e:
                print(f"❌ [OpenRouter] Error leyendo snapshot: {e}")

        if not data:
            print("❌ [OpenRouter] No se pudo obtener datos del catálogo válidos.")
            self.is_stale = False
            self.data_warning = "❌ No Data"
            return 0

        self.is_stale = is_stale
        self.data_warning = "«stale-cache ⚠»" if is_stale else ""

        
        try:
            models_list = data.get("data", [])
            count = 0
            
            for item in models_list:
                raw_id = item.get("id", "")
                pricing = item.get("pricing", {})
                context_length = item.get("context_length", 128000)
                
                # Precios por millón de tokens
                try:
                    prompt_price = float(pricing.get("prompt", 0.0)) * 1_000_000
                    completion_price = float(pricing.get("completion", 0.0)) * 1_000_000
                except (ValueError, TypeError):
                    prompt_price = 0.0
                    completion_price = 0.0
                    
                is_free = (prompt_price == 0.0 and completion_price == 0.0)
                
                # Normalizar a catálogo canónico
                can_id, model_dict = normalizer.resolve(raw_id, provider_hint="OpenRouter")
                
                # Actualizar precio y contexto detectado
                model_dict["input_cost_per_m"] = round(prompt_price, 4)
                model_dict["output_cost_per_m"] = round(completion_price, 4)
                model_dict["context_window"] = context_length
                model_dict["is_free_tier"] = is_free
                upsert_model(model_dict)
                count += 1
                
            tag = " «stale-cache ⚠»" if is_stale else ""
            print(f"✅ [OpenRouter] Procesados {count} modelos del catálogo{tag}.")
            return count
        except Exception as e:
            print(f"❌ [OpenRouter] Error procesando payload: {e}")
            return 0

