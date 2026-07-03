import json
import os
import time
from typing import Any, Dict, Optional


class StrategicTaskRouter:
    def __init__(self, matrix_path: Optional[str] = None):
        if matrix_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.matrix_path = os.path.join(base_dir, "..", "data", "agent_matching_matrix.json")
        else:
            self.matrix_path = matrix_path
        # Provider health tracking
        self.provider_health = {
            "nvidia_nim": {"consecutive_failures": 0, "last_429_time": 0.0},
            "openrouter_free": {"consecutive_failures": 0, "last_429_time": 0.0},
            "groq_free": {"consecutive_failures": 0, "last_429_time": 0.0},
            "google_ai_studio": {"consecutive_failures": 0, "last_429_time": 0.0},
        }

    def _load_matrix(self) -> Dict[str, Any]:
        try:
            with open(self.matrix_path, "r") as f:
                return json.load(f)  # type: ignore[no-any-return]
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def determine_optimal_route(self, category: str, payload_size: int) -> Dict[str, Any]:
        current_time = time.time()

        # 1. Active Cooldown Rule for NVIDIA NIM
        if current_time - self.provider_health["nvidia_nim"]["last_429_time"] < 60:
            # NVIDIA NIM is cooling down, try alternatives
            return self._select_fallback(category, payload_size, excluded={"nvidia_nim"})

        # 2. Time-of-day congestion profile
        current_hour_utc = time.gmtime().tm_hour
        is_peak_hours = 14 <= current_hour_utc <= 22  # Danger Zone

        # 3. Strategic allocation with fallback awareness
        if category in ["css_layout", "regex_cleaning"]:
            # Prefer NIM for speed, but if peak hours and large payload, consider Groq for ultra-low latency
            if is_peak_hours and payload_size > 5000:
                return {
                    "provider": "groq_free",
                    "model": "mixtral-8x7b-32768",
                    "reason": "PEAK_HOUR_GROQ_ULTRALOW",
                }
            return {
                "provider": "nvidia_nim",
                "model": "nvidia/qwen3-coder",
                "reason": "OPTIMAL_SPEED_NIM",
            }

        if category == "jinja_logic":
            # Lightweight formatting, can use OpenRouter Free
            return {
                "provider": "openrouter_free",
                "model": "qwen-2.5-coder-free",
                "reason": "OPENROUTER_LIGHTWEIGHT",
            }

        if category == "system_architecture":
            # Heavy reasoning tasks
            if is_peak_hours:
                # During danger zone, avoid large models on NIM if possible; use Google AI Studio for capacity
                if payload_size > 10000:
                    return {
                        "provider": "google_ai_studio",
                        "model": "gemini-1.5-pro-latest",
                        "reason": "PEAK_HOUR_GOOGLE_CAPACITY",
                    }
                else:
                    return {
                        "provider": "nvidia_nim",
                        "model": "nvidia/nemotron-3-super-120b",
                        "reason": "PEAK_HOUR_NIM_REASONING",
                    }
            else:
                # Green zone: safe to use heavy models
                return {
                    "provider": "nvidia_nim",
                    "model": "nvidia/nemotron-3-super-120b",
                    "reason": "GREEN_ZONE_MAX_REASONING",
                }

        # Default fallback: try NIM first, then others
        return self._select_fallback(category, payload_size, excluded=set())

    def _select_fallback(self, category: str, payload_size: int, excluded: set) -> Dict[str, Any]:
        """Select a fallback provider when primary is unavailable."""
        # Order of preference: NIM -> Groq -> OpenRouter -> Google
        order = [
            ("nvidia_nim", "nvidia/qwen3-coder", "FALLBACK_NIM"),
            ("groq_free", "mixtral-8x7b-32768", "FALLBACK_GROQ"),
            ("openrouter_free", "qwen-2.5-coder-free", "FALLBACK_OPENROUTER"),
            ("google_ai_studio", "gemini-1.5-pro-latest", "FALLBACK_GOOGLE"),
        ]
        for provider, model, reason in order:
            if provider in excluded:
                continue
            # Simple health check: if too many consecutive failures, skip
            if self.provider_health[provider]["consecutive_failures"] >= 3:
                continue
            return {"provider": provider, "model": model, "reason": reason}
        # If all are exhausted, return first anyway (will likely fail but we tried)
        provider, model, reason = order[0]
        return {"provider": provider, "model": model, "reason": reason + "_EXHAUSTED"}

    def report_failure(self, provider: str, error_code: int):
        if error_code == 429:
            self.provider_health[provider]["last_429_time"] = time.time()
        self.provider_health[provider]["consecutive_failures"] += 1


# Backward compatibility
def get_optimal_model_for_task(category: str) -> str:
    router = StrategicTaskRouter()
    result = router.determine_optimal_route(category, payload_size=0)
    return result["model"]  # type: ignore[no-any-return]
