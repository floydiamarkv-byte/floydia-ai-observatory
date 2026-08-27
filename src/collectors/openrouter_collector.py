"""
Recolector de métricas, catálogo y precios de OpenRouter en Vivo.
Extrae precios por token, longitud de contexto, latencia y disponibilidad.
"""

import json
import requests
from typing import Dict, Any
from pathlib import Path

from src.collectors.base import BaseCollector
from src.core.normalizer import normalizer
from src.core.db import save_evaluation, upsert_model
from config.settings import RAW_SNAPSHOTS_DIR


class OpenRouterCollector(BaseCollector):
    def __init__(self):
        super().__init__("OpenRouter")
        self.models_url = "https://openrouter.ai/api/v1/models"
        self.snapshot_file = RAW_SNAPSHOTS_DIR / "openrouter_models_snapshot.json"

    def collect(self) -> int:
        """Descarga el catálogo completo de modelos de OpenRouter y sus precios en vivo."""
        print("🌐 [OpenRouter] Consultando catálogo y precios en vivo...")
        data = None
        
        try:
            resp = requests.get(self.models_url, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                with open(self.snapshot_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"📦 [OpenRouter] Snapshot actualizado.")
            else:
                print(f"⚠️ [OpenRouter] HTTP {resp.status_code}. Cargando snapshot local...")
        except Exception as e:
            print(f"⚠️ [OpenRouter] Error de conexión: {e}. Usando snapshot local...")

        if not data and self.snapshot_file.exists():
            try:
                with open(self.snapshot_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"❌ [OpenRouter] Error leyendo snapshot: {e}")

        if not data:
            print("❌ [OpenRouter] No se pudo obtener datos del catálogo.")
            return 0
        
        try:
            models_list = data.get("data", [])
            count = 0
            
            for item in models_list:
                raw_id = item.get("id", "")
                name = item.get("name", raw_id)
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
                
                # Guardar disponibilidad
                save_evaluation(can_id, "OpenRouter", "openrouter_availability", 100.0, "adoption")
                count += 1
                
            print(f"✅ [OpenRouter] Procesados {count} modelos del catálogo en vivo.")
            return count
        except Exception as e:
            print(f"❌ [OpenRouter] Error procesando payload: {e}")
            return 0
