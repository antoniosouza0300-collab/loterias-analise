"""Testes da configuração centralizada."""

from src.config import (
    LoteriaConfig,
    LOTOFACIL,
    DIA_DE_SORTE,
    MEGA_SENA,
    QUINA,
    TODAS_LOTERIAS,
    TOTAL_CONCURSOS_HISTORICO,
)


class TestLoteriaConfig:
    def test_colunas_csv_lotofacil(self):
        cols = LOTOFACIL.colunas_csv
        assert cols[0] == "concurso"
        assert cols[1] == "data"
        assert cols[2] == "bola1"
        assert cols[-1] == "bola15"
        assert len(cols) == 17

    def test_colunas_csv_quina(self):
        cols = QUINA.colunas_csv
        assert len(cols) == 7
        assert cols[-1] == "bola5"

    def test_arquivo_csv(self):
        assert LOTOFACIL.arquivo_csv == "data/lotofacil.csv"
        assert QUINA.arquivo_csv == "data/quina.csv"

    def test_url_api(self):
        assert "lotofacil" in LOTOFACIL.url_api
        assert "quina" in QUINA.url_api
        assert "megasena" in MEGA_SENA.url_api

    def test_imutavel(self):
        import dataclasses
        assert LOTOFACIL.__dataclass_params__.frozen is True

    def test_todas_loterias(self):
        assert len(TODAS_LOTERIAS) == 5
        siglas = [l.sigla for l in TODAS_LOTERIAS]
        assert "lotofacil" in siglas
        assert "quina" in siglas
        assert "lotomania" in siglas

    def test_total_concursos(self):
        assert TOTAL_CONCURSOS_HISTORICO == 100
