import pytest
from src.regras_dia import (
    validar_entrada, calcular_metricas, avaliar_regras, validar_jogo,
    TOTAL_DEZENAS, DEZENA_MINIMA, DEZENA_MAXIMA,
)


def test_validar_entrada_ok():
    jogo = [1, 5, 10, 15, 20, 25, 31]
    assert validar_entrada(jogo) == sorted(jogo)


def test_validar_entrada_tamanho_errado():
    with pytest.raises(ValueError, match="7 dezenas"):
        validar_entrada([1, 2, 3])


def test_validar_entrada_fora_do_intervalo():
    with pytest.raises(ValueError, match="1 e 31"):
        validar_entrada([0, 5, 10, 15, 20, 25, 31])


def test_validar_entrada_repetida():
    with pytest.raises(ValueError, match="repetidas"):
        validar_entrada([1, 1, 10, 15, 20, 25, 31])


def test_calcular_metricas_chaves():
    jogo = [1, 5, 10, 15, 20, 25, 31]
    m = calcular_metricas(jogo)
    assert "soma" in m
    assert "moldura" in m
    assert "pares" in m
    assert "amplitude" in m
    assert m["soma"] == sum(jogo)
    assert m["amplitude"] == 30


def test_avaliar_regras_retorna_15():
    jogo = [1, 5, 10, 15, 20, 25, 31]
    rv = avaliar_regras(jogo)
    assert len(rv) == 15
    assert all(isinstance(v, bool) for v in rv.values())


def test_validar_jogo_tipo():
    jogo = [2, 5, 11, 16, 22, 27, 30]
    assert isinstance(validar_jogo(jogo), bool)
