"""
Recolector de Arena.ai (ex-LMSYS Chatbot Arena) en Vivo.
Procesa leaderboards de Text (General), WebDev (Coding) y Agent.
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
            resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
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
        """Descarga e ingesta rankings Elo en vivo de Arena.ai (Text, WebDev y Agent)."""
        print("🌐 [Arena.ai] Consultando leaderboards de Arena.ai...")
        
        all_data = {}
        if self.snapshot_file.exists():
            try:
                with open(self.snapshot_file, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            except Exception as e:
                print(f"❌ [Arena.ai] Error leyendo snapshot: {e}")

        text_rows = all_data.get("text", [])
        webdev_rows = all_data.get("webdev", all_data.get("coding", []))
        agent_rows = all_data.get("agent", [])

        total_count = 0

        # 1. Procesar Text Leaderboard (arena_elo -> pilar preference)
        for item in text_rows:
            model_name = item.get("model", item.get("Model", item.get("name", "")))
            score = item.get("score", item.get("arena_score", item.get("rating", 0)))
            rank = item.get("rank", None)
            if not model_name or not score:
                continue
            try:
                score_val = float(score)
            except (ValueError, TypeError):
                continue

            can_id, _ = normalizer.resolve(model_name)
            save_evaluation(can_id, "ArenaAI", "arena_elo", score_val, "preference", 
                          rank_position=int(rank) if rank else None, unit="Elo")
            total_count += 1

        # 2. Procesar WebDev / Coding Leaderboard (arena_coding_elo -> pilar coding)
        for item in webdev_rows:
            model_name = item.get("model", item.get("Model", item.get("name", "")))
            score = item.get("score", item.get("arena_score", item.get("rating", 0)))
            rank = item.get("rank", None)
            if not model_name or not score:
                continue
            try:
                score_val = float(score)
            except (ValueError, TypeError):
                continue

            can_id, _ = normalizer.resolve(model_name)
            save_evaluation(can_id, "ArenaAI", "arena_coding_elo", score_val, "coding",
                          rank_position=int(rank) if rank else None, unit="Elo")
            total_count += 1

        # 3. Procesar Agent Leaderboard (arena_agent_score -> pilar reasoning / agentic)
        for item in agent_rows:
            model_name = item.get("model", item.get("Model", item.get("name", "")))
            score = item.get("score", 0)
            win_rate = item.get("win_rate", 0)
            rank = item.get("rank", None)
            if not model_name:
                continue
            try:
                score_val = float(score) if score else 1500.0
            except (ValueError, TypeError):
                score_val = 1500.0

            can_id, _ = normalizer.resolve(model_name)
            save_evaluation(can_id, "ArenaAI", "chatbot_arena", score_val, "preference",
                          rank_position=int(rank) if rank else None, unit="Elo")
            total_count += 1

        print(f"✅ [Arena.ai] Registradas {total_count} evaluaciones combinadas (Text + WebDev + Agent).")
        return total_count
