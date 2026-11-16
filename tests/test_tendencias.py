"""Testes da análise de tendências temporais."""

from src.config import QUINA
from src.tendencias import (
    frequencia_por_janela,
    classificar_tendencia,
    top_tendencias,
    resumo_tendencias_texto,
)


def _mock_historico(n=20):
    """Gera histórico mock com padrão conhecido."""
    hist = []
    for i in range(1, n + 1):
        reg = {"concurso": i, "data": "01/01/2025"}
        # Dezena 1 sempre sai, dezena 80 nunca sai
        bolas = [1, 10 + i % 20, 30 + i % 10, 50 + i % 10, 60 + i % 10]
        for j, b in enumerate(bolas, 1):
            reg[f"bola{j}"] = b
        hist.append(reg)
    return hist


class TestFrequenciaPorJanela:
    def test_retorna_todas_dezenas(self):
        hist = _mock_historico(10)
        freqs = frequencia_por_janela(hist, QUINA)
        assert len(freqs) == 80
        assert all("j10" in v for v in freqs.values())

    def test_historico_vazio(self):
        assert frequencia_por_janela([], QUINA) == {}

    def test_dezena_frequente(self):
        hist = _mock_historico(20)
        freqs = frequencia_por_janela(hist, QUINA)
        assert freqs[1]["total"] == 20  # dezena 1 sai sempre


class TestClassificarTendencia:
    def test_em_alta(self):
        assert "alta" in classificar_tendencia(8, 5)

    def test_em_baixa(self):
        assert "baixa" in classificar_tendencia(1, 10)

    def test_estavel(self):
        assert "estável" in classificar_tendencia(5, 25)


class TestTopTendencias:
    def test_retorna_alta_e_baixa(self):
        hist = _mock_historico(50)
        top = top_tendencias(hist, QUINA)
        assert "alta" in top
        assert "baixa" in top


class TestResumoTexto:
    def test_sem_dados(self):
        assert "Sem dados" in resumo_tendencias_texto([], QUINA)

    def test_com_dados(self):
        hist = _mock_historico(50)
        texto = resumo_tendencias_texto(hist, QUINA)
        assert "Tendências" in texto
