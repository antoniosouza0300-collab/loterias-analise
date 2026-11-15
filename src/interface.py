import gradio as gr
from src.atualizador import ler_historico
# from src.analise import analisar_temperatura_dezenas

def exibir_analise_temperatura():
    historico = ler_historico()
    resultado = analisar_temperatura_dezenas(historico, ultimos_n=20)
    
    txt_quentes = ", ".join(f"{d:02d}" for d in resultado["quentes"])
    txt_mornas = ", ".join(f"{d:02d}" for d in resultado["mornas"])
    txt_frias = ", ".join(f"{d:02d}" for d in resultado["frias"])
    
    return f"🔥 **Quentes (Mais sorteadas):** {txt_quentes}\n\n" \
           f"☀️ **Mornas (Frequência intermediária):** {txt_mornas}\n\n" \
           f"❄️ **Frias (Menos sorteadas):** {txt_frias}"
def validar_soma_jogo(soma: float) -> str:
    """Equivalente em Python da fórmula do Excel: =SE(E(G2>=166;G2<=224);'✅ DENTRO';'❌ FORA')"""
    if soma == 0 or soma is None:
        return ""
    
    if 166 <= soma <= 224:
        return "✅ DENTRO (Padrão: 166 a 224)"
    else:
        return "❌ FORA (Padrão: 166 a 224)"
