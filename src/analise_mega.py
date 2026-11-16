"""Análise avançada de atraso, frequência ponderada e score — Mega-Sena."""

from __future__ import annotations
from typing import Any, Dict, List


def calcular_atrasos(
    historico: List[Dict[str, Any]],
    ultimos_n: int = 100,
) -> Dict[int, int]:
    """Retorna quantos concursos cada dezena (1-60) está sem sair."""
    if not historico:
        return {d: 0 for d in range(1, 61)}

    recentes = historico[-ultimos_n:]
    atraso = {d: len(recentes) for d in range(1, 61)}

    for idx, reg in enumerate(recentes):
        dist = len(recentes) - 1 - idx
        for i in range(1, 7):
            bola = reg.get(f"bola{i}")
            if bola is not None:
                d = int(bola)
                if dist < atraso[d]:
                    atraso[d] = dist

    return atraso


def calcular_frequencia_ponderada(
    historico: List[Dict[str, Any]],
    ultimos_n: int = 50,
    decay: float = 0.95,
) -> Dict[int, float]:
    """Frequência com peso exponencial — concursos recentes valem mais."""
    if not historico:
        return {d: 0.0 for d in range(1, 61)}

    recentes = historico[-ultimos_n:]
    freq = {d: 0.0 for d in range(1, 61)}

    for idx, reg in enumerate(recentes):
        peso = decay ** (len(recentes) - 1 - idx)
        for i in range(1, 7):
            bola = reg.get(f"bola{i}")
            if bola is not None:
                freq[int(bola)] += peso

    return freq


def calcular_atraso_medio(
    historico: List[Dict[str, Any]],
    ultimos_n: int = 100,
) -> Dict[int, float]:
    """Atraso médio histórico de cada dezena."""
    if not historico or len(historico) < 2:
        return {d: 0.0 for d in range(1, 61)}

    recentes = historico[-ultimos_n:]
    gaps: Dict[int, List[int]] = {d: [] for d in range(1, 61)}
    ultima_pos = {d: -1 for d in range(1, 61)}

    for idx, reg in enumerate(recentes):
        for i in range(1, 7):
            bola = reg.get(f"bola{i}")
            if bola is not None:
                d = int(bola)
                if ultima_pos[d] >= 0:
                    gaps[d].append(idx - ultima_pos[d])
                ultima_pos[d] = idx

    return {
        d: (sum(gaps[d]) / len(gaps[d]) if gaps[d] else 0.0)
        for d in range(1, 61)
    }


def calcular_score_devido(
    historico: List[Dict[str, Any]],
    ultimos_n: int = 50,
) -> List[Dict[str, Any]]:
    """Score combinado: atraso alto + frequência alta = dezena 'devida'."""
    atrasos = calcular_atrasos(historico, ultimos_n)
    freq_pond = calcular_frequencia_ponderada(historico, ultimos_n)
    atraso_med = calcular_atraso_medio(historico, ultimos_n)

    max_freq = max(freq_pond.values()) or 1.0
    resultados = []

    for d in range(1, 61):
        atraso = atrasos[d]
        avg = atraso_med[d] or 1.0
        freq_norm = freq_pond[d] / max_freq
        ratio = atraso / avg if avg > 0 else 0.0
        score = (ratio * 0.6 + freq_norm * 0.4) * 100

        if ratio >= 1.5:
            status = "🔴 MUITO ATRASADA"
        elif ratio >= 1.0:
            status = "🟡 ATRASADA"
        elif ratio >= 0.7:
            status = "🟢 NORMAL"
        else:
            status = "🔵 RECENTE"

        resultados.append({
            "dezena": d,
            "atraso": atraso,
            "atraso_medio": round(avg, 1),
            "ratio": round(ratio, 2),
            "freq_ponderada": round(freq_pond[d], 2),
            "score": round(score, 1),
            "status": status,
        })

    resultados.sort(key=lambda x: -x["score"])
    return resultados


def gerar_html_analise(
    historico: List[Dict[str, Any]],
    ultimos_n: int = 50,
) -> str:
    """Gera HTML completo com tabela de análise para o Gradio."""
    if not historico:
        return (
            "<div style='padding:14px;border-radius:10px;background:#fff3cd;color:#856404;'>"
            "Sem dados. Atualize o histórico primeiro.</div>"
        )

    scores = calcular_score_devido(historico, ultimos_n)

    linhas = []
    for s in scores:
        cor_bg = (
            "#fee2e2" if "MUITO" in s["status"]
            else "#fef3c7" if "ATRASADA" in s["status"]
            else "#dcfce7" if "NORMAL" in s["status"]
            else "#dbeafe"
        )
        linhas.append(
            f"<tr style='background:{cor_bg};'>"
            f"<td style='font-weight:700;font-size:16px;text-align:center;'>{s['dezena']:02d}</td>"
            f"<td style='text-align:center;'>{s['atraso']}</td>"
            f"<td style='text-align:center;'>{s['atraso_medio']}</td>"
            f"<td style='text-align:center;'>{s['ratio']}</td>"
            f"<td style='text-align:center;'>{s['freq_ponderada']}</td>"
            f"<td style='text-align:center;font-weight:700;'>{s['score']}</td>"
            f"<td style='text-align:center;'>{s['status']}</td>"
            f"</tr>"
        )

    top5 = scores[:5]
    top5_html = " ".join(
        f"<span style='display:inline-block;padding:8px 14px;margin:4px;"
        f"border-radius:10px;background:#ef4444;color:white;font-weight:700;"
        f"font-size:16px;'>{s['dezena']:02d} "
        f"<small style='opacity:0.85;'>(score {s['score']})</small></span>"
        for s in top5
    )

    return f"""
    <div style="font-family:sans-serif;display:flex;flex-direction:column;gap:16px;">
      <div style="padding:14px;border-radius:12px;border:2px solid #ef4444;background:rgba(239,68,68,0.06);">
        <div style="font-weight:700;font-size:16px;color:#b91c1c;margin-bottom:8px;">
          🎯 Top 5 Dezenas Mais "Devidas"
        </div>
        <div>{top5_html}</div>
      </div>
      <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="background:#1e293b;color:white;">
              <th style="padding:8px;">Dezena</th>
              <th style="padding:8px;">Atraso</th>
              <th style="padding:8px;">Atraso Médio</th>
              <th style="padding:8px;">Ratio</th>
              <th style="padding:8px;">Freq. Pond.</th>
              <th style="padding:8px;">Score</th>
              <th style="padding:8px;">Status</th>
            </tr>
          </thead>
          <tbody>{"".join(linhas)}</tbody>
        </table>
      </div>
      <div style="font-size:12px;opacity:0.7;">
        <b>Ratio</b> = Atraso atual ÷ Atraso médio (>1.5 = muito atrasada).
        <b>Score</b> = 60% ratio + 40% frequência ponderada.
      </div>
    </div>
    """
