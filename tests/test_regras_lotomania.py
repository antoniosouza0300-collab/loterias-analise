"""Testes das regras da Lotomania (20 de 100)."""

import pytest
from src.regras_lotomania import (
    validar_jogo,
    validar_entrada,
    calcular_metricas,
    avaliar_regras,
    TOTAL_DEZENAS,
    DEZENA_MAXIMA,
)


class TestValidarEntrada:
    def test_entrada_valida(self):
        jogo = list(range(1, 21))
        resultado = validar_entrada(jogo)
        assert resultado == list(range(1, 21))

    def test_entrada_desordenada(self):
        jogo = list(range(20, 0, -1))
        resultado = validar_entrada(jogo)
        assert resultado == list(range(1, 21))

    def test_dezena_zero_levanta_excecao(self):
        jogo = [0] + list(range(2, 21))
        with pytest.raises(ValueError):
            validar_entrada(jogo)

    def test_dezena_acima_maximo(self):
        jogo = [101] + list(range(2, 21))
        with pytest.raises(ValueError):
            validar_entrada(jogo)

    def test_dezena_repetida(self):
        jogo = [1, 1] + list(range(3, 21))
        with pytest.raises(ValueError):
            validar_entrada(jogo)

    def test_quantidade_errada_menos(self):
        jogo = list(range(1, 20))
        with pytest.raises(ValueError):
            validar_entrada(jogo)

    def test_quantidade_errada_mais(self):
        jogo = list(range(1, 22))
        with pytest.raises(ValueError):
            validar_entrada(jogo)

    def test_entrada_vazia(self):
        with pytest.raises(ValueError):
            validar_entrada([])


class TestCalcularMetricas:
    def test_metricas_contem_chaves(self):
        jogo = list(range(1, 21))
        m = calcular_metricas(jogo)
        assert "soma" in m
        assert "pares" in m
        assert "moldura" in m
        assert "amplitude" in m

    def test_soma_correta(self):
        jogo = list(range(1, 21))
        m = calcular_metricas(jogo)
        assert m["soma"] == sum(range(1, 21))

    def test_amplitude(self):
        jogo = list(range(1, 21))
        m = calcular_metricas(jogo)
        assert m["amplitude"] == 19


class TestAvaliarRegras:
    def test_retorna_dict_bool(self):
        jogo = list(range(1, 21))
        r = avaliar_regras(jogo)
        assert isinstance(r, dict)
        assert all(isinstance(v, bool) for v in r.values())

    def test_15_regras(self):
        jogo = list(range(1, 21))
        r = avaliar_regras(jogo)
        assert len(r) == 15


class TestValidarJogo:
    def test_retorna_bool(self):
        jogo = list(range(1, 21))
        resultado = validar_jogo(jogo)
        assert isinstance(resultado, bool)

    def test_jogo_invalido_levanta_excecao(self):
        with pytest.raises(ValueError):
            validar_jogo([0] + list(range(2, 21)))


class TestConstantes:
    def test_total_dezenas(self):
        assert TOTAL_DEZENAS == 20

    def test_dezena_maxima(self):
        assert DEZENA_MAXIMA == 100
