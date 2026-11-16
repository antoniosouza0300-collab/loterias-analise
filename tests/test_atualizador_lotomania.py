"""Testes do atualizador da Lotomania."""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.atualizador_lotomania import (
    converter_resultado_api,
    gravar_historico,
    ler_historico,
    COLUNAS,
)


MOCK_JSON = {
    "numero": 2800,
    "dataApuracao": "20/06/2025",
    "listaDezenas": [
        "03", "07", "12", "18", "22", "27", "33", "38", "41", "45",
        "50", "55", "60", "64", "69", "73", "78", "82", "88", "95",
    ],
}


class TestConverterResultadoApi:
    def test_converte_corretamente(self):
        registro = converter_resultado_api(MOCK_JSON)
        assert registro["concurso"] == 2800
        assert registro["bola1"] == 3
        assert registro["bola20"] == 95

    def test_colunas_completas(self):
        registro = converter_resultado_api(MOCK_JSON)
        assert set(registro.keys()) == set(COLUNAS)

    def test_20_bolas(self):
        registro = converter_resultado_api(MOCK_JSON)
        bolas = [registro[f"bola{i}"] for i in range(1, 21)]
        assert len(bolas) == 20
        assert bolas == sorted(bolas)

    def test_dados_invalidos_levanta_excecao(self):
        with pytest.raises(ValueError):
            converter_resultado_api("nao_e_dict")

    def test_dezenas_insuficientes(self):
        dados = {"numero": 1, "listaDezenas": ["01", "02"]}
        with pytest.raises(ValueError):
            converter_resultado_api(dados)


class TestGravarELerHistorico:
    def test_gravar_e_ler(self, tmp_path):
        arquivo = str(tmp_path / "lotomania_teste.csv")
        dados = [converter_resultado_api(MOCK_JSON)]
        gravar_historico(dados, arquivo)

        assert os.path.exists(arquivo)
        carregado = ler_historico(arquivo)
        assert len(carregado) == 1
        assert carregado[0]["concurso"] == 2800
        assert carregado[0]["bola1"] == 3
        assert carregado[0]["bola20"] == 95

    def test_ler_arquivo_inexistente(self, tmp_path):
        arquivo = str(tmp_path / "nao_existe.csv")
        carregado = ler_historico(arquivo)
        assert carregado == []
