"""Testes da camada de integração dashboard."""

from unittest.mock import patch, MagicMock
from src.config import QUINA, LOTOFACIL
from src.dashboard import (
    get_engine,
    atualizar_loteria,
    carregar_historico,
    obter_score_jogo,
    obter_tendencias,
    _engines,
)


class TestGetEngine:
    def setup_method(self):
        _engines.clear()

    def test_cria_engine_lazy(self):
        engine = get_engine(QUINA)
        assert engine is not None
        assert engine.nome == "Quina"

    def test_reutiliza_engine(self):
        e1 = get_engine(QUINA)
        e2 = get_engine(QUINA)
        assert e1 is e2


class TestAtualizarLoteria:
    def setup_method(self):
        _engines.clear()

    @patch("src.dashboard.get_engine")
    def test_retorna_string(self, mock_get):
        mock_engine = MagicMock()
        mock_engine.atualizar.return_value = {"status": "ok", "novos": 3}
        mock_engine.total_concursos.return_value = 100
        mock_get.return_value = mock_engine

        resultado = atualizar_loteria(QUINA)
        assert "3 novos" in resultado
        assert "100" in resultado

    @patch("src.dashboard.get_engine")
    def test_offline(self, mock_get):
        mock_engine = MagicMock()
        mock_engine.atualizar.return_value = {"status": "offline", "novos": 0}
        mock_engine.total_concursos.return_value = 50
        mock_get.return_value = mock_engine

        resultado = atualizar_loteria(QUINA)
        assert "indisponível" in resultado


class TestObterScore:
    def test_retorna_string(self):
        resultado = obter_score_jogo(QUINA, [3, 15, 37, 52, 74])
        assert "Score" in resultado
        assert "/100" in resultado
