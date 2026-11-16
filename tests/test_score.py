"""Testes do score de aderência."""

from src.score import calcular_score, classificar_score, formatar_score


def _mock_avaliar_regras(jogo):
    """Mock que aprova tudo se soma > 100."""
    return {
        "soma": sum(jogo) > 100,
        "pares": True,
        "primos": True,
        "moldura": sum(jogo) > 50,
    }


class TestCalcularScore:
    def test_score_perfeito(self):
        r = calcular_score([30, 40, 50, 60, 70], _mock_avaliar_regras)
        assert r["score"] == 100
        assert r["aprovadas"] == 4
        assert r["falhas"] == []

    def test_score_parcial(self):
        r = calcular_score([1, 2, 3, 4, 5], _mock_avaliar_regras)
        assert 0 < r["score"] < 100
        assert len(r["falhas"]) > 0

    def test_jogo_invalido(self):
        def bad_fn(j):
            raise ValueError("inválido")
        r = calcular_score([], bad_fn)
        assert r["score"] == 0
        assert "jogo inválido" in r["falhas"]


class TestClassificarScore:
    def test_excelente(self):
        rotulo, cor = classificar_score(95)
        assert rotulo == "Excelente"
        assert cor == "#22c55e"

    def test_muito_fraco(self):
        rotulo, cor = classificar_score(10)
        assert rotulo == "Muito fraco"


class TestFormatarScore:
    def test_formato(self):
        r = {"score": 75, "aprovadas": 3, "total": 4, "falhas": ["soma"]}
        texto = formatar_score(r)
        assert "75/100" in texto
        assert "soma" in texto
