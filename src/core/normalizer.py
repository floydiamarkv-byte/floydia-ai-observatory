"""
Normalizador y Resolución de Entidades Canónicas con 10 Categorías Especializadas (FloydIA Protocol V11).
Mapea nombres y alias hacia su identificador canónico único y categoría, previniendo duplicaciones.
"""

import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config.settings import CONFIG_DIR
from src.core.db import upsert_model


def normalize_alias(name: str) -> str:
    """
    Normaliza agresivamente identificadores de modelos para resolución de entidades:
    - Remueve prefijos de proveedor ('x-ai/', 'openai/', 'anthropic/', 'google/', etc.)
    - Remueve prefijos y tildes ('~', 'models/')
    - Remueve sufijos y decoraciones ('(High)', '(Max)', ':free', ':latest', '-instruct', '-preview')
    """
    n = unicodedata.normalize("NFKD", name).lower().strip()
    n = re.sub(r"^~", "", n)
    n = re.sub(r"^models/", "", n)
    # Remueve paréntesis decorativos (High), (xHigh), (Free), etc.
    n = re.sub(r"\([^)]*\)", "", n)
    # Remueve prefijos conocidos de proveedores
    n = re.sub(r"^(x-ai|xai|openai|anthropic|google|deepseek|alibaba|qwen|zhipu|z-ai|meta-llama|meta|mistralai|mistral|moonshotai|moonshot|nousresearch|nous|bytedance|tencent|cohere|minimax|upstage|baidu|microsoft|amazon|nvidia|sao10k)[/.]", "", n)
    # Remueve sufijos
    n = re.sub(r":(free|batch|preview|nitro|online|extended|exact)$", "", n)
    n = re.sub(r"-(instruct|chat|preview|latest|fast|thinking|v\d+.*)$", "", n)
    # Normaliza separadores a guiones simples
    n = re.sub(r"[^a-z0-9]+", "-", n).strip("-")
    return n


class ModelNormalizer:
    def __init__(self):
        self.mappings_file = CONFIG_DIR / "model_mappings.json"
        self.canonical_models: Dict[str, Dict[str, Any]] = {}
        self.alias_to_id: Dict[str, str] = {}
        self.normalized_alias_to_id: Dict[str, str] = {}
        self.tiers: Dict[str, Dict[str, Any]] = {}
        self.duplicate_aliases: List[str] = []
        self.load_mappings()

    def _register_alias(self, alias: str, model_id: str, is_normalized: bool = False):
        target_dict = self.normalized_alias_to_id if is_normalized else self.alias_to_id
        existing = target_dict.get(alias)
        if existing and existing != model_id:
            if not is_normalized:
                self.duplicate_aliases.append(f"'{alias}' ({existing} vs {model_id})")
            return
        target_dict[alias] = model_id

    def load_mappings(self):
        """Carga las definiciones canónicas y construye las tablas hash de alias exactos y normalizados."""
        if not self.mappings_file.exists():
            return
        
        with open(self.mappings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.tiers = data.get("tiers", {})
            for m in data.get("canonical_models", []):
                m_id = m["id"]
                m["is_synthetic"] = False
                self.canonical_models[m_id] = m
                upsert_model(m)
                
                # Mapeos exactos
                self._register_alias(m_id.lower(), m_id)
                self._register_alias(m["canonical_name"].lower(), m_id)
                
                # Mapeo normalizado
                norm_id = normalize_alias(m_id)
                if norm_id:
                    self._register_alias(norm_id, m_id, is_normalized=True)
                norm_canon = normalize_alias(m["canonical_name"])
                if norm_canon:
                    self._register_alias(norm_canon, m_id, is_normalized=True)
                
                for alias in m.get("aliases", []):
                    alias_clean = alias.strip().lower()
                    self._register_alias(alias_clean, m_id)
                    norm_a = normalize_alias(alias)
                    if norm_a:
                        self._register_alias(norm_a, m_id, is_normalized=True)

        if self.duplicate_aliases:
            print(f"[Normalizer] {len(self.duplicate_aliases)} alias duplicados detectados (gana el primero): {', '.join(self.duplicate_aliases[:5])}")

    def resolve(self, raw_name: str, provider_hint: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        cleaned = raw_name.strip().lower()
        
        # 1. Búsqueda exacta en tabla de alias
        if cleaned in self.alias_to_id:
            can_id = self.alias_to_id[cleaned]
            return can_id, self.canonical_models[can_id]

        # 2. Búsqueda por alias normalizado
        norm_key = normalize_alias(cleaned)
        if norm_key in self.normalized_alias_to_id:
            can_id = self.normalized_alias_to_id[norm_key]
            return can_id, self.canonical_models[can_id]

        # 3. Búsqueda por subcadenas específicas seguras (solo alias largos >= 6, gana el más largo)
        best_alias, best_id = None, None
        for alias, can_id in self.alias_to_id.items():
            if len(alias) >= 6 and alias in cleaned:
                if best_alias is None or len(alias) > len(best_alias):
                    best_alias, best_id = alias, can_id
        if best_id:
            return best_id, self.canonical_models[best_id]

        # 4. Heurística de Categoría para nuevos modelos descubiertos
        tier = "workhorse"
        detected_provider = provider_hint or "Unknown"

        if "anthropic" in cleaned or "claude" in cleaned:
            detected_provider = "Anthropic"
        elif "google" in cleaned or "gemini" in cleaned or "gemma" in cleaned:
            detected_provider = "Google"
        elif "openai" in cleaned or "gpt" in cleaned or "o1" in cleaned or "o3" in cleaned:
            detected_provider = "OpenAI"
        elif "deepseek" in cleaned:
            detected_provider = "DeepSeek"
        elif "qwen" in cleaned or "alibaba" in cleaned:
            detected_provider = "Alibaba"
        elif "mistral" in cleaned or "codestral" in cleaned:
            detected_provider = "Mistral"
        elif "zhipu" in cleaned or "glm" in cleaned or "z-ai" in cleaned:
            detected_provider = "Zhipu AI"
        elif "grok" in cleaned or "xai" in cleaned:
            detected_provider = "xAI"

        if any(w in cleaned for w in ["hermes", "uncensored", "dolphin", "venice", "wizardlm", "abliterated"]):
            tier = "uncensored"
        elif any(w in cleaned for w in ["groq", "cerebras", "sambanova", "realtime", "instant", "turbo", "flash-lite"]):
            tier = "realtime"
        elif any(w in cleaned for w in ["fable", "claude-fable", "claude-3-7", "agent", "function", "tool", "act"]):
            tier = "frontier" if "fable" in cleaned or "3-7" in cleaned else "agentic"
        elif any(w in cleaned for w in ["r1", "o1", "o3", "reasoner", "thinking", "cot", "deepseek-r1"]):
            tier = "reasoning"
        elif any(w in cleaned for w in ["vision", "omni", "multimodal", "image", "audio", "video", "vl", "gpt-4o"]):
            tier = "multimodal"
        elif any(w in cleaned for w in ["1m", "2m", "long", "context", "gemini-2.5"]):
            tier = "long_context"
        elif any(w in cleaned for w in ["coder", "code", "dev", "deepseek-coder", "starcoder"]):
            tier = "coding"
        elif any(w in cleaned for w in ["opus", "max", "pro", "gpt-5", "gpt-4.5"]):
            tier = "frontier"
        elif any(w in cleaned for w in ["7b", "8b", "3b", "1b", "mini", "small", "nano", "edge"]):
            tier = "edge"

        synthetic_id = norm_key[:40] if norm_key else cleaned.replace("/", "-").replace(":", "-").replace(" ", "-")[:40]
        synthetic_model = {
            "id": synthetic_id,
            "canonical_name": raw_name.strip(),
            "tier": tier,
            "provider": detected_provider,
            "context_window": 128000,
            "max_output": 8192,
            "is_free_tier": (":free" in cleaned),
            "input_cost_per_m": 0.0,
            "output_cost_per_m": 0.0,
            "supports_tools": (tier in ["agentic", "coding", "frontier", "workhorse", "uncensored"]),
            "supports_vision": (tier == "multimodal"),
            "supports_reasoning": (tier in ["reasoning", "frontier", "agentic"]),
            "aliases": [raw_name],
            "is_synthetic": True
        }
        self.canonical_models[synthetic_id] = synthetic_model
        self.alias_to_id[cleaned] = synthetic_id
        if norm_key:
            self.normalized_alias_to_id[norm_key] = synthetic_id
        upsert_model(synthetic_model)
        
        return synthetic_id, synthetic_model


normalizer = ModelNormalizer()

