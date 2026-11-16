"""Cliente HTTP com retry, backoff exponencial e cache."""

import time
import json
import urllib.request
from typing import Any, Optional
from datetime import datetime, timezone

from src.config import API_TIMEOUT, API_TENTATIVAS, API_BACKOFF_BASE, CACHE_TTL_SEGUNDOS
from src.logger import log


_cache: dict[str, tuple[float, Any]] = {}


def _cache_get(chave: str) -> Optional[Any]:
    """Retorna dados do cache se ainda válidos."""
    if chave in _cache:
        ts, dados = _cache[chave]
        if (time.time() - ts) < CACHE_TTL_SEGUNDOS:
            log.debug("Cache HIT: %s", chave)
            return dados
        del _cache[chave]
    return None


def _cache_set(chave: str, dados: Any) -> None:
    """Armazena dados no cache."""
    _cache[chave] = (time.time(), dados)


def limpar_cache() -> None:
    """Limpa todo o cache em memória."""
    _cache.clear()
    log.info("Cache limpo")


def requisitar_json(
    url: str,
    usar_cache: bool = True,
    tentativas: int = API_TENTATIVAS,
    timeout: int = API_TIMEOUT,
) -> Optional[dict[str, Any]]:
    """
    Requisita JSON da API com retry e backoff exponencial.

    Retorna None se todas as tentativas falharem.
    """
    if usar_cache:
        cached = _cache_get(url)
        if cached is not None:
            return cached

    headers = {
        "User-Agent": "Mozilla/5.0 (loterias-analise)",
        "Accept": "application/json",
    }

    for tentativa in range(1, tentativas + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = json.loads(resp.read().decode("utf-8"))

            if not isinstance(dados, dict):
                log.warning("Resposta não é dict: %s", url)
                return None

            if usar_cache:
                _cache_set(url, dados)

            log.debug("API OK: %s (tentativa %d)", url, tentativa)
            return dados

        except urllib.error.HTTPError as exc:
            log.warning(
                "HTTP %d na tentativa %d/%d: %s",
                exc.code, tentativa, tentativas, url,
            )
            if exc.code in (404, 400):
                return None

        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            log.warning(
                "Erro rede tentativa %d/%d: %s — %s",
                tentativa, tentativas, url, exc,
            )

        if tentativa < tentativas:
            espera = API_BACKOFF_BASE ** tentativa
            log.info("Aguardando %ds antes de retry...", espera)
            time.sleep(espera)

    log.error("Todas as %d tentativas falharam: %s", tentativas, url)
    return None
