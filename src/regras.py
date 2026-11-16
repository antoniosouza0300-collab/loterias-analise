"""Cálculo e validação independente das 15 regras da Lotofácil."""

from collections import Counter
from typing import Any


TOTAL_DEZENAS = 15
DEZENA_MINIMA = 1
DEZENA_MAXIMA = 25

MOLDURA = {
    1, 2, 3, 4, 5,
    6, 10, 11, 15,
    16, 20, 21, 22, 23, 24, 25,
}
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
MULTIPLOS_DE_3 = {3, 6, 9, 12, 15, 18, 21, 24}
GEMEOS = {11, 22}
MIOLO = {7, 8, 9, 12, 13, 14, 17, 18, 19}
DIAGONAL_PRINCIPAL = {1, 7, 13, 19, 25}
DIAGONAL_SECUNDARIA = {5, 9, 13, 17, 21}
FIBONACCI = {1, 2, 3, 5, 8, 13, 21}


def validar_entrada(jogo: Any) -> list[int]:
    """Valida e normaliza um jogo de 15 dezenas."""
    if isinstance(jogo, (str, bytes)):
        raise ValueError("O jogo deve ser uma sequência de 15 dezenas.")

    try:
        dezenas = list(jogo)
    except TypeError as exc:
        raise ValueError("O jogo deve ser uma sequência de 15 dezenas.") from exc

    if len(dezenas) != TOTAL_DEZENAS:
        raise ValueError("O jogo deve conter exatamente 15 dezenas.")

    if any(type(d) is not int for d in dezenas):
        raise ValueError("Todas as dezenas devem ser números inteiros.")

    if len(set(dezenas)) != TOTAL_DEZENAS:
        raise ValueError("O jogo não pode conter dezenas repetidas.")

    if any(d < DEZENA_MINIMA or d > DEZENA_MAXIMA for d in dezenas):
        raise ValueError("As dezenas devem estar entre 1 e 25.")

    return sorted(dezenas)


def calcular_metricas(jogo: Any) -> dict[str, Any]:
    """Calcula as métricas necessárias para avaliar as 15 regras."""
    dezenas = validar_entrada(jogo)
    conjunto = set(dezenas)

    linhas = [
        [d for d in dezenas if inicio <= d <= inicio + 4]
        for inicio in (1, 6, 11, 16, 21)
    ]
    colunas = [
        [d for d in dezenas if (d - 1) % 5 == coluna]
        for coluna in range(5)
    ]

    quadrantes = [
        [d for d in dezenas if (d - 1) // 5 < 3 and (d - 1) % 5 < 3],
        [d for d in dezenas if (d - 1) // 5 < 3 and (d - 1) % 5 >= 3],
        [d for d in dezenas if (d - 1) // 5 >= 3 and (d - 1) % 5 < 3],
        [d for d in dezenas if (d - 1) // 5 >= 3 and (d - 1) % 5 >= 3],
    ]

    finais = Counter(d % 10 for d in dezenas)
    pares_por_linha = [
        sum(d % 2 == 0 for d in linhas[i])
        for i in range(2)
    ]

    return {
        "dezenas": dezenas,
        "soma": sum(dezenas),
        "moldura": len(conjunto & MOLDURA),
        "pares": sum(d % 2 == 0 for d in dezenas),
        "primos": len(conjunto & PRIMOS),
        "multiplos_de_3": len(conjunto & MULTIPLOS_DE_3),
        "gemeos": len(conjunto & GEMEOS),
        "linhas": [len(linha) for linha in linhas],
        "pares_linhas_1_e_2": pares_por_linha,
        "quadrantes": [len(q) for q in quadrantes],
        "miolo": len(conjunto & MIOLO),
        "maior_frequencia_final": max(finais.values()),
        "colunas": [len(coluna) for coluna in colunas],
        "diagonal_principal": len(conjunto & DIAGONAL_PRINCIPAL),
        "diagonal_secundaria": len(conjunto & DIAGONAL_SECUNDARIA),
        "fibonacci": len(conjunto & FIBONACCI),
        "menor_dezena": min(dezenas),
        "maior_dezena": max(dezenas),
    }


def avaliar_regras(jogo: Any) -> dict[str, bool]:
    """Retorna o resultado individual das 15 regras."""
    m = calcular_metricas(jogo)

    return {
        "soma": 166 <= m["soma"] <= 224,
        "moldura": 9 <= m["moldura"] <= 11,
        "pares": 6 <= m["pares"] <= 9,
        "primos": 4 <= m["primos"] <= 7,
        "multiplos_de_3": 4 <= m["multiplos_de_3"] <= 6,
        "gemeos": m["gemeos"] <= 1,
        "linhas": all(1 <= n <= 4 for n in m["linhas"]),
        "paridade_linhas_1_e_2": all(
            pares < 5 for pares in m["pares_linhas_1_e_2"]
        ),
        "quadrantes": (
            min(m["quadrantes"]) >= 2
            and max(m["quadrantes"]) <= 6
        ),
        "miolo": 3 <= m["miolo"] <= 6,
        "finais": m["maior_frequencia_final"] <= 4,
        "colunas": (
            min(m["colunas"]) >= 1
            and max(m["colunas"]) <= 4
        ),
        "diagonais": (
            2 <= m["diagonal_principal"] <= 4
            and 2 <= m["diagonal_secundaria"] <= 4
        ),
        "fibonacci": 3 <= m["fibonacci"] <= 5,
        "inicio_fim": (
            m["menor_dezena"] <= 4
            and m["maior_dezena"] >= 22
        ),
    }


def validar_jogo(jogo: Any) -> bool:
    """Retorna True somente quando as 15 regras são aprovadas."""
    return all(avaliar_regras(jogo).values())
