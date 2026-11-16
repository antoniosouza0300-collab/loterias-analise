import pytest

from src.regras import (
    avaliar_regras,
    calcular_metricas,
    validar_entrada,
    validar_jogo,
)


JOGO_EXEMPLO = list(range(1, 16))


@pytest.mark.parametrize(
    "jogo",
    [
        [1, 2, 3],
        [1] * 15,
        [0] + list(range(2, 16)),
        list(range(1, 15)) + [26],
        list(range(1, 15)) + [15.5],
        list(range(1, 15)) + ["15"],
        None,
        "123456789012345",
    ],
)
def test_validar_entrada_rejeita_jogos_invalidos(jogo):
    with pytest.raises(ValueError):
        validar_entrada(jogo)


def test_validar_entrada_aceita_jogo_valido():
    resultado = validar_entrada(JOGO_EXEMPLO)

    assert resultado == JOGO_EXEMPLO
    assert len(resultado) == 15
    assert len(set(resultado)) == 15


def test_validar_entrada_normaliza_ordem():
    jogo = list(reversed(JOGO_EXEMPLO))

    assert validar_entrada(jogo) == JOGO_EXEMPLO


def test_calcular_metricas_jogo_de_1_a_15():
    metricas = calcular_metricas(JOGO_EXEMPLO)

    assert metricas["soma"] == 120
    assert metricas["moldura"] == 9
    assert metricas["pares"] == 7
    assert metricas["primos"] == 6
    assert metricas["multiplos_de_3"] == 5
    assert metricas["gemeos"] == 1
    assert metricas["linhas"] == [5, 5, 5, 0, 0]
    assert metricas["pares_linhas_1_e_2"] == [2, 3]
    assert metricas["quadrantes"] == [9, 6, 0, 0]
    assert metricas["miolo"] == 6
    assert metricas["maior_frequencia_final"] == 2
    assert metricas["colunas"] == [3, 3, 3, 3, 3]
    assert metricas["diagonal_principal"] == 3
    assert metricas["diagonal_secundaria"] == 3
    assert metricas["fibonacci"] == 6
    assert metricas["menor_dezena"] == 1
    assert metricas["maior_dezena"] == 15


def test_avaliar_regras_retorna_exatamente_15_resultados_booleanos():
    resultado = avaliar_regras(JOGO_EXEMPLO)

    assert len(resultado) == 15
    assert all(type(valor) is bool for valor in resultado.values())


def test_avaliar_regras_jogo_de_1_a_15():
    resultado = avaliar_regras(JOGO_EXEMPLO)

    assert resultado == {
        "soma": False,
        "moldura": True,
        "pares": True,
        "primos": True,
        "multiplos_de_3": True,
        "gemeos": True,
        "linhas": False,
        "paridade_linhas_1_e_2": True,
        "quadrantes": False,
        "miolo": True,
        "finais": True,
        "colunas": True,
        "diagonais": True,
        "fibonacci": False,
        "inicio_fim": False,
    }


def test_validar_jogo_corresponde_a_aprovacao_das_15_regras():
    resultado = avaliar_regras(JOGO_EXEMPLO)

    assert validar_jogo(JOGO_EXEMPLO) is all(resultado.values())
