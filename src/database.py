"""Camada de persistência com SQLite — substitui CSV gradualmente."""

import sqlite3
import csv
from pathlib import Path
from typing import Any, Optional

from src.config import LoteriaConfig, TODAS_LOTERIAS
from src.logger import log

DB_PATH = Path("data/loterias.db")


def _get_conn() -> sqlite3.Connection:
    """Retorna conexão com o banco (cria se não existir)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def inicializar_banco() -> None:
    """Cria tabelas para todas as loterias se não existirem."""
    conn = _get_conn()
    try:
        for lot in TODAS_LOTERIAS:
            cols = ", ".join(f"{c} INTEGER" for c in lot.colunas_bolas)
            sql = f"""
                CREATE TABLE IF NOT EXISTS {lot.sigla} (
                    concurso INTEGER PRIMARY KEY,
                    data TEXT NOT NULL,
                    {cols}
                )
            """
            conn.execute(sql)
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{lot.sigla}_concurso "
                f"ON {lot.sigla}(concurso DESC)"
            )
        conn.commit()
        log.info("Banco SQLite inicializado: %s", DB_PATH)
    finally:
        conn.close()


def inserir_concurso(lot: LoteriaConfig, registro: dict[str, Any]) -> bool:
    """Insere um concurso. Retorna True se inseriu, False se já existia."""
    conn = _get_conn()
    try:
        cols = ["concurso", "data"] + lot.colunas_bolas
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        valores = [registro.get(c) for c in cols]
        conn.execute(
            f"INSERT OR IGNORE INTO {lot.sigla} ({col_names}) VALUES ({placeholders})",
            valores,
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def buscar_ultimo_concurso(lot: LoteriaConfig) -> Optional[int]:
    """Retorna o número do último concurso armazenado."""
    conn = _get_conn()
    try:
        row = conn.execute(
            f"SELECT MAX(concurso) FROM {lot.sigla}"
        ).fetchone()
        return row[0] if row and row[0] else None
    finally:
        conn.close()


def buscar_historico(
    lot: LoteriaConfig, limite: int = 100
) -> list[dict[str, Any]]:
    """Retorna os últimos N concursos como lista de dicts."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            f"SELECT * FROM {lot.sigla} ORDER BY concurso DESC LIMIT ?",
            (limite,),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


def contar_concursos(lot: LoteriaConfig) -> int:
    """Retorna quantos concursos há no banco."""
    conn = _get_conn()
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {lot.sigla}").fetchone()
        return row[0]
    finally:
        conn.close()


def importar_csv_para_sqlite(lot: LoteriaConfig) -> int:
    """Importa CSV existente para o SQLite. Retorna qtd de linhas."""
    csv_path = Path(lot.arquivo_csv)
    if not csv_path.exists():
        return 0

    count = 0
    with csv_path.open("r", encoding="utf-8-sig") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            registro = {}
            for k, v in linha.items():
                k = k.strip()
                if k in ("concurso",) + tuple(lot.colunas_bolas):
                    try:
                        registro[k] = int(v)
                    except (ValueError, TypeError):
                        registro[k] = v
                else:
                    registro[k] = v
            if inserir_concurso(lot, registro):
                count += 1

    log.info("%s: importadas %d linhas do CSV", lot.nome, count)
    return count
