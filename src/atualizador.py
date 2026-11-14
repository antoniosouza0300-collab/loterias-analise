
from __future__ import annotations

import json
import os
import tempfile
import unicodedata
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

try:
    from .importador import importar_resultados, validar_resultados
except ImportError:
    from importador import importar_resultados, validar_resultados


# ============================================================
# CONFIGURAÇÕES
# ============================================================

URL_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"

URL_HISTORICO = (
    "https://servicebus2.caixa.gov.br/portaldeloterias/api/"
    "resultados/download?modalidade=Lotof%C3%A1cil"
)

TOTAL_CONCURSOS = 100

PASTA_PROJETO = Path(__file__).resolve().parents[1]
ARQUIVO_CSV = PASTA_PROJETO / "data" / "lotofacil.csv"

COLUNAS = [
    "concurso",
    "data",
    *[f"bola{i}" for i in range(1, 16)],
]


# ============================================================
# COMUNICAÇÃO COM A CAIXA
# ============================================================

def requisitar(url: str, timeout: int = 45) -> bytes:
    """Realiza uma requisição HTTP."""
    requisicao = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 loterias-analise/1.0",
            "Accept": "application/json, application/octet-stream, */*",
        },
    )

    try:
        with urlopen(requisicao, timeout=timeout) as resposta:
            return resposta.read()
    except Exception as erro:
        raise RuntimeError(
            f"Erro ao consultar a CAIXA: {erro}"
        ) from erro


def consultar_concurso(numero: int | None = None) -> dict:
    """Consulta o último concurso ou um concurso específico."""
    url = URL_API

    if numero is not None:
        url = f"{URL_API}/{numero}"

    try:
        conteudo = requisitar(url)
        resultado = json.loads(conteudo.decode("utf-8"))
    except Exception as erro:
        raise RuntimeError(
            f"Falha ao consultar o concurso {numero or 'mais recente'}: "
            f"{erro}"
        ) from erro

    if not isinstance(resultado, dict):
        raise ValueError("Resposta inválida da API da CAIXA.")

    return resultado


# ============================================================
# CONVERSÃO DOS RESULTADOS
# ============================================================

def normalizar_nome_coluna(nome: str) -> str:
    """Normaliza nomes de colunas do Excel."""
    texto = unicodedata.normalize("NFKD", str(nome))

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return (
        texto.lower()
        .strip()
        .replace(" ", "")
        .replace("_", "")
    )


def converter_historico_excel(conteudo: bytes) -> pd.DataFrame:
    """Lê o histórico oficial e converte para o formato do projeto."""
    try:
        original = pd.read_excel(
            BytesIO(conteudo),
            engine="openpyxl",
        )
    except Exception as erro:
        raise ValueError(
            f"Não foi possível ler o Excel oficial: {erro}"
        ) from erro

    mapa = {
        normalizar_nome_coluna(coluna): coluna
        for coluna in original.columns
    }

    aliases = {
        "concurso": ["concurso"],
        "data": ["datasorteio", "dataapuracao", "data"],
    }

    conversoes = {}

    for destino, opcoes in aliases.items():
        origem = next(
            (mapa[opcao] for opcao in opcoes if opcao in mapa),
            None,
        )

        if origem is None:
            raise ValueError(
                f"Coluna '{destino}' não encontrada no histórico."
            )

        conversoes[origem] = destino

    for numero in range(1, 16):
        destino = f"bola{numero}"

        opcoes = [
            destino,
            f"bola{numero:02d}",
        ]

        origem = next(
            (mapa[opcao] for opcao in opcoes if opcao in mapa),
            None,
        )

        if origem is None:
            raise ValueError(
                f"Coluna da dezena {numero} não encontrada."
            )

        conversoes[origem] = destino

    dados = original.rename(columns=conversoes)

    return dados[COLUNAS].copy()


def converter_resultado_api(resultado: dict) -> dict:
    """Converte a resposta JSON de um concurso."""
    try:
        numero = int(resultado["numero"])
        data = resultado["dataApuracao"]
        dezenas = resultado["listaDezenas"]

        if not isinstance(dezenas, list):
            raise ValueError("Lista de dezenas inválida.")

        if len(dezenas) != 15:
            raise ValueError("O concurso não contém 15 dezenas.")

        registro = {
            "concurso": numero,
            "data": data,
        }

        for indice, dezena in enumerate(dezenas, start=1):
            registro[f"bola{indice}"] = int(dezena)

        return registro

    except (KeyError, TypeError, ValueError) as erro:
        raise ValueError(
            f"Resultado inválido recebido da CAIXA: {erro}"
        ) from erro


# ============================================================
# VALIDAÇÃO E ORGANIZAÇÃO
# ============================================================

def verificar_sequencia(dados: pd.DataFrame) -> None:
    """Confere se os concursos são consecutivos."""
    concursos = dados["concurso"].astype(int).tolist()

    if not concursos:
        raise ValueError("Histórico vazio.")

    esperados = list(
        range(concursos[0], concursos[-1] + 1)
    )

    if concursos != esperados:
        raise ValueError(
            "Foram encontrados concursos ausentes ou fora de ordem."
        )


def preparar_ultimos_100(dados: pd.DataFrame) -> pd.DataFrame:
    """Valida e mantém somente os 100 concursos mais recentes."""
    dados = validar_resultados(dados)

    dados = dados.sort_values("concurso")
    dados = dados.drop_duplicates(
        subset=["concurso"],
        keep="last",
    )

    dados = dados.tail(TOTAL_CONCURSOS).reset_index(drop=True)

    if len(dados) != TOTAL_CONCURSOS:
        raise ValueError(
            f"Histórico incompleto: encontrados {len(dados)} "
            f"concursos, esperados {TOTAL_CONCURSOS}."
        )

    verificar_sequencia(dados)

    return dados[COLUNAS]


# ============================================================
# GRAVAÇÃO ATÔMICA
# ============================================================

def gravar_atomicamente(
    dados: pd.DataFrame,
    destino: Path,
) -> None:
    """
    Grava em arquivo temporário e substitui o CSV somente
    depois que a gravação for concluída.
    """
    destino.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporario = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            suffix=".tmp",
            prefix="lotofacil_",
            dir=destino.parent,
            delete=False,
        ) as arquivo:

            temporario = Path(arquivo.name)

            dados.to_csv(
                arquivo,
                index=False,
                columns=COLUNAS,
            )

            arquivo.flush()
            os.fsync(arquivo.fileno())

        # Substituição atômica.
        os.replace(temporario, destino)

    finally:
        if temporario and temporario.exists():
            temporario.unlink()


# ============================================================
# ATUALIZAÇÃO DO HISTÓRICO
# ============================================================

def atualizar_historico(
    caminho: str | Path = ARQUIVO_CSV,
) -> dict:

    destino = Path(caminho)

    # Consulta o concurso mais recente.
    ultimo_resultado = consultar_concurso()

    numero_atual = int(ultimo_resultado["numero"])

    # --------------------------------------------------------
    # PRIMEIRA EXECUÇÃO
    # --------------------------------------------------------

    if not destino.exists():

        print("Primeira execução: baixando histórico oficial...")

        conteudo = requisitar(URL_HISTORICO)

        historico = converter_historico_excel(conteudo)

        historico = validar_resultados(historico)

        historico = historico.sort_values("concurso")

        # Mantém somente os últimos 100.
        historico = historico.tail(TOTAL_CONCURSOS)

        # Confere o concurso mais recente.
        if int(historico["concurso"].max()) != numero_atual:
            raise ValueError(
                "O histórico baixado não corresponde "
                "ao último concurso da CAIXA."
            )

        historico = preparar_ultimos_100(historico)

        gravar_atomicamente(historico, destino)

        return {
            "status": "carga_inicial",
            "total_concursos": len(historico),
            "primeiro_concurso": int(historico["concurso"].min()),
            "ultimo_concurso": numero_atual,
            "novos_concursos": len(historico),
            "arquivo": str(destino),
        }

    # --------------------------------------------------------
    # ATUALIZAÇÕES SEGUINTES
    # --------------------------------------------------------

    anterior = importar_resultados(destino)

    anterior = anterior.sort_values("concurso")

    if len(anterior) > TOTAL_CONCURSOS:
        raise ValueError(
            "O CSV local possui mais de 100 concursos. "
            "Revise o arquivo antes de atualizar."
        )

    ultimo_local = int(anterior["concurso"].max())

    if ultimo_local > numero_atual:
        raise ValueError(
            "O CSV local possui concurso posterior ao informado pela CAIXA."
        )

    # Atualiza também o último concurso local, permitindo
    # detectar eventual correção publicada pela CAIXA.
    inicio = int(anterior["concurso"].min())

    novos_registros = []

    for numero in range(ultimo_local, numero_atual + 1):

        resultado = (
            ultimo_resultado
            if numero == numero_atual
            else consultar_concurso(numero)
        )

        registro = converter_resultado_api(resultado)

        if registro["concurso"] != numero:
            raise ValueError(
                f"Concurso inesperado: solicitado {numero}, "
                f"recebido {registro['concurso']}."
            )

        novos_registros.append(registro)

    novos = pd.DataFrame(novos_registros)

    # Remove do histórico local os concursos que serão
    # atualizados pela resposta oficial.
    anterior = anterior[
        anterior["concurso"] < ultimo_local
    ]

    combinado = pd.concat(
        [anterior, novos],
        ignore_index=True,
    )

    combinado = combinado.drop_duplicates(
        subset=["concurso"],
        keep="last",
    )

    combinado = combinado.sort_values("concurso")

    # Mantém somente os 100 mais recentes.
    combinado = combinado.tail(TOTAL_CONCURSOS)

    # Validação completa antes de qualquer gravação.
    combinado = preparar_ultimos_100(combinado)

    if int(combinado["concurso"].max()) != numero_atual:
        raise ValueError(
            "O histórico final não corresponde ao último concurso."
        )

    # Se não houve mudança, não regrava o arquivo.
    anterior_normalizado = preparar_ultimos_100(anterior) if len(anterior) >= TOTAL_CONCURSOS else anterior

    if (
        len(anterior_normalizado) == len(combinado)
        and anterior_normalizado.equals(combinado)
    ):
        return {
            "status": "sem_novidades",
            "total_concursos": len(combinado),
            "primeiro_concurso": int(combinado["concurso"].min()),
            "ultimo_concurso": numero_atual,
            "novos_concursos": 0,
            "arquivo": str(destino),
        }

    quantidade_novos = max(
        0,
        numero_atual - ultimo_local,
    )

    gravar_atomicamente(combinado, destino)

    return {
        "status": "atualizado",
        "total_concursos": len(combinado),
        "primeiro_concurso": int(combinado["concurso"].min()),
        "ultimo_concurso": numero_atual,
        "novos_concursos": quantidade_novos,
        "arquivo": str(destino),
    }


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    try:
        resultado = atualizar_historico()

        print("\nATUALIZAÇÃO DO HISTÓRICO")
        print("-" * 40)

        for chave, valor in resultado.items():
            print(f"{chave}: {valor}")

    except Exception as erro:
        print("\nFALHA NA ATUALIZAÇÃO")
        print(f"Motivo: {erro}")
        print("O CSV anterior foi preservado.")
        raise
