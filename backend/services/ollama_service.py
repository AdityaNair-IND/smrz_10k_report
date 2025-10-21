import subprocess
import shutil
import os
import sys
from typing import Dict

# 🧠 Cache of running model processes
_ollama_sessions: Dict[str, subprocess.Popen] = {}

# 🚀 Safe character limit per request (prevents truncation/crashes)
CHUNK_LIMIT = 5000


def _split_prompt(prompt: str, limit: int = CHUNK_LIMIT):
    """
    Split long prompts into smaller chunks (at sentence boundaries when possible).
    """
    chunks = []
    while len(prompt) > limit:
        split_idx = prompt[:limit].rfind(".")
        if split_idx == -1:
            split_idx = limit
        chunks.append(prompt[:split_idx + 1].strip())
        prompt = prompt[split_idx + 1:]
    if prompt.strip():
        chunks.append(prompt.strip())
    return chunks


def _ensure_session(model: str):
    """
    Ensure a persistent Ollama session for the given model.
    If not already running, starts it in the background.
    """
    if model in _ollama_sessions and _ollama_sessions[model].poll() is None:
        return _ollama_sessions[model]

    if not shutil.which("ollama"):
        raise EnvironmentError("Ollama is not installed or not found in PATH.")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["LANG"] = "en_US.UTF-8"

    sys.stdout.write(f"🚀 Starting persistent session for {model}...\n")
    sys.stdout.flush()

    process = subprocess.Popen(
        ["ollama", "run", model],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env
    )

    _ollama_sessions[model] = process
    return process


def run_ollama(model: str, prompt: str) -> str:
    """
    Runs a local Ollama model using a cached persistent session.
    Handles chunked input, streaming output, and UTF-8 encoding.
    """
    prompt_chunks = _split_prompt(prompt)
    all_output = []

    for i, chunk in enumerate(prompt_chunks, 1):
        sys.stdout.write(f"🧠 Sending chunk {i}/{len(prompt_chunks)} → {model}\n")
        sys.stdout.flush()

        process = _ensure_session(model)

        try:
            # Send prompt chunk to model
            process.stdin.write(chunk + "\n")
            process.stdin.flush()

            # Collect output until completion marker or EOF
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line:
                    output_lines.append(line)
                    # Optional: detect end of response markers, if needed
                    if line.endswith("}") or len(output_lines) > 1000:
                        break

            combined_out = "\n".join(output_lines).strip()
            if combined_out:
                all_output.append(combined_out)
            else:
                all_output.append(f"[Warning: Empty output for chunk {i}]")

        except Exception as e:
            raise RuntimeError(f"Ollama session error on chunk {i}: {e}")

    final_output = "\n\n".join(all_output).strip()
    if not final_output:
        raise ValueError(f"Ollama returned no usable output for model {model}.")

    return final_output


def close_all_sessions():
    """Cleanly close all cached Ollama model sessions."""
    for model, process in _ollama_sessions.items():
        if process.poll() is None:
            sys.stdout.write(f"🧹 Closing session for {model}...\n")
            process.terminate()
    _ollama_sessions.clear()
