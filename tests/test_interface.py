import pytest
from src.interface import (
    validar_soma_jogo, validar_moldura_jogo, validar_pares_jogo,
    validar_primos_jogo, validar_mult3_jogo, validar_gemeos_jogo,
    validar_miolo_jogo, validar_finais_jogo, validar_fibonacci_jogo,
    validar_colunas_jogo, validar_diagonais_jogo,
    validar_inicio_fim_jogo, validar_paridade_linhas_excel,
    validar_quadrantes_jogo, validar_por_dezenas,
    analisar_temperatura, painel_temperatura,
    criar_aba_lotofacil, criar_interface,
)


# ── Validadores individuais ───────────────────────────────────────────
def test_validar_soma_dentro():
    assert "DENTRO" in validar_soma_jogo(195)

def test_validar_soma_fora():
    assert "FORA" in validar_soma_jogo(100)

def test_validar_moldura_dentro():
    assert "DENTRO" in validar_moldura_jogo(10)

def test_validar_moldura_fora():
    assert "FORA" in validar_moldura_jogo(5)

def test_validar_pares_dentro():
    assert "DENTRO" in validar_pares_jogo(7)

def test_validar_pares_fora():
    assert "FORA" in validar_pares_jogo(2)

def test_validar_primos_dentro():
    assert "DENTRO" in validar_primos_jogo(5)

def test_validar_mult3_dentro():
    assert "DENTRO" in validar_mult3_jogo(5)

def test_validar_gemeos_dentro():
    assert "DENTRO" in validar_gemeos_jogo(0)

def test_validar_gemeos_fora():
    assert "FORA" in validar_gemeos_jogo(2)

def test_validar_miolo_dentro():
    assert "DENTRO" in validar_miolo_jogo(4)

def test_validar_finais_dentro():
    assert "DENTRO" in validar_finais_jogo(3)

def test_validar_fibonacci_dentro():
    assert "DENTRO" in validar_fibonacci_jogo(4)

def test_validar_colunas_dentro():
    assert "DENTRO" in validar_colunas_jogo(3, 2)

def test_validar_colunas_fora():
    assert "FORA" in validar_colunas_jogo(5, 0)

def test_validar_diagonais_dentro():
    assert "DENTRO" in validar_diagonais_jogo(3, 3)

def test_validar_diagonais_fora():
    assert "FORA" in validar_diagonais_jogo(1, 5)

def test_validar_inicio_fim_dentro():
    assert "DENTRO" in validar_inicio_fim_jogo(2, 24)

def test_validar_inicio_fim_fora():
    assert "FORA" in validar_inicio_fim_jogo(10, 15)

def test_validar_paridade_linhas_dentro():
    assert "DENTRO" in validar_paridade_linhas_excel(2, 3)

def test_validar_paridade_linhas_fora():
    assert "FORA" in validar_paridade_linhas_excel(5, 2)

def test_validar_quadrantes_dentro():
    assert "DENTRO" in validar_quadrantes_jogo(5, 3)

def test_validar_quadrantes_fora():
    assert "FORA" in validar_quadrantes_jogo(7, 1)

def test_validar_vazio():
    assert validar_soma_jogo("") == ""
    assert validar_soma_jogo(None) == ""


# ── Validador por dezenas ─────────────────────────────────────────────
def test_validar_por_dezenas_vazio():
    assert "15 dezenas" in validar_por_dezenas("")

def test_validar_por_dezenas_qtd_errada():
    assert "15 dezenas" in validar_por_dezenas("1 2 3")

def test_validar_por_dezenas_fora_intervalo():
    jogo = "0 2 3 4 5 6 7 8 9 10 11 12 13 14 15"
    assert "1 e 25" in validar_por_dezenas(jogo)

def test_validar_por_dezenas_repetidas():
    jogo = "1 1 2 3 4 5 6 7 8 9 10 11 12 13 14"
    assert "repetidas" in validar_por_dezenas(jogo)

def test_validar_por_dezenas_ok():
    jogo = "1 2 3 5 7 9 11 13 15 17 19 21 23 24 25"
    resultado = validar_por_dezenas(jogo)
    assert "regras" in resultado


# ── Temperatura ───────────────────────────────────────────────────────
def test_analisar_temperatura_vazio():
    r = analisar_temperatura([])
    assert r["analisados"] == 0
    assert len(r["frias"]) == 25

def test_analisar_temperatura_com_dados():
    historico = [
        {f"bola{i}": i for i in range(1, 16)}
        for _ in range(10)
    ]
    r = analisar_temperatura(historico, 10)
    assert r["analisados"] == 10
    assert len(r["quentes"]) == 8


# ── Interface ─────────────────────────────────────────────────────────
def test_criar_interface_retorna_blocks():
    import gradio as gr
    demo = criar_interface()
    assert isinstance(demo, gr.Blocks)
