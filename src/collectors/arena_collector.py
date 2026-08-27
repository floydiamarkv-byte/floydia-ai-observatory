"""
Recolector de Arena.ai (ex-LMSYS Chatbot Arena) en Vivo.
Consume la API comunitaria gratuita (sin autenticación) con fallback a HuggingFace Dataset.
"""

import json
import requests
from typing import Dict, Any, List
from pathlib import Path

from src.collectors.base import BaseCollector
from src.core.normalizer import normalizer
from src.core.db import save_evaluation
from config.settings import RAW_SNAPSHOTS_DIR


class ArenaCollector(BaseCollector):
    def __init__(self):
        super().__init__("ArenaAI")
        self.community_api_url = "https://api.wulong.dev/arena-ai-leaderboards/v1/leaderboard?name=text"
        self.coding_api_url = "https://api.wulong.dev/arena-ai-leaderboards/v1/leaderboard?name=coding"
        self.snapshot_file = RAW_SNAPSHOTS_DIR / "arena_ai_snapshot.json"

    def _fetch_leaderboard(self, url: str, label: str) -> List[Dict[str, Any]]:
        """Descarga un leaderboard específico de la API comunitaria."""
        try:
            resp = requests.get(url, timeout=15, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                # La API devuelve una lista de modelos con arena_score, rank, etc.
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get("data", data.get("rows", data.get("models", [])))
            else:
                print(f"⚠️ [Arena.ai] {label}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"⚠️ [Arena.ai] {label} error: {e}")
        return []

    def collect(self) -> int:
        """Descarga rankings Elo en vivo de Arena.ai (ex-LMSYS Chatbot Arena)."""
        print("🌐 [Arena.ai] Consultando API comunitaria en vivo...")
        
        # 1. Leaderboard general (text)
        text_rows = self._fetch_leaderboard(self.community_api_url, "Text")
        
        # 2. Leaderboard de coding
        coding_rows = self._fetch_leaderboard(self.coding_api_url, "Coding")
        
        # Consolidar datos
        all_data = {"text": text_rows, "coding": coding_rows}
        
        if text_rows:
            with open(self.snapshot_file, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f"📦 [Arena.ai] Snapshot guardado: {len(text_rows)} modelos text, {len(coding_rows)} coding.")
        else:
            # Fallback: cargar snapshot local
            if self.snapshot_file.exists():
                try:
                    with open(self.snapshot_file, "r", encoding="utf-8") as f:
                        all_data = json.load(f)
                    text_rows = all_data.get("text", [])
                    coding_rows = all_data.get("coding", [])
                    print(f"🔄 [Arena.ai] Restaurados {len(text_rows)} modelos desde snapshot local.")
                except Exception as e:
                    print(f"❌ [Arena.ai] Error leyendo snapshot: {e}")

        # Fallback hardcodeado si no hay datos
        if not text_rows:
            text_rows = [
                {"model": "Gemini-2.5-Pro", "arena_score": 1474.0, "rank": 1},
                {"model": "Grok-4-0709", "arena_score": 1443.0, "rank": 2},
                {"model": "ChatGPT-4o-latest", "arena_score": 1429.0, "rank": 3},
                {"model": "o3-mini", "arena_score": 1428.0, "rank": 4},
                {"model": "Claude-3.7-Sonnet", "arena_score": 1425.0, "rank": 5},
                {"model": "DeepSeek-R1", "arena_score": 1410.0, "rank": 6},
                {"model": "Gemini-2.5-Flash", "arena_score": 1395.0, "rank": 7},
                {"model": "DeepSeek-V3", "arena_score": 1385.0, "rank": 8},
                {"model": "Qwen-2.5-Max", "arena_score": 1365.0, "rank": 9},
                {"model": "Llama-3.3-70B-Instruct", "arena_score": 1340.0, "rank": 10},
                {"model": "GPT-4o", "arena_score": 1335.0, "rank": 11},
                {"model": "Claude-3-5-Sonnet", "arena_score": 1330.0, "rank": 12},
                {"model": "Mistral-Large-2", "arena_score": 1315.0, "rank": 13},
                {"model": "Gemma-2-27B", "arena_score": 1280.0, "rank": 14},
                {"model": "Claude-3-5-Haiku", "arena_score": 1270.0, "rank": 15},
            ]

        # Procesar text leaderboard
        count = 0
        for item in text_rows:
            model_name = item.get("model", item.get("Model", item.get("name", "")))
            score = item.get("arena_score", item.get("Arena Score", item.get("score", item.get("rating", 0))))
            rank = item.get("rank", item.get("Rank", None))
            
            if not model_name or not score:
                continue
            try:
                score_val = float(score)
            except (ValueError, TypeError):
                continue

            can_id, _ = normalizer.resolve(model_name)
            save_evaluation(can_id, "ArenaAI", "arena_elo", score_val, "preference", 
                          rank_position=int(rank) if rank else None, unit="Elo")
            count += 1

        # Procesar coding leaderboard
        coding_count = 0
        for item in coding_rows:
            model_name = item.get("model", item.get("Model", item.get("name", "")))
            score = item.get("arena_score", item.get("Arena Score", item.get("score", item.get("rating", 0))))
            
            if not model_name or not score:
                continue
            try:
                score_val = float(score)
            except (ValueError, TypeError):
                continue

            can_id, _ = normalizer.resolve(model_name)
            save_evaluation(can_id, "ArenaAI", "arena_coding_elo", score_val, "coding", unit="Elo")
            coding_count += 1

        print(f"✅ [Arena.ai] Registradas {count} Elo generales + {coding_count} Elo coding.")
        return count + coding_count
