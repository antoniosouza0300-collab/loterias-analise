"""Score de aderência de um jogo às regras estatísticas (0–100)."""

from typing import Any

from src.config import LoteriaConfig
from src.logger import log


def calcular_score(
    jogo: list[int],
    avaliar_regras_fn: Any,
) -> dict[str, Any]:
    """
    Avalia um jogo e retorna score de 0 a 100.

    Args:
        jogo: lista de dezenas.
        avaliar_regras_fn: função avaliar_regras() da loteria específica.

    Returns:
        dict com 'score' (int), 'aprovadas' (int), 'total' (int),
        'falhas' (list[str]) e 'detalhes' (dict[str, bool]).
    """
    try:
        detalhes = avaliar_regras_fn(jogo)
    except (ValueError, TypeError) as exc:
        log.warning("Score: jogo inválido — %s", exc)
        return {
            "score": 0,
            "aprovadas": 0,
            "total": 0,
            "falhas": ["jogo inválido"],
            "detalhes": {},
        }

    total = len(detalhes)
    aprovadas = sum(1 for v in detalhes.values() if v)
    falhas = [k for k, v in detalhes.items() if not v]
    score = round((aprovadas / total) * 100) if total else 0

    return {
        "score": score,
        "aprovadas": aprovadas,
        "total": total,
        "falhas": falhas,
        "detalhes": detalhes,
    }


def classificar_score(score: int) -> tuple[str, str]:
    """Retorna (rótulo, cor) baseado no score."""
    if score >= 90:
        return "Excelente", "#22c55e"
    if score >= 70:
        return "Bom", "#84cc16"
    if score >= 50:
        return "Regular", "#f59e0b"
    if score >= 30:
        return "Fraco", "#f97316"
    return "Muito fraco", "#ef4444"


def formatar_score(resultado: dict[str, Any]) -> str:
    """Formata o resultado do score como texto legível."""
    rotulo, _ = classificar_score(resultado["score"])
    linhas = [
        f"📊 Score: {resultado['score']}/100 ({rotulo})",
        f"✅ Regras aprovadas: {resultado['aprovadas']}/{resultado['total']}",
    ]
    if resultado["falhas"]:
        linhas.append(f"❌ Falhas: {', '.join(resultado['falhas'])}")
    return "\n".join(linhas)
