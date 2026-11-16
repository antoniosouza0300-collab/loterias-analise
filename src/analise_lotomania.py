"""Análises estatísticas completas da Lotomania (20 de 100)."""

from collections import Counter
from typing import Any

from src.regras_lotomania import (
    TOTAL_DEZENAS,
    DEZENA_MAXIMA,
    MOLDURA,
    PRIMOS,
    GEMEOS,
    MIOLO,
    FIBONACCI,
    calcular_metricas,
    avaliar_regras,
)


def frequencia_dezenas(historico: list[dict[str, Any]]) -> dict[int, int]:
    """Frequência de cada dezena no histórico."""
    counter: Counter[int] = Counter()
    for reg in historico:
        for i in range(1, TOTAL_DEZENAS + 1):
            col = f"bola{i}"
            val = reg.get(col)
            if val is not None:
                counter[int(val)] += 1
    return {d: counter.get(d, 0) for d in range(1, DEZENA_MAXIMA + 1)}


def atraso_dezenas(historico: list[dict[str, Any]]) -> dict[int, int]:
    """Atraso (concursos sem sair) de cada dezena."""
    if not historico:
        return {d: 0 for d in range(1, DEZENA_MAXIMA + 1)}

    ultimo = max(int(r.get("concurso", 0)) for r in historico)
    ultima_aparicao: dict[int, int] = {}

    for reg in historico:
        c = int(reg.get("concurso", 0))
        for i in range(1, TOTAL_DEZENAS + 1):
            val = reg.get(f"bola{i}")
            if val is not None:
                d = int(val)
                if d not in ultima_aparicao or c > ultima_aparicao[d]:
                    ultima_aparicao[d] = c

    return {d: ultimo - ultima_aparicao.get(d, 0) for d in range(1, DEZENA_MAXIMA + 1)}


def classificar_temperatura(
    freq: dict[int, int],
) -> dict[str, list[int]]:
    """Classifica dezenas em quentes, mornas e frias."""
    if not freq:
        return {"quentes": [], "mornas": [], "frias": []}

    valores = sorted(freq.values(), reverse=True)
    top = len(valores) // 4
    limiar_quente = valores[top] if top < len(valores) else 0
    limiar_frio = valores[-top] if top < len(valores) else 0

    quentes, mornas, frias = [], [], []
    for d, f in freq.items():
        if f >= limiar_quente:
            quentes.append(d)
        elif f <= limiar_frio:
            frias.append(d)
        else:
            mornas.append(d)

    return {"quentes": sorted(quentes), "mornas": sorted(mornas), "frias": sorted(frias)}


def analisar_concurso(registro: dict[str, Any]) -> dict[str, Any]:
    """Análise completa de um concurso."""
    dezenas = []
    for i in range(1, TOTAL_DEZENAS + 1):
        val = registro.get(f"bola{i}")
        if val is not None:
            dezenas.append(int(val))

    if len(dezenas) != TOTAL_DEZENAS:
        return {"erro": "Registro incompleto"}

    metricas = calcular_metricas(dezenas)
    regras = avaliar_regras(dezenas)

    return {
        "concurso": registro.get("concurso"),
        "data": registro.get("data"),
        "dezenas": dezenas,
        "metricas": metricas,
        "regras": regras,
        "score": round(sum(regras.values()) / len(regras) * 100),
    }


def gerar_jogo_aleatorio(
    quentes: int = 8,
    mornas: int = 7,
    frias: int = 5,
    temperatura: dict[str, list[int]] | None = None,
) -> list[int]:
    """Gera um jogo aleatório respeitando distribuição de temperatura."""
    import random

    if temperatura is None:
        todas = list(range(1, DEZENA_MAXIMA + 1))
        random.shuffle(todas)
        return sorted(todas[:TOTAL_DEZENAS])

    q = temperatura.get("quentes", [])
    m = temperatura.get("mornas", [])
    f = temperatura.get("frias", [])

    jogo: set[int] = set()
    for pool, n in [(q, quentes), (m, mornas), (f, frias)]:
        disponiveis = [d for d in pool if d not in jogo]
        jogo.update(random.sample(disponiveis, min(n, len(disponiveis))))

    # Completa se faltar
    while len(jogo) < TOTAL_DEZENAS:
        d = random.randint(1, DEZENA_MAXIMA)
        jogo.add(d)

    return sorted(list(jogo)[:TOTAL_DEZENAS])
