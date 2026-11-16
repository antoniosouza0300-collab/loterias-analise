"""Interface Gradio principal — Lotofácil + Dia de Sorte."""

from collections import Counter
import csv
import random
import re
import tempfile
import time
from typing import Any, Dict, List
import gradio as gr
from src.atualizador import atualizar_historico, ler_historico
from src.regras import avaliar_regras, calcular_metricas
from src.analise import gerar_html_analise
from src.interface_dia import criar_aba_dia
from src.interface_mega import criar_aba_mega
from src.interface_quina import criar_aba_quina
from src.interface_analytics import criar_aba_analytics
from src.interface_lotomania import criar_aba_lotomania

# ── Cache TTL (Lotofácil) ─────────────────────────────────────────────
_cache: Dict[str, Any] = {"historico": None, "ts": 0.0}
CACHE_TTL = 5


def _ler() -> List[Dict[str, Any]]:
    now = time.time()
    if _cache["historico"] is None or (now - _cache["ts"]) > CACHE_TTL:
        _cache["historico"] = ler_historico()
        _cache["ts"] = now
    return _cache["historico"]


def _invalidar():
    _cache["historico"] = None
    _cache["ts"] = 0.0


# ── Temperatura (Lotofácil) ───────────────────────────────────────────
def analisar_temperatura(historico, ultimos_n=20):
    if not historico:
        return {"quentes": [], "mornas": [], "frias": list(range(1, 26)),
                "frequencias": {d: 0 for d in range(1, 26)}, "analisados": 0}
    n = max(1, min(int(ultimos_n), len(historico)))
    ctr = Counter()
    for reg in historico[-n:]:
        for i in range(1, 16):
            b = reg.get(f"bola{i}")
            if b is not None:
                ctr[int(b)] += 1
    freqs = {d: ctr.get(d, 0) for d in range(1, 26)}
    ordenadas = sorted(freqs, key=lambda d: (-freqs[d], d))
    return {"quentes": sorted(ordenadas[:8]), "mornas": sorted(ordenadas[8:17]),
            "frias": sorted(ordenadas[17:]), "frequencias": freqs, "analisados": n}


def _badges(dezenas, freqs, bg, borda):
    if not dezenas:
        return "<em>Sem dados.</em>"
    return "".join(
        f"<span style='display:inline-block;margin:4px;padding:8px 12px;border-radius:10px;"
        f"background:{bg};border:1px solid {borda};font-weight:700;font-size:15px;'>"
        f"{d:02d} <small style='opacity:0.85;'>({freqs.get(d,0)}x)</small></span>"
        for d in dezenas
    )


def painel_temperatura(ultimos_n=20):
    h = _ler()
    if not h:
        return "<div style='padding:14px;border-radius:10px;background:#fff3cd;color:#856404;'>Sem dados. Atualize primeiro.</div>"
    r = analisar_temperatura(h, ultimos_n)
    f = r["frequencias"]
    return f"""<div style="font-family:sans-serif;display:flex;flex-direction:column;gap:14px;">
      <div style="font-size:14px;opacity:0.85;">Últimos <b>{r['analisados']}</b> de <b>{len(h)}</b> concursos.</div>
      <div style="padding:14px;border-radius:12px;border:1px solid #fca5a5;background:rgba(239,68,68,0.06);">
        <div style="font-weight:700;font-size:16px;margin-bottom:8px;color:#b91c1c;">🔥 Quentes</div>
        <div>{_badges(r['quentes'],f,'#fee2e2','#ef4444')}</div></div>
      <div style="padding:14px;border-radius:12px;border:1px solid #fcd34d;background:rgba(245,158,11,0.06);">
        <div style="font-weight:700;font-size:16px;margin-bottom:8px;color:#b45309;">☀️ Mornas</div>
        <div>{_badges(r['mornas'],f,'#fef3c7','#f59e0b')}</div></div>
      <div style="padding:14px;border-radius:12px;border:1px solid #93c5fd;background:rgba(59,130,246,0.06);">
        <div style="font-weight:700;font-size:16px;margin-bottom:8px;color:#1d4ed8;">❄️ Frias</div>
        <div>{_badges(r['frias'],f,'#dbeafe','#3b82f6')}</div></div>
    </div>"""


# ── Gerador com filtro de 15 regras (Lotofácil) ──────────────────────
def _badge(ok, label, det=""):
    c = "#10b981" if ok else "#ef4444"
    t = "✅" if ok else "❌"
    return f"<div>{label} ({det}): <span style='padding:2px 5px;border-radius:4px;background:{c};color:white;font-weight:600;'>{t}</span></div>"


def gerar_jogos(qq, qm, qf, qtd, janela):
    h = _ler()
    if not h:
        return "❌ Histórico vazio.", None
    if qq + qm + qf != 15:
        return f"❌ Soma deve ser 15 (atual: {qq+qm+qf}).", None

    r = analisar_temperatura(h, janela)
    qu, mo, fr = r["quentes"], r["mornas"], r["frias"]
    if qq > len(qu) or qm > len(mo) or qf > len(fr):
        return "❌ Quantidade excede grupos.", None

    jogos = []
    for _ in range(qtd):
        melhor, best = [], -1
        for _ in range(8000):
            sel = sorted(
                (random.sample(qu, qq) if qq else [])
                + (random.sample(mo, qm) if qm else [])
                + (random.sample(fr, qf) if qf else [])
            )
            if len(sel) != 15 or len(set(sel)) != 15:
                continue
            sc = sum(avaliar_regras(sel).values())
            if sc == 15:
                melhor = sel
                break
            if sc > best:
                best, melhor = sc, sel
        if melhor:
            jogos.append(melhor)

    if not jogos:
        return "⚠️ Não foi possível gerar jogos.", None

    html = []
    for idx, j in enumerate(jogos, 1):
        m = calcular_metricas(j)
        rv = avaliar_regras(j)
        sc = sum(rv.values())
        cor = "#10b981" if sc == 15 else ("#f59e0b" if sc >= 12 else "#ef4444")
        dz = " ".join(f"<span style='display:inline-block;padding:5px 8px;margin:2px;background:#0ea5e9;color:white;border-radius:6px;font-weight:bold;font-size:13px;'>{d:02d}</span>" for d in j)
        html.append(f"""<div style='margin-bottom:14px;padding:12px;border-radius:10px;background:#fff;border:1px solid #cbd5e1;box-shadow:0 1px 3px rgba(0,0,0,0.05);'>
          <div style='font-size:15px;font-weight:700;color:#1e293b;margin-bottom:8px;'>Jogo {idx:02d}
            <span style='float:right;padding:3px 8px;border-radius:6px;background:{cor};color:white;font-size:12px;'>{sc}/15</span></div>
          <div style='margin-bottom:10px;'>{dz}</div>
          <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:6px;font-size:11px;border-top:1px solid #e2e8f0;padding-top:8px;'>
            {_badge(rv['soma'],"Soma",str(m['soma']))}{_badge(rv['moldura'],"Moldura",str(m['moldura']))}
            {_badge(rv['pares'],"Pares",str(m['pares']))}{_badge(rv['primos'],"Primos",str(m['primos']))}
            {_badge(rv['multiplos_de_3'],"Mult.3",str(m['multiplos_de_3']))}{_badge(rv['gemeos'],"Gêmeos",str(m['gemeos']))}
            {_badge(rv['linhas'],"Linhas",f"Max{max(m['linhas'])}/Min{min(m['linhas'])}")}
            {_badge(rv['paridade_linhas_1_e_2'],"Par.L",str(m['pares_linhas_1_e_2']))}
            {_badge(rv['quadrantes'],"Quad",f"Max{max(m['quadrantes'])}/Min{min(m['quadrantes'])}")}
            {_badge(rv['miolo'],"Miolo",str(m['miolo']))}{_badge(rv['finais'],"Finais",f"Max{m['maior_frequencia_final']}")}
            {_badge(rv['colunas'],"Col",f"Max{max(m['colunas'])}/Min{min(m['colunas'])}")}
            {_badge(rv['diagonais'],"Diag",f"P:{m['diagonal_principal']}/S:{m['diagonal_secundaria']}")}
            {_badge(rv['fibonacci'],"Fib",str(m['fibonacci']))}
            {_badge(rv['inicio_fim'],"Ini/Fim",f"{m['menor_dezena']:02d}/{m['maior_dezena']:02d}")}
          </div></div>""")

    html_out = f"""<div style="font-family:sans-serif;">
      <div style="margin-bottom:14px;font-weight:600;color:#334155;">🎲 {len(jogos)} jogos ({qq}Q {qm}M {qf}F):</div>
      {"".join(html)}</div>"""

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    w = csv.writer(tmp)
    _cols = [f"bola{i}" for i in range(1, 16)]
    w.writerow(["jogo", *_cols, "score"])
    for idx, j in enumerate(jogos, 1):
        w.writerow([idx, *j, sum(avaliar_regras(j).values())])
    tmp.close()

    return html_out, tmp.name


# ── Validador por dezenas (Lotofácil) ─────────────────────────────────
def validar_por_dezenas(texto):
    if not texto or not texto.strip():
        return "<em>Digite 15 dezenas.</em>"
    nums = re.findall(r"\d+", texto)
    if len(nums) != 15:
        return f"❌ Precisam ser 15 dezenas (encontradas: {len(nums)})."
    jogo = sorted(int(n) for n in nums)
    if any(d < 1 or d > 25 for d in jogo):
        return "❌ Dezenas entre 1 e 25."
    if len(set(jogo)) != 15:
        return "❌ Dezenas repetidas."
    m = calcular_metricas(jogo)
    rv = avaliar_regras(jogo)
    sc = sum(rv.values())
    cor = "#10b981" if sc == 15 else ("#f59e0b" if sc >= 12 else "#ef4444")
    dz = " ".join(f"<span style='display:inline-block;padding:5px 8px;margin:2px;background:#0ea5e9;color:white;border-radius:6px;font-weight:bold;font-size:14px;'>{d:02d}</span>" for d in jogo)
    return f"""<div style="font-family:sans-serif;padding:12px;border-radius:10px;background:#fff;border:1px solid #cbd5e1;">
      <div style="font-size:16px;font-weight:700;margin-bottom:8px;">
        <span style="padding:4px 10px;border-radius:6px;background:{cor};color:white;">{sc}/15 regras</span></div>
      <div style="margin-bottom:10px;">{dz}</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:6px;font-size:12px;">
        {_badge(rv['soma'],"Soma",str(m['soma']))}{_badge(rv['moldura'],"Moldura",str(m['moldura']))}
        {_badge(rv['pares'],"Pares",str(m['pares']))}{_badge(rv['primos'],"Primos",str(m['primos']))}
        {_badge(rv['multiplos_de_3'],"Mult.3",str(m['multiplos_de_3']))}{_badge(rv['gemeos'],"Gêmeos",str(m['gemeos']))}
        {_badge(rv['linhas'],"Linhas",f"Max{max(m['linhas'])}/Min{min(m['linhas'])}")}
        {_badge(rv['paridade_linhas_1_e_2'],"Par.L",str(m['pares_linhas_1_e_2']))}
        {_badge(rv['quadrantes'],"Quad",f"Max{max(m['quadrantes'])}/Min{min(m['quadrantes'])}")}
        {_badge(rv['miolo'],"Miolo",str(m['miolo']))}{_badge(rv['finais'],"Finais",f"Max{m['maior_frequencia_final']}")}
        {_badge(rv['colunas'],"Col",f"Max{max(m['colunas'])}/Min{min(m['colunas'])}")}
        {_badge(rv['diagonais'],"Diag",f"P:{m['diagonal_principal']}/S:{m['diagonal_secundaria']}")}
        {_badge(rv['fibonacci'],"Fib",str(m['fibonacci']))}
        {_badge(rv['inicio_fim'],"Ini/Fim",f"{m['menor_dezena']:02d}/{m['maior_dezena']:02d}")}
      </div></div>"""


# ── Validadores individuais (Lotofácil) ───────────────────────────────
def _v(val, lo, hi, lbl):
    if val is None or val == "":
        return ""
    try:
        v = float(val)
    except (ValueError, TypeError):
        return "❌ Inválido"
    return f"✅ DENTRO ({lbl})" if lo <= v <= hi else f"❌ FORA ({lbl})"

def validar_soma_jogo(v): return _v(v, 166, 224, "166–224")
def validar_moldura_jogo(v): return _v(v, 9, 11, "9–11")
def validar_pares_jogo(v): return _v(v, 6, 9, "6–9")
def validar_primos_jogo(v): return _v(v, 4, 7, "4–7")
def validar_mult3_jogo(v): return _v(v, 4, 6, "4–6")
def validar_gemeos_jogo(v):
    if v is None or v == "": return ""
    try: val = int(v)
    except: return "❌ Inválido"
    return "✅ DENTRO (≤1)" if val <= 1 else "❌ FORA (>1)"
def validar_miolo_jogo(v): return _v(v, 3, 6, "3–6")
def validar_finais_jogo(v):
    if v is None or v == "": return ""
    try: val = int(v)
    except: return "❌ Inválido"
    return "✅ DENTRO (≤4)" if val <= 4 else "❌ FORA (>4)"
def validar_fibonacci_jogo(v): return _v(v, 3, 5, "3–5")
def validar_paridade_linhas_excel(a, b):
    if a is None or b is None or a == "" or b == "": return ""
    try: p1, p2 = int(a), int(b)
    except: return "❌ Inválido"
    return "❌ FORA" if (p1 == 5 or p2 == 5) else "✅ DENTRO"
def validar_quadrantes_jogo(mx, mn):
    if mx is None or mn is None or mx == "" or mn == "": return ""
    try: a, b = int(mx), int(mn)
    except: return "❌ Inválido"
    return "✅ DENTRO" if (a <= 6 and b >= 2) else "❌ FORA"
def validar_colunas_jogo(mx, mn):
    if mx is None or mn is None or mx == "" or mn == "": return ""
    try: a, b = int(mx), int(mn)
    except: return "❌ Inválido"
    return "✅ DENTRO" if (a <= 4 and b >= 1) else "❌ FORA"
def validar_diagonais_jogo(dp, ds):
    if dp is None or ds is None or dp == "" or ds == "": return ""
    try: a, b = int(dp), int(ds)
    except: return "❌ Inválido"
    return "✅ DENTRO" if (2 <= a <= 4 and 2 <= b <= 4) else "❌ FORA"
def validar_inicio_fim_jogo(ini, fim):
    if ini is None or fim is None or ini == "" or fim == "": return ""
    try: a, b = int(ini), int(fim)
    except: return "❌ Inválido"
    return "✅ DENTRO" if (a <= 4 and b >= 22) else "❌ FORA"


# ── Callbacks (Lotofácil) ─────────────────────────────────────────────
def executar_atualizacao(ultimos_n):
    try:
        _invalidar()
        r = atualizar_historico()
        msg = f"✅ {r['status']} | {r['primeiro_concurso']}–{r['ultimo_concurso']} (Total: {r['total_concursos']}, Novos: {r['novos_concursos']})"
    except Exception as e:
        msg = f"❌ Erro: {e}"
    return msg, painel_temperatura(ultimos_n)


# ── Sub-aba Lotofácil ─────────────────────────────────────────────────
def criar_aba_lotofacil():
    """Monta os componentes da Lotofácil dentro de uma TabItem existente."""
    gr.Markdown("Análise, geração inteligente e validação das **15 regras estatísticas** (15 de 25).")

    with gr.Tabs():
        with gr.TabItem("📊 Termômetro"):
            with gr.Row():
                sl_n = gr.Slider(5, 100, 20, 1, label="Concursos recentes")
                btn_upd = gr.Button("🔄 Atualizar", variant="primary")
            status = gr.Textbox(label="Status", value="Pronto.", interactive=False)
            painel = gr.HTML(value=painel_temperatura(20))
            sl_n.change(fn=painel_temperatura, inputs=[sl_n], outputs=[painel])
            btn_upd.click(fn=executar_atualizacao, inputs=[sl_n], outputs=[status, painel])

        with gr.TabItem("🎲 Gerador"):
            gr.Markdown("Soma dos 3 grupos = **15**. Jogos filtrados pelas 15 regras.")
            with gr.Row():
                sq = gr.Slider(0, 8, 6, 1, label="Quentes")
                sm = gr.Slider(0, 9, 5, 1, label="Mornas")
                sf = gr.Slider(0, 8, 4, 1, label="Frias")
            with gr.Row():
                sqtd = gr.Slider(1, 20, 5, 1, label="Jogos")
                sjanela = gr.Slider(5, 100, 20, 1, label="Janela")
            btn_gerar = gr.Button("🚀 Gerar Jogos", variant="primary")
            out_html = gr.HTML(value="<em>Clique em Gerar.</em>")
            out_file = gr.File(label="📥 Baixar CSV", visible=True)
            btn_gerar.click(fn=gerar_jogos, inputs=[sq, sm, sf, sqtd, sjanela], outputs=[out_html, out_file])

        with gr.TabItem("📈 Análise Avançada"):
            gr.Markdown("### Atraso, frequência ponderada e score de dezenas")
            sl_analise = gr.Slider(10, 100, 50, 5, label="Janela de análise")
            btn_analise = gr.Button("📊 Calcular Análise", variant="primary")
            out_analise = gr.HTML()
            btn_analise.click(fn=lambda n: gerar_html_analise(_ler(), n), inputs=[sl_analise], outputs=[out_analise])

        with gr.TabItem("🔍 Validador"):
            gr.Markdown("### ⚡ Validação Rápida — Cole 15 dezenas")
            inp_dz = gr.Textbox(label="Dezenas", placeholder="01 03 05 07 09 11 13 15 17 19 21 23 24 25 02")
            btn_vdz = gr.Button("🔍 Validar", variant="primary")
            out_dz = gr.HTML()
            btn_vdz.click(fn=validar_por_dezenas, inputs=[inp_dz], outputs=[out_dz])

            gr.Markdown("---")
            gr.Markdown("### 🔧 Validador Manual")
            with gr.Row():
                i_soma = gr.Number(label="Soma", value=195, step=1)
                i_mold = gr.Number(label="Moldura", value=10, step=1)
                i_par = gr.Number(label="Pares", value=7, step=1)
                i_prim = gr.Number(label="Primos", value=5, step=1)
            with gr.Row():
                i_m3 = gr.Number(label="Mult.3", value=5, step=1)
                i_gem = gr.Number(label="Gêmeos", value=0, step=1)
                i_l1 = gr.Number(label="Par.L1", value=1, step=1)
                i_l2 = gr.Number(label="Par.L2", value=1, step=1)
            with gr.Row():
                i_mxq = gr.Number(label="MaxQuad", value=4, step=1)
                i_mnq = gr.Number(label="MinQuad", value=3, step=1)
                i_mio = gr.Number(label="Miolo", value=4, step=1)
                i_fin = gr.Number(label="MaxFin", value=3, step=1)
            with gr.Row():
                i_mxc = gr.Number(label="MaxCol", value=3, step=1)
                i_mnc = gr.Number(label="MinCol", value=2, step=1)
                i_dp = gr.Number(label="Diag.P", value=3, step=1)
                i_ds = gr.Number(label="Diag.S", value=3, step=1)
            with gr.Row():
                i_fib = gr.Number(label="Fib", value=4, step=1)
                i_ini = gr.Number(label="Menor", value=2, step=1)
                i_fim = gr.Number(label="Maior", value=24, step=1)

            btn_val = gr.Button("Validar Todos", variant="primary")
            with gr.Row():
                o_soma = gr.Textbox(label="Soma", interactive=False)
                o_mold = gr.Textbox(label="Moldura", interactive=False)
                o_par = gr.Textbox(label="Pares", interactive=False)
                o_prim = gr.Textbox(label="Primos", interactive=False)
            with gr.Row():
                o_m3 = gr.Textbox(label="Mult.3", interactive=False)
                o_gem = gr.Textbox(label="Gêmeos", interactive=False)
                o_lpar = gr.Textbox(label="Par.L", interactive=False)
                o_quad = gr.Textbox(label="Quad", interactive=False)
            with gr.Row():
                o_mio = gr.Textbox(label="Miolo", interactive=False)
                o_fin = gr.Textbox(label="Finais", interactive=False)
                o_col = gr.Textbox(label="Colunas", interactive=False)
                o_diag = gr.Textbox(label="Diag", interactive=False)
            with gr.Row():
                o_fib = gr.Textbox(label="Fib", interactive=False)
                o_if = gr.Textbox(label="Ini/Fim", interactive=False)

            all_in = [i_soma,i_mold,i_par,i_prim,i_m3,i_gem,i_l1,i_l2,i_mxq,i_mnq,i_mio,i_fin,i_mxc,i_mnc,i_dp,i_ds,i_fib,i_ini,i_fim]
            all_out = [o_soma,o_mold,o_par,o_prim,o_m3,o_gem,o_lpar,o_quad,o_mio,o_fin,o_col,o_diag,o_fib,o_if]

            btn_val.click(
                fn=lambda s,mo,p,pr,m3,g,l1,l2,mxq,mnq,mio,fin,mxc,mnc,dp,ds,fib,ini,fn: (
                    validar_soma_jogo(s), validar_moldura_jogo(mo), validar_pares_jogo(p),
                    validar_primos_jogo(pr), validar_mult3_jogo(m3), validar_gemeos_jogo(g),
                    validar_paridade_linhas_excel(l1,l2), validar_quadrantes_jogo(mxq,mnq),
                    validar_miolo_jogo(mio), validar_finais_jogo(fin),
                    validar_colunas_jogo(mxc,mnc), validar_diagonais_jogo(dp,ds),
                    validar_fibonacci_jogo(fib), validar_inicio_fim_jogo(ini,fn)),
                inputs=all_in, outputs=all_out)

            i_soma.change(fn=validar_soma_jogo, inputs=[i_soma], outputs=[o_soma])
            i_mold.change(fn=validar_moldura_jogo, inputs=[i_mold], outputs=[o_mold])
            i_par.change(fn=validar_pares_jogo, inputs=[i_par], outputs=[o_par])
            i_prim.change(fn=validar_primos_jogo, inputs=[i_prim], outputs=[o_prim])
            i_m3.change(fn=validar_mult3_jogo, inputs=[i_m3], outputs=[o_m3])
            i_gem.change(fn=validar_gemeos_jogo, inputs=[i_gem], outputs=[o_gem])
            i_mio.change(fn=validar_miolo_jogo, inputs=[i_mio], outputs=[o_mio])
            i_fin.change(fn=validar_finais_jogo, inputs=[i_fin], outputs=[o_fin])
            i_fib.change(fn=validar_fibonacci_jogo, inputs=[i_fib], outputs=[o_fib])
            i_mxc.change(fn=validar_colunas_jogo, inputs=[i_mxc, i_mnc], outputs=[o_col])
            i_mnc.change(fn=validar_colunas_jogo, inputs=[i_mxc, i_mnc], outputs=[o_col])
            i_dp.change(fn=validar_diagonais_jogo, inputs=[i_dp, i_ds], outputs=[o_diag])
            i_ds.change(fn=validar_diagonais_jogo, inputs=[i_dp, i_ds], outputs=[o_diag])
            i_ini.change(fn=validar_inicio_fim_jogo, inputs=[i_ini, i_fim], outputs=[o_if])
            i_fim.change(fn=validar_inicio_fim_jogo, inputs=[i_ini, i_fim], outputs=[o_if])
            i_l1.change(fn=validar_paridade_linhas_excel, inputs=[i_l1, i_l2], outputs=[o_lpar])
            i_l2.change(fn=validar_paridade_linhas_excel, inputs=[i_l1, i_l2], outputs=[o_lpar])
            i_mxq.change(fn=validar_quadrantes_jogo, inputs=[i_mxq, i_mnq], outputs=[o_quad])
            i_mnq.change(fn=validar_quadrantes_jogo, inputs=[i_mxq, i_mnq], outputs=[o_quad])


# ── Interface Principal ───────────────────────────────────────────────
def criar_interface():
    with gr.Blocks(title="Loterias — Dashboard Completo") as demo:
        gr.Markdown("# 🍀 Dashboard de Loterias")
        gr.Markdown("Escolha a loteria abaixo. Cada uma com Termômetro, Gerador, Análise e Validador.")

        with gr.Tabs():
            with gr.TabItem("🍀 Lotofácil (15 de 25)"):
                criar_aba_lotofacil()

            with gr.TabItem("🍀 Dia de Sorte (7 de 31)"):
                criar_aba_dia()

            with gr.TabItem("🍀 Mega-Sena (6 de 60)"):
                criar_aba_mega()

            with gr.TabItem("🎯 Quina (5 de 80)"):
                criar_aba_quina()

            with gr.TabItem("🎲 Lotomania (20 de 100)"):
                criar_aba_lotomania()

            with gr.TabItem("📊 Analytics"):
                criar_aba_analytics()

    return demo


if __name__ == "__main__":
    app = criar_interface()
    app.launch(share=True)
