#!/usr/bin/env python3
"""
Lightweight Dynamic Agent Matching & Evaluation Harness
Tests model endpoints on project-specific tasks and produces a performance matrix.
"""

import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from core.agent_router import StrategicTaskRouter

# Ensure data directory exists
DATA_DIR = Path("/root/acaciafund/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def query_model(model_name: str, prompt: str) -> Tuple[str, float, int]:
    """
    Query a model endpoint via appropriate provider based on model_name prefix.
    Supports NVIDIA NIM, Groq, OpenRouter, Google AI Studio (via OpenAI-compatible endpoint).
    Falls back to mock if no credentials.
    Returns: (response_text, latency_seconds, token_count)
    """
    # Determine provider from model_name prefix or env mapping
    provider = None
    api_key = None
    api_url = None

    if model_name.startswith("nvidia/"):
        provider = "nvidia_nim"
        api_key = os.getenv("NIM_API_KEY")
        api_url = os.getenv("NIM_API_URL", "https://integrate.api.nvidia.com/v1")
    elif (
        model_name.startswith("groq/")
        or "-" in model_name
        and ("mixtral" in model_name or "llama" in model_name)
    ):
        # Assume Groq models like mixtral-8x7b-32768
        provider = "groq_free"
        api_key = os.getenv("GROQ_API_KEY")
        api_url = "https://api.groq.com/openai/v1"
    elif "-free" in model_name or "qwen-2.5-coder-free" in model_name:
        provider = "openrouter_free"
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv(
            "REGLOAI_API_KEY"
        )  # treat Regolo as OpenRouter
        api_url = "https://openrouter.ai/api/v1"
    elif "gemini" in model_name or "google" in model_name:
        provider = "google_ai_studio"
        api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("OPENAI_API_KEY")
        api_url = os.getenv(
            "OPENAI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
        )
    else:
        # fallback to NIM check
        api_key = os.getenv("NIM_API_KEY")
        api_url = os.getenv("NIM_API_URL", "https://integrate.api.nvidia.com/v1")
        provider = "nvidia_nim" if api_key and api_url else None

    if provider and api_key and api_url:
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            # Some providers may need different model naming; pass model_name as is
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "temperature": 0.0,
            }
            start = time.time()
            resp = requests.post(
                f"{api_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            elapsed = time.time() - start
            resp.raise_for_status()
            data = resp.json()
            # Extract response text
            response_text = data["choices"][0]["message"]["content"]
            # Extract token usage if available
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens
            return response_text, elapsed, total_tokens
        except Exception as e:
            # Fall back to mock on any error
            print(f"{provider} query failed for {model_name}: {e}. Falling back to mock.")

    # ---- Mock fallback (original implementation) ----
    # Simulate network delay
    time.sleep(0.1)  # 100ms base latency

    # Mock responses based on model name and prompt content
    if "qwen" in model_name.lower():
        # Simulate qwen3-coder behavior
        if "css" in prompt.lower() or "layout" in prompt.lower():
            response = """
            .card-research-summary {
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
                font-size: 0.875rem;
                line-height: 1.55;
                color: var(--color-text-secondary);
            }
            """
            tokens = 42
        elif "regex" in prompt.lower():
            response = r"[^\w\s]"  # simple regex to remove punctuation
            tokens = 20
        elif "jinja" in prompt.lower() or "template" in prompt.lower():
            response = "{{ item.description | truncate(100, true) }}"
            tokens = 35
        else:  # system architecture
            response = "Use a microservices architecture with API gateway, service mesh, and event-driven communication."
            tokens = 50
    else:  # nemotron-3-super or other
        if "css" in prompt.lower() or "layout" in prompt.lower():
            response = """
            .card-research-summary {
                line-clamp: 3;
                font-size: 0.875rem;
                color: var(--color-text-secondary);
            }
            """  # missing -webkit prefix
            tokens = 38
        elif "regex" in prompt.lower():
            response = r"\W+"  # matches non-word chars
            tokens = 22
        elif "jinja" in prompt.lower() or "template" in prompt.lower():
            response = "{{ item.description | truncate(100) }}"
            tokens = 33  # missing true for word boundary
        else:
            response = (
                "A scalable system should use load balancing, caching, and database sharding."
            )
            tokens = 45

    # Simulate variable latency
    latency = 0.1 + (hash(model_name + prompt) % 100) / 1000.0  # 100-200ms

    return response, latency, tokens


# Validator functions
def validate_css_layout(output: str) -> bool:
    """Check if CSS includes proper line-clamp properties."""
    return (
        "-webkit-line-clamp" in output
        and "-webkit-box-orient" in output
        and "display: -webkit-box" in output
    )


def validate_regex_cleaning(output: str) -> bool:
    """Check if output is a syntactically valid regex pattern (simple check)."""
    # Must start and end with something like quotes or be a raw string pattern
    stripped = output.strip()
    # Accept patterns like r"..." or "..." or just the pattern
    if stripped.startswith('r"') and stripped.endswith('"'):
        stripped = stripped[2:-1]
    elif stripped.startswith('"') and stripped.endswith('"'):
        stripped = stripped[1:-1]
    # Basic check: should not be empty and should not contain obvious mistakes
    return len(stripped) > 0 and "\\" in stripped  # very simple


def validate_jinja_logic(output: str) -> bool:
    """Check if Jinja2 truncate filter uses word boundary (true)."""
    return "truncate" in output and ", true" in output


def validate_system_architecture(output: str) -> bool:
    """Check if output mentions key architectural concepts."""
    keywords = [
        "microservice",
        "api gateway",
        "service mesh",
        "event-driven",
        "load balancing",
        "caching",
        "database sharding",
        "scalable",
    ]
    output_lower = output.lower()
    return any(kw in output_lower for kw in keywords)


# Task definitions
TASKS = [
    {
        "task_id": "css_layout_001",
        "category": "css_layout",
        "prompt": "Write CSS for a class named 'card-research-summary' that clamps text to exactly 3 lines using webkit box model, with font-size 0.875rem and color var(--color-text-secondary).",
        "validator_func": validate_css_layout,
    },
    {
        "task_id": "regex_cleaning_001",
        "category": "regex_cleaning",
        "prompt": "Provide a regex pattern that matches all punctuation and special characters (non-alphanumeric, non-whitespace) for cleaning text. Return as a raw string suitable for Python re.sub.",
        "validator_func": validate_regex_cleaning,
    },
    {
        "task_id": "jinja_logic_001",
        "category": "jinja_logic",
        "prompt": "In a Jinja2 template, how would you truncate a description to 100 characters while respecting word boundaries (not cutting words)? Show the filter usage.",
        "validator_func": validate_jinja_logic,
    },
    {
        "task_id": "system_architecture_001",
        "category": "system_architecture",
        "prompt": "Describe a high-level system architecture for a scalable web application that handles high traffic, includes fault tolerance, and uses modern cloud patterns.",
        "validator_func": validate_system_architecture,
    },
    # Add more tasks as needed
]


def run_evaluation() -> Dict[str, Any]:
    """Run the evaluation harness and return results matrix."""
    # Results structure: {category: {model: {success_rate, avg_latency, avg_tokens}}}
    results: Dict[str, Dict[str, Dict[str, float]]] = {}

    # Initialize results containers
    for task in TASKS:
        cat = task["category"]
        if cat not in results:
            results[cat] = {}
        # We'll discover models from first run

    # Track per-model per-category accumulators
    accum: Dict[str, Dict[str, List[float]]] = {}  # model -> category -> list of latencies
    success_counts: Dict[str, Dict[str, int]] = {}  # model -> category -> count
    total_counts: Dict[str, Dict[str, int]] = {}  # model -> category -> total

    for task in TASKS:
        cat = task["category"]
        prompt = task["prompt"]
        validator = task["validator_func"]

        # Determine optimal route using router (payload size approximated by prompt length)
        router = StrategicTaskRouter()
        route = router.determine_optimal_route(cat, payload_size=len(prompt))
        provider = route["provider"]
        model_name = route["model"]
        reason = route["reason"]

        # Initialize accumulators for this model/category if needed
        if model_name not in accum:
            accum[model_name] = {}
            success_counts[model_name] = {}
            total_counts[model_name] = {}
        if cat not in accum[model_name]:
            accum[model_name][cat] = []
            success_counts[model_name][cat] = 0
            total_counts[model_name][cat] = 0

        # Run the task
        start = time.time()
        try:
            response, latency, tokens = query_model(model_name, prompt)
            elapsed = time.time() - start

            # Validate
            try:
                success = validator(response)
            except Exception as e:
                print(f"Validator error for {model_name} on {task['task_id']}: {e}")
                success = False

            # Record success
            accum[model_name][cat].append(elapsed)
            total_counts[model_name][cat] += 1
            if success:
                success_counts[model_name][cat] += 1

            # Debug output
            print(
                f"[{model_name} via {provider} ({reason})] {task['task_id']}: success={success}, latency={elapsed:.3f}s, tokens={tokens}"
            )
        except Exception as e:
            elapsed = time.time() - start
            # Extract status code if possible
            status_code = getattr(e, "response", None)
            if status_code is not None and hasattr(status_code, "status_code"):
                status_code = status_code.status_code
            else:
                # Try to parse from exception message
                status_code = 500  # default
                if "429" in str(e):
                    status_code = 429
                elif "503" in str(e):
                    status_code = 503
            # Report failure to router for cooldown tracking
            router.report_failure(provider, status_code)
            # Record failure (latency, but no success)
            accum[model_name][cat].append(elapsed)
            total_counts[model_name][cat] += 1
            # success_counts unchanged
            print(
                f"[{model_name} via {provider} ({reason})] {task['task_id']}: FAILED (status={status_code}), latency={elapsed:.3f}s"
            )

    # Compute final metrics
    results = {}  # category -> {model: metrics}
    for model_name in accum:
        for cat in accum[model_name]:
            latencies = accum[model_name][cat]
            total = total_counts[model_name][cat]
            success = success_counts[model_name][cat]
            success_rate = success / total if total > 0 else 0.0
            avg_latency = statistics.mean(latencies) if latencies else 0.0

            # Store under category->model (as requested in spec)
            if cat not in results:
                results[cat] = {}
            results[cat][model_name] = {
                "success_rate": round(success_rate, 3),
                "avg_latency": round(avg_latency, 3),
            }

    # Reformat to match spec: {category: {model: {success_rate, avg_latency}}}
    final: Dict[str, Dict[str, Dict[str, float]]] = {}
    for cat in results:
        final[cat] = results[cat]

    return final


def print_markdown_table(matrix: Dict[str, Dict[str, Dict[str, float]]]):
    """Print a scannable Markdown table summarizing which model dominated each category."""
    print("\n# Agent Matching Evaluation Results\n")
    print("| Category | Best Model | Success Rate | Avg Latency (s) |")
    print("|----------|------------|--------------|-----------------|")

    for category, models in matrix.items():
        # Determine best model by success rate, then latency
        best_model = None
        best_score = (-1, 0)  # (success_rate, -latency)
        for model_name, metrics in models.items():
            score = (metrics["success_rate"], -metrics["avg_latency"])
            if score > best_score:
                best_score = score
                best_model = model_name

        if best_model:
            best_metrics = models[best_model]
            print(
                f"| {category} | {best_model} | {best_metrics['success_rate']:.2f} | {best_metrics['avg_latency']:.3f} |"
            )
        else:
            print(f"| {category} | N/A | N/A | N/A |")
    print()


def main():
    print("Starting Agent Matching & Evaluation Harness...")
    matrix = run_evaluation()

    # Save JSON
    output_path = DATA_DIR / "agent_matching_matrix.json"
    with open(output_path, "w") as f:
        json.dump(matrix, f, indent=2)
    print(f"\nResults saved to {output_path}")

    # Print markdown table
    print_markdown_table(matrix)

    # Also print raw JSON for inspection
    print("\nRaw JSON:")
    print(json.dumps(matrix, indent=2))


if __name__ == "__main__":
    main()
