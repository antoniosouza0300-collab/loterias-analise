"""Aba de Analytics avançados com gráficos Plotly, score e tendências."""

import gradio as gr
import plotly.graph_objects as go

from src.config import TODAS_LOTERIAS, LoteriaConfig
from src.logger import log


def _loteria_choices() -> list[str]:
    return [f"{l.emoji} {l.nome}" for l in TODAS_LOTERIAS]


def _parse_loteria(nome: str) -> LoteriaConfig:
    for l in TODAS_LOTERIAS:
        if l.nome in nome:
            return l
    return TODAS_LOTERIAS[0]


def _atualizar_analytics(nome_loteria: str):
    """Carrega todos os analytics de uma loteria (lazy)."""
    from src.dashboard import (
        obter_grafico_frequencia,
        obter_grafico_atraso,
        obter_grafico_soma,
        obter_grafico_pares,
        obter_tendencias,
        atualizar_loteria,
    )

    lot = _parse_loteria(nome_loteria)
    log.info("Analytics: carregando %s", lot.nome)

    try:
        status = atualizar_loteria(lot)
    except Exception as exc:
        status = f"⚠️ {exc}"

    try:
        fig_freq = obter_grafico_frequencia(lot)
    except Exception:
        fig_freq = go.Figure().update_layout(title="Erro ao carregar")

    try:
        fig_atraso = obter_grafico_atraso(lot)
    except Exception:
        fig_atraso = go.Figure().update_layout(title="Erro ao carregar")

    try:
        fig_soma = obter_grafico_soma(lot)
    except Exception:
        fig_soma = go.Figure().update_layout(title="Erro ao carregar")

    try:
        fig_pares = obter_grafico_pares(lot)
    except Exception:
        fig_pares = go.Figure().update_layout(title="Erro ao carregar")

    try:
        tendencias = obter_tendencias(lot)
    except Exception:
        tendencias = "Erro ao carregar tendências."

    return status, fig_freq, fig_atraso, fig_soma, fig_pares, tendencias


def _avaliar_jogo_score(nome_loteria: str, dezenas_texto: str) -> str:
    """Avalia um jogo e retorna o score."""
    from src.dashboard import obter_score_jogo

    lot = _parse_loteria(nome_loteria)

    try:
        dezenas = [int(d.strip()) for d in dezenas_texto.replace(",", " ").split() if d.strip()]
    except ValueError:
        return "❌ Digite apenas números separados por espaço ou vírgula."

    if len(dezenas) != lot.total_dezenas:
        return f"❌ {lot.nome} precisa de {lot.total_dezenas} dezenas (você digitou {len(dezenas)})."

    return obter_score_jogo(lot, dezenas)


def criar_aba_analytics():
    """Cria a aba de Analytics no dashboard."""
    choices = _loteria_choices()

    with gr.Row():
        sel_loteria = gr.Dropdown(
            choices=choices,
            value=choices[0],
            label="Loteria",
            scale=2,
        )
        btn_carregar = gr.Button("🔄 Carregar Analytics", variant="primary", scale=1)

    status_box = gr.Textbox(label="Status", interactive=False)

    with gr.Row():
        graf_freq = gr.Plot(label="Frequência das Dezenas")
        graf_atraso = gr.Plot(label="Dezenas Mais Atrasadas")

    with gr.Row():
        graf_soma = gr.Plot(label="Soma por Concurso")
        graf_pares = gr.Plot(label="Pares vs Ímpares")

    tendencias_box = gr.Textbox(
        label="📈 Tendências Temporais",
        lines=8,
        interactive=False,
    )

    gr.Markdown("---")
    gr.Markdown("### 🎯 Avaliador de Jogo (Score 0–100)")

    with gr.Row():
        sel_loteria_score = gr.Dropdown(
            choices=choices,
            value=choices[0],
            label="Loteria",
            scale=2,
        )
        input_dezenas = gr.Textbox(
            label="Suas dezenas (separadas por espaço)",
            placeholder="3 15 37 52 74",
            scale=3,
        )
        btn_score = gr.Button("📊 Avaliar", variant="secondary", scale=1)

    score_output = gr.Textbox(label="Resultado", lines=4, interactive=False)

    # Eventos
    btn_carregar.click(
        fn=_atualizar_analytics,
        inputs=[sel_loteria],
        outputs=[status_box, graf_freq, graf_atraso, graf_soma, graf_pares, tendencias_box],
    )

    btn_score.click(
        fn=_avaliar_jogo_score,
        inputs=[sel_loteria_score, input_dezenas],
        outputs=[score_output],
    )
