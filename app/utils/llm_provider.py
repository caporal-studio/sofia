import json
import time
import urllib.error
import urllib.request
from typing import Any

from openai import OpenAI

from app.utils.app_config import get_app_info


class LLMProviderError(RuntimeError):
    pass


def _openai_key(info: dict[str, Any]) -> str:
    key = (info.get("openai_api_key") or "").strip()
    if not key:
        raise LLMProviderError(
            "OpenAI selecionado, mas nenhuma chave foi configurada. "
            "Defina OPENAI_API_KEY ou salve a chave em resources/sofia_config.json."
        )
    return key


def _chat_openai(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    timeout: float,
    max_tokens: int | None,
) -> dict[str, Any]:
    info = get_app_info()
    client = OpenAI(api_key=_openai_key(info), timeout=timeout)
    start = time.time()
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    response = client.chat.completions.create(**kwargs)
    usage = response.usage
    return {
        "text": response.choices[0].message.content.strip(),
        "provider": "openai",
        "model": model,
        "latency_ms": int((time.time() - start) * 1000),
        "tokens_prompt": getattr(usage, "prompt_tokens", 0) if usage else 0,
        "tokens_completion": getattr(usage, "completion_tokens", 0) if usage else 0,
    }


def _chat_ollama(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    timeout: float,
    max_tokens: int | None,
) -> dict[str, Any]:
    info = get_app_info()
    base_url = (info.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    options = {"temperature": temperature}
    num_predict = max_tokens or info.get("ollama_num_predict")
    if num_predict:
        options["num_predict"] = int(num_predict)

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options,
        "keep_alive": info.get("ollama_keep_alive", "30m"),
    }
    if info.get("ollama_disable_thinking", True):
        payload["think"] = False
    request = urllib.request.Request(
        f"{base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise LLMProviderError(
            f"Ollama indisponivel em {base_url}. Verifique se o Ollama esta rodando e se o modelo '{model}' foi baixado."
        ) from exc

    message = data.get("message") or {}
    return {
        "text": (message.get("content") or "").strip(),
        "provider": "ollama",
        "model": model,
        "latency_ms": int((time.time() - start) * 1000),
        "tokens_prompt": data.get("prompt_eval_count", 0) or 0,
        "tokens_completion": data.get("eval_count", 0) or 0,
    }


def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    timeout: float = 120.0,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    info = get_app_info()
    provider = (info.get("llm_provider") or "ollama").lower()
    resolved_temperature = float(temperature if temperature is not None else info.get("temperature", 0.4))

    if provider == "openai":
        resolved_model = model or info.get("openai_model", "gpt-4o-mini")
        return _chat_openai(messages, resolved_model, resolved_temperature, timeout, max_tokens)

    if provider == "ollama":
        resolved_model = model or info.get("ollama_model", "llama3.1:8b")
        return _chat_ollama(messages, resolved_model, resolved_temperature, timeout, max_tokens)

    raise LLMProviderError(f"Provider de LLM nao suportado: {provider}")
