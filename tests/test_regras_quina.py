"""Testes das regras da Quina (5 de 80)."""

import pytest
from src.regras_quina import (
    validar_jogo,
    validar_entrada,
    calcular_metricas,
    avaliar_regras,
    TOTAL_DEZENAS,
    DEZENA_MAXIMA,
)


class TestValidarEntrada:
    def test_entrada_valida(self):
        resultado = validar_entrada([3, 15, 37, 52, 74])
        assert resultado == [3, 15, 37, 52, 74]

    def test_entrada_ordenada(self):
        resultado = validar_entrada([74, 3, 52, 15, 37])
        assert resultado == [3, 15, 37, 52, 74]

    def test_dezena_zero_levanta_excecao(self):
        with pytest.raises(ValueError):
            validar_entrada([0, 15, 37, 52, 74])

    def test_dezena_acima_maximo_levanta_excecao(self):
        with pytest.raises(ValueError):
            validar_entrada([3, 15, 37, 52, 81])

    def test_dezena_repetida_levanta_excecao(self):
        with pytest.raises(ValueError):
            validar_entrada([3, 15, 15, 52, 74])

    def test_quantidade_errada_menos(self):
        with pytest.raises(ValueError):
            validar_entrada([3, 15, 37, 52])

    def test_quantidade_errada_mais(self):
        with pytest.raises(ValueError):
            validar_entrada([3, 15, 37, 52, 74, 78])

    def test_entrada_vazia(self):
        with pytest.raises(ValueError):
            validar_entrada([])


class TestCalcularMetricas:
    def test_metricas_contem_chaves(self):
        jogo = [3, 15, 37, 52, 74]
        m = calcular_metricas(jogo)
        assert isinstance(m, dict)
        assert "soma" in m
        assert "pares" in m
        assert "moldura" in m

    def test_soma_correta(self):
        jogo = [10, 20, 30, 40, 50]
        m = calcular_metricas(jogo)
        assert m["soma"] == 150


class TestAvaliarRegras:
    def test_retorna_dict_bool(self):
        jogo = [3, 15, 37, 52, 74]
        r = avaliar_regras(jogo)
        assert isinstance(r, dict)
        assert all(isinstance(v, bool) for v in r.values())

    def test_15_regras(self):
        jogo = [3, 15, 37, 52, 74]
        r = avaliar_regras(jogo)
        assert len(r) == 15


class TestValidarJogo:
    def test_retorna_bool(self):
        jogo = [3, 15, 37, 52, 74]
        resultado = validar_jogo(jogo)
        assert isinstance(resultado, bool)

    def test_jogo_invalido_levanta_excecao(self):
        with pytest.raises(ValueError):
            validar_jogo([0, 15, 37, 52, 74])


class TestConstantes:
    def test_total_dezenas(self):
        assert TOTAL_DEZENAS == 5

    def test_dezena_maxima(self):
        assert DEZENA_MAXIMA == 80
