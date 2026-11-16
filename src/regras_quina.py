"""Cálculo e validação independente das 15 regras da Quina (5 de 80)."""

from collections import Counter
from typing import Any


TOTAL_DEZENAS = 5
DEZENA_MINIMA = 1
DEZENA_MAXIMA = 80

MOLDURA = set(range(1, 11)) | set(range(71, 81))
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
          43, 47, 53, 59, 61, 67, 71, 73, 79}
MULTIPLOS_DE_3 = {d for d in range(3, 81, 3)}
GEMEOS = {11, 22, 33, 44, 55, 66, 77}
MIOLO = set(range(21, 61))
FIBONACCI = {1, 2, 3, 5, 8, 13, 21, 34, 55}


def validar_entrada(jogo: Any) -> list[int]:
    """Valida e normaliza um jogo de 5 dezenas."""
    if isinstance(jogo, (str, bytes)):
        raise ValueError("O jogo deve ser uma sequência de 5 dezenas.")

    try:
        dezenas = list(jogo)
    except TypeError as exc:
        raise ValueError("O jogo deve ser uma sequência de 5 dezenas.") from exc

    if len(dezenas) != TOTAL_DEZENAS:
        raise ValueError("O jogo deve conter exatamente 5 dezenas.")

    if any(type(d) is not int for d in dezenas):
        raise ValueError("Todas as dezenas devem ser números inteiros.")

    if len(set(dezenas)) != TOTAL_DEZENAS:
        raise ValueError("O jogo não pode conter dezenas repetidas.")

    if any(d < DEZENA_MINIMA or d > DEZENA_MAXIMA for d in dezenas):
        raise ValueError("As dezenas devem estar entre 1 e 80.")

    return sorted(dezenas)


def calcular_metricas(jogo: Any) -> dict[str, Any]:
    """Calcula as métricas necessárias para avaliar as 15 regras."""
    dezenas = validar_entrada(jogo)
    conjunto = set(dezenas)

    faixas = [
        len([d for d in dezenas if 1 <= d <= 20]),
        len([d for d in dezenas if 21 <= d <= 40]),
        len([d for d in dezenas if 41 <= d <= 60]),
        len([d for d in dezenas if 61 <= d <= 80]),
    ]

    quadrantes = [
        len([d for d in dezenas if 1 <= d <= 20]),
        len([d for d in dezenas if 21 <= d <= 40]),
        len([d for d in dezenas if 41 <= d <= 60]),
        len([d for d in dezenas if 61 <= d <= 80]),
    ]

    grupos_mod8 = Counter(d % 8 for d in dezenas)
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
        "grupos_mod8": list(grupos_mod8.values()),
        "fibonacci": len(conjunto & FIBONACCI),
        "menor_dezena": min(dezenas),
        "maior_dezena": max(dezenas),
        "amplitude": max(dezenas) - min(dezenas),
    }


def avaliar_regras(jogo: Any) -> dict[str, bool]:
    """Retorna o resultado individual das 15 regras."""
    m = calcular_metricas(jogo)

    return {
        "soma": 120 <= m["soma"] <= 290,
        "moldura": 1 <= m["moldura"] <= 3,
        "pares": 1 <= m["pares"] <= 4,
        "primos": 1 <= m["primos"] <= 3,
        "multiplos_de_3": 0 <= m["multiplos_de_3"] <= 3,
        "gemeos": m["gemeos"] <= 1,
        "faixas": all(0 <= n <= 3 for n in m["faixas"]) and sum(1 for n in m["faixas"] if n > 0) >= 2,
        "consecutivos": m["max_consecutivos"] <= 2,
        "quadrantes": max(m["quadrantes"]) <= 3,
        "miolo": 1 <= m["miolo"] <= 4,
        "finais": m["maior_frequencia_final"] <= 2,
        "grupos_mod8": max(m["grupos_mod8"]) <= 2 if m["grupos_mod8"] else True,
        "fibonacci": 0 <= m["fibonacci"] <= 2,
        "inicio_fim": m["menor_dezena"] <= 15 and m["maior_dezena"] >= 66,
        "amplitude": 30 <= m["amplitude"] <= 75,
    }


def validar_jogo(jogo: Any) -> bool:
    """Retorna True somente quando as 15 regras são aprovadas."""
    return all(avaliar_regras(jogo).values())
