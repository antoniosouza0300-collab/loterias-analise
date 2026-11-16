"""Aba Gradio da Lotomania (20 de 100)."""

import gradio as gr
import pandas as pd

from src.atualizador_lotomania import (
    atualizar_historico,
    ler_historico,
    COLUNAS,
)
from src.analise_lotomania import (
    frequencia_dezenas,
    atraso_dezenas,
    classificar_temperatura,
    analisar_concurso,
    gerar_jogo_aleatorio,
)
from src.regras_lotomania import (
    TOTAL_DEZENAS,
    DEZENA_MAXIMA,
    avaliar_regras,
)
from src.logger import log


def _atualizar():
    """Atualiza o histórico e retorna status."""
    try:
        resultado = atualizar_historico()
        status = resultado.get("status", "desconhecido")
        novos = resultado.get("novos", 0)
        total = resultado.get("total", 0)
        if status == "offline":
            return f"⚠️ API indisponível. Usando {total} concursos locais."
        if novos == 0:
            return f"✅ Lotomania já atualizado ({total} concursos)."
        return f"🚀 {novos} novos concursos! Total: {total}."
    except Exception as exc:
        log.error("Erro ao atualizar Lotomania: %s", exc)
        return f"❌ Erro: {exc}"


def _carregar_tabela():
    """Carrega histórico como DataFrame."""
    try:
        historico = ler_historico()
        if not historico:
            return pd.DataFrame(columns=COLUNAS)
        return pd.DataFrame(historico)[COLUNAS].tail(20)
    except Exception:
        return pd.DataFrame(columns=COLUNAS)


def _carregar_frequencia():
    """Carrega tabela de frequência."""
    try:
        historico = ler_historico()
        freq = frequencia_dezenas(historico)
        df = pd.DataFrame(
            sorted(freq.items()), columns=["Dezena", "Frequência"]
        )
        return df.sort_values("Frequência", ascending=False).head(30)
    except Exception:
        return pd.DataFrame(columns=["Dezena", "Frequência"])


def _carregar_atraso():
    """Carrega tabela de atraso."""
    try:
        historico = ler_historico()
        atr = atraso_dezenas(historico)
        df = pd.DataFrame(
            sorted(atr.items()), columns=["Dezena", "Atraso"]
        )
        return df.sort_values("Atraso", ascending=False).head(20)
    except Exception:
        return pd.DataFrame(columns=["Dezena", "Atraso"])


def _carregar_temperatura():
    """Carrega classificação de temperatura."""
    try:
        historico = ler_historico()
        freq = frequencia_dezenas(historico)
        temp = classificar_temperatura(freq)
        linhas = [
            f"🔥 Quentes ({len(temp['quentes'])}): {temp['quentes'][:20]}...",
            f"🟡 Mornas ({len(temp['mornas'])}): {temp['mornas'][:20]}...",
            f"🧊 Frias ({len(temp['frias'])}): {temp['frias'][:20]}...",
        ]
        return "\n".join(linhas)
    except Exception:
        return "Erro ao calcular temperatura."


def _analisar_ultimo():
    """Analisa o último concurso."""
    try:
        historico = ler_historico()
        if not historico:
            return "Sem dados."
        ultimo = historico[-1]
        analise = analisar_concurso(ultimo)
        if "erro" in analise:
            return analise["erro"]

        regras = analise["regras"]
        aprovadas = sum(regras.values())
        total = len(regras)
        falhas = [k for k, v in regras.items() if not v]

        linhas = [
            f"📋 Concurso {analise['concurso']} ({analise['data']})",
            f"🎱 Dezenas: {analise['dezenas']}",
            f"📊 Soma: {analise['metricas']['soma']}",
            f"⚖️ Pares: {analise['metricas']['pares']} | Ímpares: {TOTAL_DEZENAS - analise['metricas']['pares']}",
            f"🔢 Primos: {analise['metricas']['primos']} | Múlt.3: {analise['metricas']['multiplos_de_3']}",
            f"🖼️ Moldura: {analise['metricas']['moldura']} | Miolo: {analise['metricas']['miolo']}",
            f"📏 Amplitude: {analise['metricas']['amplitude']}",
            f"",
            f"✅ Regras: {aprovadas}/{total} (Score: {analise['score']}%)",
        ]
        if falhas:
            linhas.append(f"❌ Falhas: {', '.join(falhas)}")

        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro: {exc}"


def _gerar_jogo():
    """Gera um jogo aleatório."""
    try:
        historico = ler_historico()
        freq = frequencia_dezenas(historico)
        temp = classificar_temperatura(freq)
        jogo = gerar_jogo_aleatorio(
            quentes=8, mornas=7, frias=5, temperatura=temp
        )
        regras = avaliar_regras(jogo)
        score = round(sum(regras.values()) / len(regras) * 100)
        falhas = [k for k, v in regras.items() if not v]

        linhas = [
            f"🎰 Jogo gerado: {jogo}",
            f"📊 Score: {score}/100",
        ]
        if falhas:
            linhas.append(f"❌ Falhas: {', '.join(falhas)}")
        else:
            linhas.append("✅ Todas as regras aprovadas!")

        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro: {exc}"


def criar_aba_lotomania():
    """Cria a aba da Lotomania no dashboard."""
    gr.Markdown(
        '<span style="background:#e11d48;color:white;padding:4px 12px;'
        'border-radius:8px;font-weight:bold;">🎲 Lotomania (20 de 100)</span>'
    )

    with gr.Row():
        btn_atualizar = gr.Button("🔄 Atualizar", variant="primary")
        status = gr.Textbox(label="Status", interactive=False, scale=3)

    btn_atualizar.click(fn=_atualizar, outputs=[status])

    with gr.Tabs():
        with gr.TabItem("📋 Histórico"):
            tabela = gr.Dataframe(label="Últimos 20 concursos")
            btn_hist = gr.Button("Carregar")
            btn_hist.click(fn=_carregar_tabela, outputs=[tabela])

        with gr.TabItem("📊 Frequência"):
            freq_table = gr.Dataframe(label="Top 30 dezenas")
            btn_freq = gr.Button("Carregar")
            btn_freq.click(fn=_carregar_frequencia, outputs=[freq_table])

        with gr.TabItem("⏳ Atraso"):
            atr_table = gr.Dataframe(label="Top 20 atrasadas")
            btn_atr = gr.Button("Carregar")
            btn_atr.click(fn=_carregar_atraso, outputs=[atr_table])

        with gr.TabItem("🌡️ Temperatura"):
            temp_box = gr.Textbox(label="Classificação", lines=4, interactive=False)
            btn_temp = gr.Button("Carregar")
            btn_temp.click(fn=_carregar_temperatura, outputs=[temp_box])

        with gr.TabItem("🔍 Análise"):
            analise_box = gr.Textbox(label="Último concurso", lines=10, interactive=False)
            btn_analise = gr.Button("Analisar")
            btn_analise.click(fn=_analisar_ultimo, outputs=[analise_box])

        with gr.TabItem("🎰 Gerador"):
            gerador_box = gr.Textbox(label="Jogo gerado", lines=5, interactive=False)
            btn_gerar = gr.Button("Gerar Jogo", variant="secondary")
            btn_gerar.click(fn=_gerar_jogo, outputs=[gerador_box])
