"""Testes da camada SQLite."""

import pytest
from src.config import QUINA, LOTOFACIL
from src.database import (
    inicializar_banco,
    inserir_concurso,
    buscar_ultimo_concurso,
    buscar_historico,
    contar_concursos,
    _get_conn,
    DB_PATH,
)


@pytest.fixture(autouse=True)
def banco_limpo(tmp_path, monkeypatch):
    """Usa banco temporário para cada teste."""
    db_teste = tmp_path / "teste.db"
    monkeypatch.setattr("src.database.DB_PATH", db_teste)
    inicializar_banco()
    yield
    if db_teste.exists():
        db_teste.unlink()


class TestInicializarBanco:
    def test_cria_tabelas(self):
        conn = _get_conn()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        nomes = [t["name"] for t in tables]
        assert "quina" in nomes
        assert "lotofacil" in nomes
        conn.close()


class TestInserirBuscar:
    def test_inserir_e_buscar(self):
        reg = {"concurso": 6500, "data": "15/06/2025",
               "bola1": 7, "bola2": 23, "bola3": 41,
               "bola4": 58, "bola5": 72}
        assert inserir_concurso(QUINA, reg) is True
        assert contar_concursos(QUINA) == 1

    def test_duplicata_ignora(self):
        reg = {"concurso": 6500, "data": "15/06/2025",
               "bola1": 7, "bola2": 23, "bola3": 41,
               "bola4": 58, "bola5": 72}
        inserir_concurso(QUINA, reg)
        assert inserir_concurso(QUINA, reg) is False
        assert contar_concursos(QUINA) == 1

    def test_ultimo_concurso(self):
        for i in range(1, 4):
            reg = {"concurso": i, "data": "01/01/2025",
                   "bola1": 1, "bola2": 2, "bola3": 3,
                   "bola4": 4, "bola5": 5}
            inserir_concurso(QUINA, reg)
        assert buscar_ultimo_concurso(QUINA) == 3

    def test_historico_ordenado(self):
        for i in [5, 3, 1]:
            reg = {"concurso": i, "data": "01/01/2025",
                   "bola1": 1, "bola2": 2, "bola3": 3,
                   "bola4": 4, "bola5": 5}
            inserir_concurso(QUINA, reg)
        hist = buscar_historico(QUINA)
        concursos = [h["concurso"] for h in hist]
        assert concursos == [1, 3, 5]

    def test_banco_vazio(self):
        assert buscar_ultimo_concurso(QUINA) is None
        assert buscar_historico(QUINA) == []
        assert contar_concursos(QUINA) == 0
