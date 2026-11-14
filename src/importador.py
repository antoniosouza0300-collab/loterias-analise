from pathlib import Path

import pandas as pd


COLUNAS_DEZENAS = [f"bola{i}" for i in range(1, 16)]
COLUNAS_OBRIGATORIAS = ["concurso", *COLUNAS_DEZENAS]


def validar_resultados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida os resultados da Lotofácil.

    Formato esperado:
    concurso,data,bola1,...,bola15

    A coluna data é opcional.
    Retorna uma cópia validada e ordenada por concurso.
    Levanta ValueError se encontrar problemas.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("A entrada precisa ser um DataFrame do pandas.")

    dados = df.copy()
    dados.columns = [str(col).strip().lower() for col in dados.columns]

    faltantes = [
        coluna for coluna in COLUNAS_OBRIGATORIAS
        if coluna not in dados.columns
    ]

    if faltantes:
        raise ValueError(
            "Colunas obrigatórias ausentes: " + ", ".join(faltantes)
        )

    problemas = []

    # Converte concurso e dezenas para números inteiros.
    colunas_numericas = ["concurso", *COLUNAS_DEZENAS]

    for coluna in colunas_numericas:
        valores = pd.to_numeric(dados[coluna], errors="coerce")

        invalidos = valores.isna() | (valores % 1 != 0)

        if invalidos.any():
            linhas = (dados.index[invalidos] + 2).tolist()
            problemas.append(
                f"Valores inválidos em '{coluna}', linhas: {linhas}"
            )
        else:
            dados[coluna] = valores.astype("int64")

    if problemas:
        raise ValueError("\n".join(problemas))

    if (dados["concurso"] <= 0).any():
        problemas.append("Os números dos concursos devem ser positivos.")

    if dados["concurso"].duplicated().any():
        duplicados = dados.loc[
            dados["concurso"].duplicated(keep=False), "concurso"
        ].tolist()
        problemas.append(f"Concursos duplicados: {duplicados}")

    # Valida as 15 dezenas de cada concurso.
    for indice, linha in dados.iterrows():
        dezenas = [int(linha[coluna]) for coluna in COLUNAS_DEZENAS]
        numero_linha = indice + 2

        if any(numero < 1 or numero > 25 for numero in dezenas):
            problemas.append(
                f"Linha {numero_linha}: existem dezenas fora do intervalo 1–25."
            )

        if len(set(dezenas)) != 15:
            problemas.append(
                f"Linha {numero_linha}: existem dezenas repetidas."
            )

    # A data é opcional, mas precisa ser válida quando informada.
    if "data" in dados.columns:
        datas = pd.to_datetime(dados["data"], errors="coerce", dayfirst=True)

        invalidas = datas.isna()
        if invalidas.any():
            linhas = (dados.index[invalidas] + 2).tolist()
            problemas.append(f"Datas inválidas nas linhas: {linhas}")
        else:
            dados["data"] = datas.dt.strftime("%Y-%m-%d")

    if problemas:
        raise ValueError(
            "Foram encontrados problemas no CSV:\n- "
            + "\n- ".join(problemas)
        )

    return dados.sort_values("concurso").reset_index(drop=True)


def importar_resultados(caminho: str | Path) -> pd.DataFrame:
    """
    Importa um CSV e retorna os resultados após a validação.
    """
    arquivo = Path(caminho)

    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    try:
        dados = pd.read_csv(
            arquivo,
            sep=None,
            engine="python",
            encoding="utf-8-sig",
        )
    except Exception as erro:
        raise ValueError(f"Não foi possível ler o CSV: {erro}") from erro

    return validar_resultados(dados)
