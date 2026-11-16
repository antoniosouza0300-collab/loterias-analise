"""Cálculo e validação independente das 15 regras do Dia de Sorte (7 de 31)."""

from collections import Counter
from typing import Any


TOTAL_DEZENAS = 7
DEZENA_MINIMA = 1
DEZENA_MAXIMA = 31

MOLDURA = {1, 2, 3, 4, 5, 27, 28, 29, 30, 31}
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
MULTIPLOS_DE_3 = {3, 6, 9, 12, 15, 18, 21, 24, 27, 30}
GEMEOS = {11, 22}
MIOLO = set(range(6, 27))
FIBONACCI = {1, 2, 3, 5, 8, 13, 21}


def validar_entrada(jogo: Any) -> list[int]:
    """Valida e normaliza um jogo de 7 dezenas."""
    if isinstance(jogo, (str, bytes)):
        raise ValueError("O jogo deve ser uma sequência de 7 dezenas.")

    try:
        dezenas = list(jogo)
    except TypeError as exc:
        raise ValueError("O jogo deve ser uma sequência de 7 dezenas.") from exc

    if len(dezenas) != TOTAL_DEZENAS:
        raise ValueError("O jogo deve conter exatamente 7 dezenas.")

    if any(type(d) is not int for d in dezenas):
        raise ValueError("Todas as dezenas devem ser números inteiros.")

    if len(set(dezenas)) != TOTAL_DEZENAS:
        raise ValueError("O jogo não pode conter dezenas repetidas.")

    if any(d < DEZENA_MINIMA or d > DEZENA_MAXIMA for d in dezenas):
        raise ValueError("As dezenas devem estar entre 1 e 31.")

    return sorted(dezenas)


def calcular_metricas(jogo: Any) -> dict[str, Any]:
    """Calcula as métricas necessárias para avaliar as 15 regras."""
    dezenas = validar_entrada(jogo)
    conjunto = set(dezenas)

    faixas = [
        len([d for d in dezenas if 1 <= d <= 10]),
        len([d for d in dezenas if 11 <= d <= 20]),
        len([d for d in dezenas if 21 <= d <= 31]),
    ]

    quadrantes = [
        len([d for d in dezenas if 1 <= d <= 8]),
        len([d for d in dezenas if 9 <= d <= 16]),
        len([d for d in dezenas if 17 <= d <= 24]),
        len([d for d in dezenas if 25 <= d <= 31]),
    ]

    grupos_mod5 = Counter(d % 5 for d in dezenas)
    finais = Counter(d % 10 for d in dezenas)

    max_consec = 1
    atual = 1
    for i in range(1, len(dezenas)):
        if dezenas[i] == dezenas[i - 1] + 1:
            atual += 1
            max_consec = max(max_consec, atual)
        else:
            atual = 1

    return {
        "dezenas": dezenas,
        "soma": sum(dezenas),
        "moldura": len(conjunto & MOLDURA),
        "pares": sum(d % 2 == 0 for d in dezenas),
        "primos": len(conjunto & PRIMOS),
        "multiplos_de_3": len(conjunto & MULTIPLOS_DE_3),
        "gemeos": len(conjunto & GEMEOS),
        "faixas": faixas,
        "max_consecutivos": max_consec,
        "quadrantes": quadrantes,
        "miolo": len(conjunto & MIOLO),
        "maior_frequencia_final": max(finais.values()),
        "grupos_mod5": list(grupos_mod5.values()),
        "fibonacci": len(conjunto & FIBONACCI),
        "menor_dezena": min(dezenas),
        "maior_dezena": max(dezenas),
        "amplitude": max(dezenas) - min(dezenas),
    }


def avaliar_regras(jogo: Any) -> dict[str, bool]:
    """Retorna o resultado individual das 15 regras."""
    m = calcular_metricas(jogo)

    return {
        "soma": 70 <= m["soma"] <= 154,
        "moldura": 1 <= m["moldura"] <= 4,
        "pares": 2 <= m["pares"] <= 5,
        "primos": 1 <= m["primos"] <= 4,
        "multiplos_de_3": 1 <= m["multiplos_de_3"] <= 4,
        "gemeos": m["gemeos"] <= 1,
        "faixas": all(1 <= n <= 4 for n in m["faixas"]),
        "consecutivos": m["max_consecutivos"] <= 3,
        "quadrantes": max(m["quadrantes"]) <= 4,
        "miolo": 3 <= m["miolo"] <= 6,
        "finais": m["maior_frequencia_final"] <= 3,
        "grupos_mod5": max(m["grupos_mod5"]) <= 3 if m["grupos_mod5"] else True,
        "fibonacci": 1 <= m["fibonacci"] <= 3,
        "inicio_fim": m["menor_dezena"] <= 5 and m["maior_dezena"] >= 27,
        "amplitude": 15 <= m["amplitude"] <= 29,
    }


def validar_jogo(jogo: Any) -> bool:
    """Retorna True somente quando as 15 regras são aprovadas."""
    return all(avaliar_regras(jogo).values())
