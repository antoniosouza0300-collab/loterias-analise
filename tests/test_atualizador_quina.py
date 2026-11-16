"""Testes do atualizador da Quina."""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.atualizador_quina import (
    converter_resultado_api,
    gravar_historico,
    ler_historico,
    COLUNAS,
)


MOCK_JSON = {
    "numero": 6500,
    "dataApuracao": "15/06/2025",
    "listaDezenas": ["07", "23", "41", "58", "72"],
}


class TestConverterResultadoApi:
    def test_converte_corretamente(self):
        registro = converter_resultado_api(MOCK_JSON)
        assert registro["concurso"] == 6500
        assert registro["bola1"] == 7
        assert registro["bola2"] == 23
        assert registro["bola3"] == 41
        assert registro["bola4"] == 58
        assert registro["bola5"] == 72

    def test_colunas_completas(self):
        registro = converter_resultado_api(MOCK_JSON)
        assert set(registro.keys()) == set(COLUNAS)

    def test_dados_invalidos_levanta_excecao(self):
        with pytest.raises(ValueError):
            converter_resultado_api("nao_e_dict")


class TestGravarELerHistorico:
    def test_gravar_e_ler(self, tmp_path):
        arquivo = str(tmp_path / "quina_teste.csv")
        dados = [converter_resultado_api(MOCK_JSON)]
        gravar_historico(dados, arquivo)

        assert os.path.exists(arquivo)
        carregado = ler_historico(arquivo)
        assert len(carregado) == 1
        assert carregado[0]["concurso"] == 6500
        assert carregado[0]["bola1"] == 7

    def test_ler_arquivo_inexistente(self, tmp_path):
        arquivo = str(tmp_path / "nao_existe.csv")
        carregado = ler_historico(arquivo)
        assert carregado == []
