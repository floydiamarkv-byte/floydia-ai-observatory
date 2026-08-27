"""
Normalizador y Resolución de Entidades con 10 Categorías Especializadas.
Mapea nombres y alias hacia su identificador canónico y categoría.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config.settings import CONFIG_DIR
from src.core.db import upsert_model


class ModelNormalizer:
    def __init__(self):
        self.mappings_file = CONFIG_DIR / "model_mappings.json"
        self.canonical_models: Dict[str, Dict[str, Any]] = {}
        self.alias_to_id: Dict[str, str] = {}
        self.tiers: Dict[str, Dict[str, Any]] = {}
        self.load_mappings()

    def load_mappings(self):
        """Carga las definiciones canónicas y construye la tabla hash de alias."""
        if not self.mappings_file.exists():
            return
        
        with open(self.mappings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.tiers = data.get("tiers", {})
            for m in data.get("canonical_models", []):
                m_id = m["id"]
                self.canonical_models[m_id] = m
                upsert_model(m)
                
                self.alias_to_id[m_id.lower()] = m_id
                self.alias_to_id[m["canonical_name"].lower()] = m_id
                
                for alias in m.get("aliases", []):
                    self.alias_to_id[alias.lower()] = m_id

    def resolve(self, raw_name: str, provider_hint: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        cleaned = raw_name.strip().lower()
        
        # 1. Búsqueda exacta en tabla de alias
        if cleaned in self.alias_to_id:
            can_id = self.alias_to_id[cleaned]
            return can_id, self.canonical_models[can_id]

        # 2. Búsqueda por subcadenas conocidas
        for alias, can_id in self.alias_to_id.items():
            if alias in cleaned or cleaned in alias:
                return can_id, self.canonical_models[can_id]

        # 3. Heurística avanzada de 10 Categorías
        tier = "workhorse"
        if any(w in cleaned for w in ["hermes", "uncensored", "dolphin", "venice", "wizardlm", "abliterated"]):
            tier = "uncensored"
        elif any(w in cleaned for w in ["groq", "cerebras", "sambanova", "realtime", "instant", "turbo", "flash-lite"]):
            tier = "realtime"
        elif any(w in cleaned for w in ["agent", "function", "tool", "act", "claude-3-7"]):
            tier = "agentic"
        elif any(w in cleaned for w in ["r1", "o1", "o3", "reasoner", "thinking", "cot", "deepseek-r1"]):
            tier = "reasoning"
        elif any(w in cleaned for w in ["vision", "omni", "multimodal", "image", "audio", "video", "vl", "gpt-4o"]):
            tier = "multimodal"
        elif any(w in cleaned for w in ["1m", "2m", "long", "context", "gemini-2.5"]):
            tier = "long_context"
        elif any(w in cleaned for w in ["coder", "code", "dev", "deepseek-coder", "starcoder", "claude-3-5-sonnet"]):
            tier = "coding"
        elif any(w in cleaned for w in ["opus", "max", "pro", "gpt-5", "gpt-4.5"]):
            tier = "frontier"
        elif any(w in cleaned for w in ["7b", "8b", "3b", "1b", "mini", "small", "nano", "edge"]):
            tier = "edge"

        synthetic_id = cleaned.replace("/", "-").replace(":", "-").replace(" ", "-")[:40]
        synthetic_model = {
            "id": synthetic_id,
            "canonical_name": raw_name.strip(),
            "tier": tier,
            "provider": provider_hint or "Unknown",
            "context_window": 128000,
            "max_output": 8192,
            "is_free_tier": (":free" in cleaned),
            "input_cost_per_m": 0.0,
            "output_cost_per_m": 0.0,
            "supports_tools": (tier in ["agentic", "coding", "frontier", "workhorse", "uncensored"]),
            "supports_vision": (tier == "multimodal"),
            "supports_reasoning": (tier in ["reasoning", "frontier", "agentic"]),
            "aliases": [raw_name]
        }
        self.canonical_models[synthetic_id] = synthetic_model
        self.alias_to_id[cleaned] = synthetic_id
        upsert_model(synthetic_model)
        
        return synthetic_id, synthetic_model


normalizer = ModelNormalizer()
