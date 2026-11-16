"""Testes para regras da Dupla Sena (6 de 50)."""
from src.regras_dupla import (
    TOTAL_DEZENAS,
    DEZENA_MAXIMA,
    validar_entrada,
    calcular_metricas,
    avaliar_regras,
    validar_jogo,
)
import pytest


class TestValidarEntrada:
    def test_valido(self):
        assert validar_entrada(list(range(1, 7))) == [1, 2, 3, 4, 5, 6]

    def test_desordenado(self):
        assert validar_entrada([6, 3, 1, 5, 2, 4]) == [1, 2, 3, 4, 5, 6]

    def test_zero(self):
        with pytest.raises(ValueError):
            validar_entrada([0, 1, 2, 3, 4, 5])

    def test_acima_max(self):
        with pytest.raises(ValueError):
            validar_entrada([1, 2, 3, 4, 5, 51])

    def test_repetido(self):
        with pytest.raises(ValueError):
            validar_entrada([1, 1, 2, 3, 4, 5])

    def test_menos_dezenas(self):
        with pytest.raises(ValueError):
            validar_entrada([1, 2, 3, 4, 5])

    def test_mais_dezenas(self):
        with pytest.raises(ValueError):
            validar_entrada([1, 2, 3, 4, 5, 6, 7])

    def test_vazio(self):
        with pytest.raises(ValueError):
            validar_entrada([])


class TestCalcularMetricas:
    def test_chaves(self):
        m = calcular_metricas(list(range(1, 7)))
        assert "soma" in m and "amplitude" in m and "pares" in m

    def test_soma(self):
        m = calcular_metricas([1, 2, 3, 4, 5, 6])
        assert m["soma"] == 21

    def test_amplitude(self):
        m = calcular_metricas([1, 2, 3, 4, 5, 6])
        assert m["amplitude"] == 5


class TestAvaliarRegras:
    def test_retorna_dict_bool(self):
        r = avaliar_regras(list(range(1, 7)))
        assert isinstance(r, dict)
        assert all(isinstance(v, bool) for v in r.values())

    def test_qtd_regras(self):
        r = avaliar_regras(list(range(1, 7)))
        assert len(r) >= 14


class TestValidarJogo:
    def test_retorna_bool(self):
        assert isinstance(validar_jogo(list(range(1, 7))), bool)

    def test_invalido_erro(self):
        with pytest.raises(ValueError):
            validar_jogo([1, 2, 3])


class TestConstantes:
    def test_total(self):
        assert TOTAL_DEZENAS == 6

    def test_max(self):
        assert DEZENA_MAXIMA == 50
