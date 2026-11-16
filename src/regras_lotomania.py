"""Cálculo e validação independente das 15 regras da Lotomania (20 de 100)."""

from collections import Counter
from typing import Any


TOTAL_DEZENAS = 20
DEZENA_MINIMA = 1
DEZENA_MAXIMA = 100

MOLDURA = set(range(1, 11)) | set(range(91, 101))
PRIMOS = {
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
    43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97,
}
MULTIPLOS_DE_3 = {d for d in range(3, 101, 3)}
GEMEOS = {11, 22, 33, 44, 55, 66, 77, 88, 99}
MIOLO = set(range(21, 81))
FIBONACCI = {1, 2, 3, 5, 8, 13, 21, 34, 55, 89}


def validar_entrada(jogo: Any) -> list[int]:
    """Valida e normaliza um jogo de 20 dezenas."""
    if isinstance(jogo, (str, bytes)):
        raise ValueError("O jogo deve ser uma sequência de 20 dezenas.")

    try:
        dezenas = list(jogo)
    except TypeError as exc:
        raise ValueError("O jogo deve ser uma sequência de 20 dezenas.") from exc

    if len(dezenas) != TOTAL_DEZENAS:
        raise ValueError(f"O jogo deve conter exatamente {TOTAL_DEZENAS} dezenas.")

    if any(type(d) is not int for d in dezenas):
        raise ValueError("Todas as dezenas devem ser números inteiros.")

    if len(set(dezenas)) != TOTAL_DEZENAS:
        raise ValueError("O jogo não pode conter dezenas repetidas.")

    if any(d < DEZENA_MINIMA or d > DEZENA_MAXIMA for d in dezenas):
        raise ValueError("As dezenas devem estar entre 1 e 100.")

    return sorted(dezenas)


def calcular_metricas(jogo: Any) -> dict[str, Any]:
    """Calcula as métricas necessárias para avaliar as 15 regras."""
    dezenas = validar_entrada(jogo)
    conjunto = set(dezenas)

    faixas = [
        len([d for d in dezenas if 1 <= d <= 25]),
        len([d for d in dezenas if 26 <= d <= 50]),
        len([d for d in dezenas if 51 <= d <= 75]),
        len([d for d in dezenas if 76 <= d <= 100]),
    ]

    quadrantes = list(faixas)

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
        "soma": 750 <= m["soma"] <= 1270,
        "moldura": 2 <= m["moldura"] <= 7,
        "pares": 6 <= m["pares"] <= 14,
        "primos": 2 <= m["primos"] <= 8,
        "multiplos_de_3": 3 <= m["multiplos_de_3"] <= 10,
        "gemeos": m["gemeos"] <= 3,
        "faixas": all(2 <= n <= 8 for n in m["faixas"]) and sum(1 for n in m["faixas"] if n > 0) >= 3,
        "consecutivos": m["max_consecutivos"] <= 4,
        "quadrantes": max(m["quadrantes"]) <= 8,
        "miolo": 8 <= m["miolo"] <= 16,
        "finais": m["maior_frequencia_final"] <= 4,
        "grupos_mod8": max(m["grupos_mod8"]) <= 4 if m["grupos_mod8"] else True,
        "fibonacci": 0 <= m["fibonacci"] <= 4,
        "inicio_fim": m["menor_dezena"] <= 10 and m["maior_dezena"] >= 91,
        "amplitude": 60 <= m["amplitude"] <= 98,
    }


def validar_jogo(jogo: Any) -> bool:
    """Retorna True somente quando as 15 regras são aprovadas."""
    return all(avaliar_regras(jogo).values())
