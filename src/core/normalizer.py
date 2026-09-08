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

    def format_display_name(self, model: Dict[str, Any]) -> str:
        """
        Estandariza deterministamente el nombre del modelo bajo el protocolo canónico:
        [<VentanaContexto>•<NivelCosto>] <Nombre del Modelo> (<Proveedor/Hub>)
        Ejemplo: [1M•Free] Gemini 2.5 Flash (Google AI Studio)
        """
        # 1. Ventana de Contexto (normalizada a potencias y múltiplos estándar)
        ctx = model.get("context_window") or model.get("detected_context_window") or 128000
        if ctx >= 1900000:
            ctx_str = "2M"
        elif ctx >= 900000:
            ctx_str = "1M"
        elif ctx >= 240000:
            ctx_str = "256k"
        elif ctx >= 120000:
            ctx_str = "128k"
        elif ctx >= 60000:
            ctx_str = "64k"
        elif ctx >= 30000:
            ctx_str = "32k"
        elif ctx >= 15000:
            ctx_str = "16k"
        elif ctx >= 7000:
            ctx_str = "8k"
        elif ctx >= 1000:
            ctx_str = f"{int(round(ctx/1000))}k"
        else:
            ctx_str = f"{ctx}"

        # 2. Proveedor Canónico
        prov_raw = str(model.get("provider") or model.get("provider_name") or "")
        p_lower = prov_raw.lower()
        if "google" in p_lower:
            prov_str = "Google AI Studio"
        elif "deepseek" in p_lower:
            prov_str = "DeepSeek Direct"
        elif "openrouter" in p_lower:
            prov_str = "OpenRouter Fleet"
        elif "groq" in p_lower:
            prov_str = "Groq"
        elif "mistral" in p_lower:
            prov_str = "Mistral AI"
        elif "nvidia" in p_lower or "nim" in p_lower:
            prov_str = "NVIDIA NIM"
        elif "dashscope" in p_lower or "alibaba" in p_lower or "qwen" in p_lower:
            prov_str = "Alibaba DashScope"
        elif "z_ai" in p_lower or "zhipu" in p_lower or "z.ai" in p_lower:
            prov_str = "Z.AI"
        elif "fireworks" in p_lower:
            prov_str = "Fireworks AI"
        elif "github" in p_lower:
            prov_str = "GitHub Models"
        elif "anthropic" in p_lower:
            prov_str = "Anthropic Direct"
        elif "openai" in p_lower:
            prov_str = "OpenAI Direct"
        elif "zen" in p_lower:
            prov_str = "OpenCode Zen"
        else:
            prov_str = prov_raw or "Clúster Local"

        # Diferenciador de cuenta (ej. C1, C2, C3, C7)
        acc_tag = ""
        acc_raw = model.get("account_tag") or model.get("account_key") or model.get("account_name") or ""
        if acc_raw:
            m_acc = re.match(r"^(C\d+|[A-Z0-9]+)", str(acc_raw))
            if m_acc:
                acc_tag = m_acc.group(1)
            else:
                acc_tag = str(acc_raw)[:4]

        # 3. Nivel de Costo
        in_cost = model.get("input_cost_per_m", model.get("cost_input_m", 0.0)) or 0.0
        out_cost = model.get("output_cost_per_m", model.get("cost_output_m", 0.0)) or 0.0
        is_free_flag = model.get("is_free_tier", False) or (in_cost == 0.0 and out_cost == 0.0 and "deepseek" not in p_lower and "anthropic" not in p_lower and "openai" not in p_lower)
        
        tier = (model.get("tier") or "").lower()

        if is_free_flag or ":free" in str(model.get("id", "")):
            cost_str = "Free"
        elif any(x in prov_str.lower() for x in ["nim", "trial", "z.ai"]):
            cost_str = "Trial"
        elif "pro" in str(model.get("id", "")).lower() and "google" in prov_str.lower():
            cost_str = "Pro"
        else:
            cost_str = "Paid"

        # 4. Nombre Limpio
        canonical_name = model.get("canonical_name") or model.get("name") or model.get("model_identifier") or model.get("id") or "Modelo"
        # Eliminar prefijos de corchetes existentes para no duplicar
        clean_name = re.sub(r"^\[[^\]]+\]\s*", "", canonical_name).strip()
        # Eliminar sufijo de proveedor entre paréntesis si ya estuviera
        clean_name = re.sub(r"\s*\([^)]+\)$", "", clean_name).strip()
        
        # Corrección de nombres legibles comunes si repiten el proveedor innecesariamente
        if clean_name.startswith("Google ") and "Google" in prov_str:
            clean_name = clean_name.replace("Google ", "")

        if acc_tag and f"[{acc_tag}]" not in clean_name and f"[{acc_tag}]" not in prov_str:
            clean_name = f"{clean_name} [{acc_tag}]"

        return f"[{ctx_str}•{cost_str}] {clean_name} ({prov_str})"


normalizer = ModelNormalizer()


def format_display_name(model: Dict[str, Any]) -> str:
    """Helper global para formatear nombres de modelos."""
    return normalizer.format_display_name(model)


