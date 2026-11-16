"""Gráficos interativos com Plotly para o dashboard."""

from typing import Any

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import LoteriaConfig
from src.logger import log


def grafico_frequencia_dezenas(
    historico: list[dict[str, Any]],
    lot: LoteriaConfig,
) -> go.Figure:
    """Heatmap de barras: frequência de cada dezena."""
    if not historico:
        return go.Figure().update_layout(title="Sem dados")

    from collections import Counter
    counter: Counter[int] = Counter()
    for reg in historico:
        for col in lot.colunas_bolas:
            val = reg.get(col)
            if val is not None:
                counter[int(val)] += 1

    dezenas = list(range(1, lot.dezena_maxima + 1))
    freqs = [counter.get(d, 0) for d in dezenas]
    max_freq = max(freqs) if freqs else 1

    cores = [
        "#22c55e" if f >= max_freq * 0.75
        else "#f59e0b" if f >= max_freq * 0.4
        else "#ef4444"
        for f in freqs
    ]

    fig = go.Figure(go.Bar(
        x=dezenas, y=freqs,
        marker_color=cores,
        hovertemplate="Dezena %{x}<br>Frequência: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title=f"Frequência das Dezenas — {lot.emoji} {lot.nome}",
        xaxis_title="Dezena",
        yaxis_title="Vezes sorteada",
        template="plotly_dark",
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def grafico_atraso_dezenas(
    historico: list[dict[str, Any]],
    lot: LoteriaConfig,
) -> go.Figure:
    """Barras horizontais: atraso de cada dezena (concursos sem sair)."""
    if not historico:
        return go.Figure().update_layout(title="Sem dados")

    ultimo_concurso = max(int(r.get("concurso", 0)) for r in historico)
    ultima_aparicao: dict[int, int] = {}

    for reg in historico:
        c = int(reg.get("concurso", 0))
        for col in lot.colunas_bolas:
            val = reg.get(col)
            if val is not None:
                d = int(val)
                if d not in ultima_aparicao or c > ultima_aparicao[d]:
                    ultima_aparicao[d] = c

    dezenas = list(range(1, lot.dezena_maxima + 1))
    atrasos = [ultimo_concurso - ultima_aparicao.get(d, 0) for d in dezenas]

    # Top 20 mais atrasadas
    pares = sorted(zip(dezenas, atrasos), key=lambda x: x[1], reverse=True)[:20]
    dez_top = [p[0] for p in reversed(pares)]
    atr_top = [p[1] for p in reversed(pares)]

    fig = go.Figure(go.Bar(
        y=[f"D{d}" for d in dez_top],
        x=atr_top,
        orientation="h",
        marker_color="#f97316",
        hovertemplate="Dezena %{y}<br>Atraso: %{x} concursos<extra></extra>",
    ))
    fig.update_layout(
        title=f"Top 20 Dezenas Mais Atrasadas — {lot.emoji} {lot.nome}",
        xaxis_title="Concursos de atraso",
        template="plotly_dark",
        height=450,
        margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig


def grafico_soma_temporal(
    historico: list[dict[str, Any]],
    lot: LoteriaConfig,
) -> go.Figure:
    """Linha temporal da soma das dezenas por concurso."""
    if not historico:
        return go.Figure().update_layout(title="Sem dados")

    concursos = []
    somas = []
    for reg in historico:
        concursos.append(int(reg.get("concurso", 0)))
        soma = sum(
            int(reg.get(col, 0)) for col in lot.colunas_bolas
            if reg.get(col) is not None
        )
        somas.append(soma)

    fig = go.Figure(go.Scatter(
        x=concursos, y=somas,
        mode="lines+markers",
        marker=dict(size=4),
        line=dict(color=lot.cor, width=2),
        hovertemplate="Concurso %{x}<br>Soma: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title=f"Soma das Dezenas por Concurso — {lot.emoji} {lot.nome}",
        xaxis_title="Concurso",
        yaxis_title="Soma",
        template="plotly_dark",
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def grafico_pares_impares(
    historico: list[dict[str, Any]],
    lot: LoteriaConfig,
) -> go.Figure:
    """Distribuição de pares vs ímpares por concurso (últimos 20)."""
    if not historico:
        return go.Figure().update_layout(title="Sem dados")

    subset = historico[-20:]
    concursos = [int(r.get("concurso", 0)) for r in subset]
    pares = []
    impares = []
    for reg in subset:
        p = sum(
            1 for col in lot.colunas_bolas
            if reg.get(col) is not None and int(reg[col]) % 2 == 0
        )
        pares.append(p)
        impares.append(lot.total_dezenas - p)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=concursos, y=pares, name="Pares",
        marker_color="#3b82f6",
    ))
    fig.add_trace(go.Bar(
        x=concursos, y=impares, name="Ímpares",
        marker_color="#ef4444",
    ))
    fig.update_layout(
        title=f"Pares vs Ímpares (últimos 20) — {lot.emoji} {lot.nome}",
        barmode="stack",
        xaxis_title="Concurso",
        yaxis_title="Dezenas",
        template="plotly_dark",
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig
