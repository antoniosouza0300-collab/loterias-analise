from pathlib import Path
import numpy as np
import pandas as pd

COLUNAS_DEZENAS = [f"bola{i}" for i in range(1, 16)]
COLUNAS_OBRIGATORIAS = ["concurso", *COLUNAS_DEZENAS]


def validar_resultados(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("A entrada precisa ser um DataFrame.")
    dados = df.copy().reset_index(drop=True)
    if dados.empty:
        raise ValueError("DataFrame vazio.")

    dados.columns = [str(c).strip().lower() for c in dados.columns]
    dup = dados.columns[dados.columns.duplicated()].tolist()
    if dup:
        raise ValueError(f"Colunas duplicadas: {', '.join(dup)}")

    falt = [c for c in COLUNAS_OBRIGATORIAS if c not in dados.columns]
    if falt:
        raise ValueError(f"Colunas ausentes: {', '.join(falt)}")

    problemas = []

    # Conversão vetorizada de concurso e dezenas
    col_num = ["concurso", *COLUNAS_DEZENAS]
    for c in col_num:
        vals = pd.to_numeric(dados[c], errors="coerce")
        invalidos = vals.isna() | (vals % 1 != 0)
        if invalidos.any():
            linhas = (dados.index[invalidos] + 2).tolist()
            problemas.append(f"Valores inválidos em '{c}', linhas: {linhas}")
        else:
            dados[c] = vals.astype("int64")

    if problemas:
        raise ValueError("\n".join(problemas))

    if (dados["concurso"] <= 0).any():
        problemas.append("Concursos devem ser positivos.")
    if dados["concurso"].duplicated().any():
        dups = dados.loc[dados["concurso"].duplicated(keep=False), "concurso"].tolist()
        problemas.append(f"Concursos duplicados: {dups}")

    # Validação VETORIZADA de dezenas (elimina iterrows)
    mat = dados[COLUNAS_DEZENAS].values  # shape (n, 15)

    fora = (mat < 1) | (mat > 25)
    linhas_fora = (dados.index[fora.any(axis=1)] + 2).tolist()
    if linhas_fora:
        problemas.append(f"Dezenas fora de 1–25 nas linhas: {linhas_fora}")

    # Duplicatas por linha via NumPy (rápido)
    for idx in np.where(np.apply_along_axis(lambda r: len(set(r)) != 15, 1, mat))[0]:
        problemas.append(f"Linha {idx + 2}: dezenas repetidas.")

    if "data" in dados.columns:
        datas = pd.to_datetime(dados["data"], errors="coerce", dayfirst=True)
        inv = datas.isna()
        if inv.any():
            problemas.append(f"Datas inválidas: {(dados.index[inv] + 2).tolist()}")
        else:
            dados["data"] = datas.dt.strftime("%Y-%m-%d")

    if problemas:
        raise ValueError("Problemas no CSV:\n- " + "\n- ".join(problemas))

    return dados.sort_values("concurso").reset_index(drop=True)


def importar_resultados(caminho: str | Path) -> pd.DataFrame:
    arquivo = Path(caminho)
    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
    try:
        dados = pd.read_csv(arquivo, sep=None, engine="python", encoding="utf-8-sig")
    except Exception as e:
        raise ValueError(f"Erro ao ler CSV: {e}") from e
    return validar_resultados(dados)
