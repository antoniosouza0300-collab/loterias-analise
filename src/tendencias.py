"""Análise de tendências temporais por janela deslizante."""

from collections import Counter
from typing import Any

from src.config import LoteriaConfig
from src.logger import log


def frequencia_por_janela(
    historico: list[dict[str, Any]],
    lot: LoteriaConfig,
    janelas: tuple[int, ...] = (10, 20, 50),
) -> dict[int, dict[str, int]]:
    """
    Calcula frequência de cada dezena por janela deslizante.

    Returns:
        {dezena: {"j10": freq, "j20": freq, "j50": freq, "total": freq}}
    """
    if not historico:
        return {}

    resultado: dict[int, dict[str, int]] = {}
    for d in range(1, lot.dezena_maxima + 1):
        resultado[d] = {}

    for janela in janelas:
        subset = historico[-janela:] if len(historico) >= janela else historico
        counter: Counter[int] = Counter()
        for reg in subset:
            for col in lot.colunas_bolas:
                val = reg.get(col)
                if val is not None:
                    counter[int(val)] += 1
        for d in range(1, lot.dezena_maxima + 1):
            resultado[d][f"j{janela}"] = counter.get(d, 0)

    # Frequência total
    counter_total: Counter[int] = Counter()
    for reg in historico:
        for col in lot.colunas_bolas:
            val = reg.get(col)
            if val is not None:
                counter_total[int(val)] += 1
    for d in range(1, lot.dezena_maxima + 1):
        resultado[d]["total"] = counter_total.get(d, 0)

    return resultado


def classificar_tendencia(
    freq_janela_curta: int,
    freq_janela_longa: int,
    tamanho_curta: int = 10,
    tamanho_longa: int = 50,
) -> str:
    """Classifica a tendência de uma dezena."""
    if freq_janela_longa == 0:
        return "sem dados"

    taxa_curta = freq_janela_curta / tamanho_curta
    taxa_longa = freq_janela_longa / tamanho_longa

    if taxa_longa == 0:
        return "em alta" if taxa_curta > 0 else "neutra"

    razao = taxa_curta / taxa_longa
    if razao >= 1.5:
        return "🔥 em alta"
    if razao <= 0.5:
        return "🧊 em baixa"
    return "➡️ estável"


def top_tendencias(
    historico: list[dict[str, Any]],
    lot: LoteriaConfig,
    top_n: int = 10,
) -> dict[str, list[tuple[int, str, int]]]:
    """
    Retorna as dezenas com maior tendência de alta e baixa.

    Returns:
        {"alta": [(dezena, tendencia, freq_j10), ...],
         "baixa": [...]}
    """
    freqs = frequencia_por_janela(historico, lot, janelas=(10, 50))
    altas = []
    baixas = []

    for dezena, dados in freqs.items():
        f10 = dados.get("j10", 0)
        f50 = dados.get("j50", 0)
        tendencia = classificar_tendencia(f10, f50)
        if "alta" in tendencia:
            altas.append((dezena, tendencia, f10))
        elif "baixa" in tendencia:
            baixas.append((dezena, tendencia, f10))

    altas.sort(key=lambda x: x[2], reverse=True)
    baixas.sort(key=lambda x: x[2])

    return {
        "alta": altas[:top_n],
        "baixa": baixas[:top_n],
    }


def resumo_tendencias_texto(
    historico: list[dict[str, Any]],
    lot: LoteriaConfig,
) -> str:
    """Gera resumo textual das tendências."""
    if not historico:
        return "Sem dados históricos suficientes."

    top = top_tendencias(historico, lot)
    linhas = [f"📈 Tendências {lot.nome} (últimos 10 vs 50 concursos):", ""]

    if top["alta"]:
        linhas.append("🔥 Em alta:")
        for dezena, tend, freq in top["alta"][:5]:
            linhas.append(f"   Dezena {dezena:2d} — {freq}x nos últimos 10")

    if top["baixa"]:
        linhas.append("🧊 Em baixa:")
        for dezena, tend, freq in top["baixa"][:5]:
            linhas.append(f"   Dezena {dezena:2d} — {freq}x nos últimos 10")

    if not top["alta"] and not top["baixa"]:
        linhas.append("   Todas as dezenas estáveis.")

    return "\n".join(linhas)
