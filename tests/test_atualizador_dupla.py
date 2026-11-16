"""Testes para o atualizador da Dupla Sena."""
import json, tempfile
from pathlib import Path
from src.atualizador_dupla import (
    converter_resultado_api,
    gravar_historico,
    ler_historico,
    COLUNAS,
)
import pytest

MOCK_JSON = {
    "numero": 2500,
    "dataApuracao": "01/01/2025",
    "listaDezenas": ["01", "10", "20", "30", "40", "50"],
    "listaDezenasSegundoSorteio": ["02", "11", "21", "31", "41", "49"],
}


class TestConverterResultadoApi:
    def test_converte(self):
        r = converter_resultado_api(MOCK_JSON)
        assert r["concurso"] == 2500
        assert r["data"] == "01/01/2025"

    def test_colunas_completas(self):
        r = converter_resultado_api(MOCK_JSON)
        for c in COLUNAS:
            assert c in r, f"Faltando coluna {c}"

    def test_6_bolas(self):
        r = converter_resultado_api(MOCK_JSON)
        assert r["bola1"] == 1 and r["bola6"] == 50

    def test_6_bolas_2s(self):
        r = converter_resultado_api(MOCK_JSON)
        assert r["bola2s_1"] == 2 and r["bola2s_6"] == 49

    def test_invalido(self):
        with pytest.raises((KeyError, ValueError, TypeError)):
            converter_resultado_api({})

    def test_dezenas_insuficientes(self):
        bad = {**MOCK_JSON, "listaDezenas": ["01", "02"]}
        with pytest.raises((ValueError, IndexError)):
            converter_resultado_api(bad)


class TestGravarELerHistorico:
    def test_gravar_e_ler(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "dupla.csv"
            dados = [converter_resultado_api(MOCK_JSON)]
            gravar_historico(dados, p)
            df = ler_historico(p)
            assert len(df) == 1
            assert df[0]["concurso"] == 2500

    def test_ler_inexistente(self):
        df = ler_historico(Path("/tmp/_nao_existe_dupla.csv"))
        assert len(df) == 0
