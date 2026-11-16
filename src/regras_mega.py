"""Cálculo e validação independente das 15 regras da Mega-Sena (6 de 60)."""

from collections import Counter
from typing import Any


TOTAL_DEZENAS = 6
DEZENA_MINIMA = 1
DEZENA_MAXIMA = 60

MOLDURA = set(range(1, 11)) | set(range(51, 61))
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}
MULTIPLOS_DE_3 = {3, 6, 9, 12, 15, 18, 21, 24, 27, 30,
                  33, 36, 39, 42, 45, 48, 51, 54, 57, 60}
GEMEOS = {11, 22, 33, 44, 55}
MIOLO = set(range(16, 46))
FIBONACCI = {1, 2, 3, 5, 8, 13, 21, 34, 55}


def validar_entrada(jogo: Any) -> list[int]:
    """Valida e normaliza um jogo de 6 dezenas."""
    if isinstance(jogo, (str, bytes)):
        raise ValueError("O jogo deve ser uma sequência de 6 dezenas.")

    try:
        dezenas = list(jogo)
    except TypeError as exc:
        raise ValueError("O jogo deve ser uma sequência de 6 dezenas.") from exc

    if len(dezenas) != TOTAL_DEZENAS:
        raise ValueError("O jogo deve conter exatamente 6 dezenas.")

    if any(type(d) is not int for d in dezenas):
        raise ValueError("Todas as dezenas devem ser números inteiros.")

    if len(set(dezenas)) != TOTAL_DEZENAS:
        raise ValueError("O jogo não pode conter dezenas repetidas.")

    if any(d < DEZENA_MINIMA or d > DEZENA_MAXIMA for d in dezenas):
        raise ValueError("As dezenas devem estar entre 1 e 60.")

    return sorted(dezenas)


def calcular_metricas(jogo: Any) -> dict[str, Any]:
    """Calcula as métricas necessárias para avaliar as 15 regras."""
    dezenas = validar_entrada(jogo)
    conjunto = set(dezenas)

    faixas = [
        len([d for d in dezenas if 1 <= d <= 15]),
        len([d for d in dezenas if 16 <= d <= 30]),
        len([d for d in dezenas if 31 <= d <= 45]),
        len([d for d in dezenas if 46 <= d <= 60]),
    ]

    quadrantes = [
        len([d for d in dezenas if 1 <= d <= 15]),
        len([d for d in dezenas if 16 <= d <= 30]),
        len([d for d in dezenas if 31 <= d <= 45]),
        len([d for d in dezenas if 46 <= d <= 60]),
    ]

    grupos_mod6 = Counter(d % 6 for d in dezenas)
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
        "grupos_mod6": list(grupos_mod6.values()),
        "fibonacci": len(conjunto & FIBONACCI),
        "menor_dezena": min(dezenas),
        "maior_dezena": max(dezenas),
        "amplitude": max(dezenas) - min(dezenas),
    }


def avaliar_regras(jogo: Any) -> dict[str, bool]:
    """Retorna o resultado individual das 15 regras."""
    m = calcular_metricas(jogo)

    return {
        "soma": 120 <= m["soma"] <= 250,
        "moldura": 1 <= m["moldura"] <= 4,
        "pares": 2 <= m["pares"] <= 4,
        "primos": 1 <= m["primos"] <= 4,
        "multiplos_de_3": 1 <= m["multiplos_de_3"] <= 3,
        "gemeos": m["gemeos"] <= 1,
        "faixas": all(1 <= n <= 3 for n in m["faixas"]),
        "consecutivos": m["max_consecutivos"] <= 2,
        "quadrantes": max(m["quadrantes"]) <= 3,
        "miolo": 2 <= m["miolo"] <= 5,
        "finais": m["maior_frequencia_final"] <= 2,
        "grupos_mod6": max(m["grupos_mod6"]) <= 2 if m["grupos_mod6"] else True,
        "fibonacci": 1 <= m["fibonacci"] <= 3,
        "inicio_fim": m["menor_dezena"] <= 10 and m["maior_dezena"] >= 51,
        "amplitude": 25 <= m["amplitude"] <= 55,
    }


def validar_jogo(jogo: Any) -> bool:
    """Retorna True somente quando as 15 regras são aprovadas."""
    return all(avaliar_regras(jogo).values())
