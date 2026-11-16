import pytest
from src.regras_mega import (
    validar_entrada, calcular_metricas, avaliar_regras, validar_jogo,
    TOTAL_DEZENAS, DEZENA_MINIMA, DEZENA_MAXIMA,
)


def test_validar_entrada_ok():
    jogo = [4, 12, 25, 33, 47, 58]
    assert validar_entrada(jogo) == sorted(jogo)


def test_validar_entrada_tamanho_errado():
    with pytest.raises(ValueError, match="6 dezenas"):
        validar_entrada([1, 2, 3])


def test_validar_entrada_fora_do_intervalo():
    with pytest.raises(ValueError, match="1 e 60"):
        validar_entrada([0, 10, 20, 30, 40, 50])


def test_validar_entrada_repetida():
    with pytest.raises(ValueError, match="repetidas"):
        validar_entrada([1, 1, 20, 30, 40, 50])


def test_calcular_metricas_chaves():
    jogo = [4, 12, 25, 33, 47, 58]
    m = calcular_metricas(jogo)
    assert "soma" in m
    assert "moldura" in m
    assert "pares" in m
    assert "amplitude" in m
    assert m["soma"] == sum(jogo)
    assert m["amplitude"] == 54


def test_avaliar_regras_retorna_15():
    jogo = [4, 12, 25, 33, 47, 58]
    rv = avaliar_regras(jogo)
    assert len(rv) == 15
    assert all(isinstance(v, bool) for v in rv.values())


def test_validar_jogo_tipo():
    jogo = [5, 13, 22, 34, 41, 56]
    assert isinstance(validar_jogo(jogo), bool)
