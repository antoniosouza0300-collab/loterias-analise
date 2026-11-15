cat << 'EOF' > src/interface.py
from collections import Counter
import random
from typing import Any, Dict, List
import gradio as gr
from src.atualizador import atualizar_historico, ler_historico


def analisar_temperatura_dezenas(
    historico: List[Dict[str, Any]], ultimos_n: int = 20
) -> Dict[str, Any]:
    """Classifica as dezenas de 1 a 25 em quentes, mornas e frias com base nos últimos N concursos."""
    if not historico:
        return {
            "quentes": [],
            "mornas": [],
            "frias": list(range(1, 26)),
            "frequencias": {d: 0 for d in range(1, 26)},
            "analisados": 0,
        }

    ultimos_n = max(1, min(int(ultimos_n), len(historico)))
    concursos_recentes = historico[-ultimos_n:]

    contador = Counter()
    for reg in concursos_recentes:
        for i in range(1, 16):
            bola = reg.get(f"bola{i}")
            if bola is not None:
                contador[int(bola)] += 1

    frequencias = {dez: contador.get(dez, 0) for dez in range(1, 26)}
    dezenas_ordenadas = sorted(
        frequencias.keys(), key=lambda d: (-frequencias[d], d)
    )

    return {
        "quentes": sorted(dezenas_ordenadas[:8]),
        "mornas": sorted(dezenas_ordenadas[8:17]),
        "frias": sorted(dezenas_ordenadas[17:]),
        "frequencias": frequencias,
        "analisados": len(concursos_recentes),
    }


def _renderizar_badges(dezenas: List[int], frequencias: Dict[int, int], cor_bg: str, cor_borda: str) -> str:
    if not dezenas:
        return "<em>Sem dados disponíveis.</em>"
    badges = []
    for d in dezenas:
        freq = frequencias.get(d, 0)
        badges.append(
            f"<span style='display:inline-block;margin:4px;padding:8px 12px;"
            f"border-radius:10px;background:{cor_bg};border:1px solid {cor_borda};"
            f"font-weight:700;font-size:15px;'>"
            f"{d:02d} <small style='font-weight:400;opacity:0.85;'>({freq}x)</small></span>"
        )
    return "".join(badges)


def atualizar_painel_temperatura(ultimos_n: int = 20) -> str:
    historico = ler_historico()
    if not historico:
        return (
            "<div style='padding:14px;border-radius:10px;background:#fff3cd;color:#856404;'>"
            "Nenhum concurso encontrado no histórico local. Clique em <b>Atualizar Histórico</b> primeiro."
            "</div>"
        )

    res = analisar_temperatura_dezenas(historico, ultimos_n=ultimos_n)
    freqs = res["frequencias"]
    total = len(historico)
    analisados = res["analisados"]

    html_quentes = _renderizar_badges(res["quentes"], freqs, "#fee2e2", "#ef4444")
    html_mornas = _renderizar_badges(res["mornas"], freqs, "#fef3c7", "#f59e0b")
    html_frias = _renderizar_badges(res["frias"], freqs, "#dbeafe", "#3b82f6")

    return f"""
    <div style="font-family:sans-serif;display:flex;flex-direction:column;gap:14px;">
      <div style="font-size:14px;opacity:0.85;">
        Analisando os últimos <b>{analisados}</b> concursos (de um total de <b>{total}</b> registrados).
      </div>
      <div style="padding:14px;border-radius:12px;border:1px solid #fca5a5;background:rgba(239,68,68,0.06);">
        <div style="font-weight:700;font-size:16px;margin-bottom:8px;color:#b91c1c;">
          🔥 Quentes — Top 8 mais sorteadas
        </div>
        <div>{html_quentes}</div>
      </div>
      <div style="padding:14px;border-radius:12px;border:1px solid #fcd34d;background:rgba(245,158,11,0.06);">
        <div style="font-weight:700;font-size:16px;margin-bottom:8px;color:#b45309;">
          ☀️ Mornas — 9 dezenas intermediárias
        </div>
        <div>{html_mornas}</div>
      </div>
      <div style="padding:14px;border-radius:12px;border:1px solid #93c5fd;background:rgba(59,130,246,0.06);">
        <div style="font-weight:700;font-size:16px;margin-bottom:8px;color:#1d4ed8;">
          ❄️ Frias — 8 dezenas menos sorteadas
        </div>
        <div>{html_frias}</div>
      </div>
    </div>
    """


def gerar_jogos_balanceados(qtd_quentes: int, qtd_mornas: int, qtd_frias: int, quantidade_jogos: int, ultimos_n: int) -> str:
    historico = ler_historico()
    if not historico:
        return "❌ Histórico vazio. Atualize a base de dados primeiro na aba anterior."

    soma_total = qtd_quentes + qtd_mornas + qtd_frias
    if soma_total != 15:
        return f"❌ A soma de dezenas por grupo deve ser exatamente 15 (atual: {soma_total}). Ajuste os seletores."

    res = analisar_temperatura_dezenas(historico, ultimos_n=ultimos_n)
    quentes = res["quentes"]
    mornas = res["mornas"]
    frias = res["frias"]

    if qtd_quentes > len(quentes) or qtd_mornas > len(mornas) or qtd_frias > len(frias):
        return "❌ Quantidade solicitada excede o tamanho dos grupos disponíveis."

    jogos_gerados = []
    for _ in range(quantidade_jogos):
        sel_quentes = random.sample(quentes, qtd_quentes) if qtd_quentes > 0 else []
        sel_mornas = random.sample(mornas, qtd_mornas) if qtd_mornas > 0 else []
        sel_frias = random.sample(frias, qtd_frias) if qtd_frias > 0 else []

        jogo = sorted(sel_quentes + sel_mornas + sel_frias)
        jogos_gerados.append(jogo)

    html_jogos = []
    for idx, jogo in enumerate(jogos_gerados, 1):
        soma_jogo = sum(jogo)
        status_soma = "✅ DENTRO" if 166 <= soma_jogo <= 224 else "❌ FORA"
        cor_badge = "#10b981" if status_soma == "✅ DENTRO" else "#ef4444"

        dezenas_str = " ".join(f"<span style='display:inline-block;padding:6px 10px;margin:2px;background:#0ea5e9;color:white;border-radius:6px;font-weight:bold;font-size:14px;'>{d:02d}</span>" for d in jogo)
        html_jogos.append(
            f"<div style='margin-bottom:10px;padding:12px;border-radius:8px;background:#f8fafc;border:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;'>"
            f"<div><b>Jogo {idx:02d}:</b> {dezenas_str}</div>"
            f"<div style='text-align:right;font-size:14px;'>Soma: <b>{soma_jogo}</b> <span style='padding:4px 8px;border-radius:6px;background:{cor_badge};color:white;font-size:12px;margin-left:6px;'>{status_soma}</span></div>"
            f"</div>"
        )

    return f"""
    <div style="font-family:sans-serif;">
      <div style="margin-bottom:12px;font-weight:600;color:#334155;">
        🎲 Gerados <b>{quantidade_jogos}</b> jogos equilibrados ({qtd_quentes} Quentes, {qtd_mornas} Mornas, {qtd_frias} Frias):
      </div>
      {"".join(html_jogos)}
    </div>
    """


def validar_soma_jogo(soma: Any) -> str:
    """Equivalente em Python da fórmula do Excel: =SE(G2="";"";SE(E(G2>=166;G2<=224);"✅ DENTRO";"❌ FORA (Padrão: 166 a 224)"))"""
    if soma is None or soma == "":
        return ""
    try:
        val = float(soma)
    except (ValueError, TypeError):
        return "❌ Valor inválido"
    
    if 166 <= val <= 224:
        return "✅ DENTRO (Padrão: 166 a 224)"
    else:
        return "❌ FORA (Padrão: 166 a 224)"


def executar_atualizacao(ultimos_n: int):
    try:
        res = atualizar_historico()
        status_msg = (
            f"✅ Status: {res['status']} | "
            f"Concursos: {res['primeiro_concurso']} a {res['ultimo_concurso']} "
            f"(Total: {res['total_concursos']}, Novos: {res['novos_concursos']})"
        )
    except Exception as exc:
        status_msg = f"❌ Erro ao atualizar histórico: {exc}"
    return status_msg, atualizar_painel_temperatura(ultimos_n)


def criar_interface() -> gr.Blocks:
    with gr.Blocks(title="Análise Lotofácil — Painel, Gerador e Validador") as demo:
        gr.Markdown("# 🍀 Dashboard Lotofácil: Análise, Gerador & Validador")
        gr.Markdown("Monitore a temperatura das dezenas, gere apostas inteligentes e valide somas baseadas na regra de 166 a 224.")

        with gr.Tabs():
            with gr.TabItem("📊 Termômetro de Dezenas"):
                with gr.Row():
                    slider_concursos = gr.Slider(
                        minimum=5,
                        maximum=100,
                        value=20,
                        step=1,
                        label="Quantidade de concursos recentes para análise",
                    )
                    btn_atualizar = gr.Button("🔄 Atualizar Histórico", variant="primary")

                status_box = gr.Textbox(
                    label="Status da Base de Dados",
                    value="Pronto para analisar.",
                    interactive=False,
                )

                painel_html = gr.HTML(value=atualizar_painel_temperatura(20))

                slider_concursos.change(
                    fn=atualizar_painel_temperatura,
                    inputs=[slider_concursos],
                    outputs=[painel_html],
                )

                btn_atualizar.click(
                    fn=executar_atualizacao,
                    inputs=[slider_concursos],
                    outputs=[status_box, painel_html],
                )

            with gr.TabItem("🎲 Gerador de Jogos Balanceados"):
                gr.Markdown("Defina quantos números de cada grupo deseja por aposta (a soma dos três controles deve ser **15**).")

                with gr.Row():
                    slider_q = gr.Slider(minimum=0, maximum=8, value=6, step=1, label="Qtd. Quentes (max 8)")
                    slider_m = gr.Slider(minimum=0, maximum=9, value=5, step=1, label="Qtd. Mornas (max 9)")
                    slider_f = gr.Slider(minimum=0, maximum=8, value=4, step=1, label="Qtd. Frias (max 8)")

                with gr.Row():
                    slider_qtd_jogos = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="Número de Jogos a Gerar")
                    slider_janela_gerador = gr.Slider(minimum=5, maximum=100, value=20, step=1, label="Janela de Concursos Base")

                btn_gerar = gr.Button("🚀 Gerar Jogos Balanceados", variant="primary")
                saida_jogos = gr.HTML(value="<em>Clique em 'Gerar Jogos Balanceados' para criar suas apostas.</em>")

                btn_gerar.click(
                    fn=gerar_jogos_balanceados,
                    inputs=[slider_q, slider_m, slider_f, slider_qtd_jogos, slider_janela_gerador],
                    outputs=[saida_jogos],
                )

            with gr.TabItem("🔍 Validador de Soma"):
                gr.Markdown("### Validador de Intervalo de Soma")
                gr.Markdown("Verifica se a soma das dezenas de um jogo está dentro da faixa padrão recomendada (**166 a 224**), replicando a lógica da sua fórmula do Excel.")

                with gr.Row():
                    input_soma = gr.Number(label="Digite a Soma das Dezenas", value=195, step=1)
                    btn_validar = gr.Button("Validar Soma", variant="primary")

                saida_validacao = gr.Textbox(label="Resultado da Validação", interactive=False)

                btn_validar.click(
                    fn=validar_soma_jogo,
                    inputs=[input_soma],
                    outputs=[saida_validacao],
                )
                
                input_soma.change(
                    fn=validar_soma_jogo,
                    inputs=[input_soma],
                    outputs=[saida_validacao],
                )

    return demo


if __name__ == "__main__":
    app = criar_interface()
    app.launch(share=True)
EOF
