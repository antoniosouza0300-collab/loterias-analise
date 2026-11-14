
from __future__ import annotations

import csv
import json
import os
import tempfile
import time
import urllib.error
import urllib.request

from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURAÇÕES
# ============================================================

URL_API = (
    "https://servicebus2.caixa.gov.br/"
    "portaldeloterias/api/lotofacil"
)

TOTAL_CONCURSOS = 100
TIMEOUT = 45
MAX_TENTATIVAS = 5
INTERVALO_REQUISICOES = 1.0

ARQUIVO_CSV = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "lotofacil.csv"
)

COLUNAS = [
    "concurso",
    "data",
    *[f"bola{i}" for i in range(1, 16)],
]

_ultima_requisicao = 0.0


# ============================================================
# COMUNICAÇÃO COM A API
# ============================================================

def aguardar_intervalo() -> None:
    """Controla o intervalo entre requisições."""

    global _ultima_requisicao

    agora = time.monotonic()
    decorrido = agora - _ultima_requisicao

    if decorrido < INTERVALO_REQUISICOES:
        time.sleep(INTERVALO_REQUISICOES - decorrido)

    _ultima_requisicao = time.monotonic()


def requisitar_json(url: str) -> dict[str, Any]:
    """Consulta a API com timeout e novas tentativas."""

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; LotofacilAnalise/1.0)",
        "Accept": "application/json, text/plain, */*",
    }

    for tentativa in range(MAX_TENTATIVAS):
        aguardar_intervalo()

        requisicao = urllib.request.Request(
            url,
            headers=headers,
            method="GET",
        )

        try:
            with urllib.request.urlopen(
                requisicao,
                timeout=TIMEOUT,
            ) as resposta:
                conteudo = resposta.read().decode("utf-8")
                dados = json.loads(conteudo)

                if not isinstance(dados, dict):
                    raise RuntimeError(
                        f"Resposta inesperada da API: {url}"
                    )

                return dados

        except urllib.error.HTTPError as erro:
            codigo = erro.code

            if codigo not in (429, 500, 502, 503, 504):
                raise RuntimeError(
                    f"Erro HTTP {codigo} ao consultar a CAIXA: {url}"
                ) from erro

            retry_after = erro.headers.get("Retry-After")

            try:
                espera = float(retry_after)
            except (TypeError, ValueError):
                espera = 2 ** tentativa

        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as erro:
            espera = 2 ** tentativa

        if tentativa == MAX_TENTATIVAS - 1:
            raise RuntimeError(
                f"Falha após {MAX_TENTATIVAS} tentativas: {url}"
            ) from erro

        time.sleep(min(espera, 60))

    raise RuntimeError("Não foi possível consultar a API.")


def consultar_concurso(numero: int | None = None) -> dict:
    """Consulta o último concurso ou um concurso específico."""

    if numero is None:
        url = URL_API
    else:
        if numero < 1:
            raise ValueError("Número de concurso inválido.")

        url = f"{URL_API}/{numero}"

    return requisitar_json(url)


# ============================================================
# NORMALIZAÇÃO E VALIDAÇÃO
# ============================================================

def converter_data(valor: str) -> str:
    """Converte datas para o padrão ISO YYYY-MM-DD."""

    valor = str(valor).strip()

    formatos = (
        "%d/%m/%Y",
        "%Y-%m-%d",
    )

    for formato in formatos:
        try:
            return datetime.strptime(
                valor,
                formato,
            ).strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError(f"Data inválida: {valor}")


def converter_resultado_api(dados: dict) -> dict:
    """Converte a resposta da CAIXA para o formato do CSV."""

    try:
        concurso = int(dados["numero"])
        data = converter_data(dados["dataApuracao"])

        dezenas = [
            int(dezena)
            for dezena in dados["listaDezenas"]
        ]

    except (KeyError, TypeError, ValueError) as erro:
        raise ValueError(
            f"Formato inesperado no resultado da CAIXA: {erro}"
        ) from erro

    if concurso < 1:
        raise ValueError("Número de concurso inválido.")

    if len(dezenas) != 15:
        raise ValueError(
            f"Concurso {concurso}: esperado 15 dezenas."
        )

    if len(set(dezenas)) != 15:
        raise ValueError(
            f"Concurso {concurso}: existem dezenas repetidas."
        )

    if any(dezena < 1 or dezena > 25 for dezena in dezenas):
        raise ValueError(
            f"Concurso {concurso}: dezena fora do intervalo 1–25."
        )

    registro = {
        "concurso": concurso,
        "data": data,
    }

    for indice, dezena in enumerate(sorted(dezenas), start=1):
        registro[f"bola{indice}"] = dezena

    return registro


def validar_registro(registro: dict) -> dict:
    """Valida e normaliza um registro."""

    try:
        concurso = int(registro["concurso"])
        data = converter_data(registro["data"])

        dezenas = [
            int(registro[f"bola{i}"])
            for i in range(1, 16)
        ]

    except (KeyError, TypeError, ValueError) as erro:
        raise ValueError(
            f"Registro inválido: {erro}"
        ) from erro

    if concurso < 1:
        raise ValueError("Número de concurso inválido.")

    if len(set(dezenas)) != 15:
        raise ValueError(
            f"Concurso {concurso}: dezenas repetidas."
        )

    if any(dezena < 1 or dezena > 25 for dezena in dezenas):
        raise ValueError(
            f"Concurso {concurso}: dezenas fora do intervalo."
        )

    registro_validado = {
        "concurso": concurso,
        "data": data,
    }

    for indice, dezena in enumerate(sorted(dezenas), start=1):
        registro_validado[f"bola{indice}"] = dezena

    return registro_validado


def validar_historico(registros: list[dict]) -> list[dict]:
    """Verifica duplicidades e sequência dos concursos."""

    normalizados = [
        validar_registro(registro)
        for registro in registros
    ]

    normalizados.sort(key=lambda item: item["concurso"])

    numeros = [
        registro["concurso"]
        for registro in normalizados
    ]

    if len(numeros) != len(set(numeros)):
        raise ValueError("O histórico contém concursos duplicados.")

    for anterior, atual in zip(numeros, numeros[1:]):
        if atual != anterior + 1:
            raise ValueError(
                f"Sequência interrompida entre "
                f"os concursos {anterior} e {atual}."
            )

    return normalizados


# ============================================================
# LEITURA DO CSV
# ============================================================

def ler_historico() -> list[dict]:
    """Lê o CSV existente. Não altera o arquivo original."""

    if not ARQUIVO_CSV.exists():
        return []

    registros = []

    with ARQUIVO_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:

        leitor = csv.DictReader(arquivo)

        if not leitor.fieldnames:
            raise ValueError("O CSV existente está vazio ou inválido.")

        nomes = {
            nome.strip().lower()
            for nome in leitor.fieldnames
        }

        obrigatorias = set(COLUNAS)

        if not obrigatorias.issubset(nomes):
            raise ValueError(
                "O CSV existente não possui todas as colunas obrigatórias."
            )

        for linha in leitor:
            linha_normalizada = {
                str(chave).strip().lower(): valor
                for chave, valor in linha.items()
                if chave is not None
            }

            registros.append(
                validar_registro(linha_normalizada)
            )

    return validar_historico(registros)


# ============================================================
# GRAVAÇÃO ATÔMICA
# ============================================================

def gravar_atomicamente(registros: list[dict]) -> None:
    """
    Grava em arquivo temporário e substitui o CSV
    somente depois que a gravação termina corretamente.
    """

    ARQUIVO_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivo_temporario = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=ARQUIVO_CSV.parent,
            suffix=".tmp",
            prefix="lotofacil_",
            delete=False,
        ) as temporario:

            arquivo_temporario = Path(temporario.name)

            escritor = csv.DictWriter(
                temporario,
                fieldnames=COLUNAS,
                delimiter=",",
            )

            escritor.writeheader()

            for registro in registros:
                escritor.writerow(registro)

            temporario.flush()
            os.fsync(temporario.fileno())

        os.replace(
            arquivo_temporario,
            ARQUIVO_CSV,
        )

    finally:
        if (
            arquivo_temporario is not None
            and arquivo_temporario.exists()
        ):
            arquivo_temporario.unlink()


# ============================================================
# ATUALIZAÇÃO DOS ÚLTIMOS 100 CONCURSOS
# ============================================================

def atualizar_historico() -> dict:
    """
    Atualiza o histórico mantendo somente os últimos 100 concursos.

    Primeira execução:
        Consulta individualmente os 100 concursos.

    Execuções seguintes:
        Consulta os concursos ausentes e o concurso mais recente,
        permitindo detectar correções no resultado mais atual.

    A operação é idempotente: executar novamente sem alterações
    não duplica registros nem regrava o CSV desnecessariamente.
    """

    print("Consultando o concurso mais recente da CAIXA...")

    dados_atual = consultar_concurso()
    registro_atual = converter_resultado_api(dados_atual)

    numero_atual = registro_atual["concurso"]
    primeiro_concurso = max(1, numero_atual - TOTAL_CONCURSOS + 1)

    anterior = ler_historico()

    mapa_anterior = {
        registro["concurso"]: registro
        for registro in anterior
    }

    if anterior:
        ultimo_local = max(mapa_anterior)

        if ultimo_local > numero_atual:
            raise ValueError(
                "O CSV contém concurso posterior ao informado pela CAIXA."
            )

    else:
        ultimo_local = 0

    mapa_novo = {
        numero: registro
        for numero, registro in mapa_anterior.items()
        if primeiro_concurso <= numero <= numero_atual
    }

    novos_concursos = 0
    consultas = 0

    total_necessario = numero_atual - primeiro_concurso + 1

    print(
        f"Atualizando a janela de concursos "
        f"{primeiro_concurso} a {numero_atual}..."
    )

    for numero in range(primeiro_concurso, numero_atual + 1):

        # Consulta concursos ausentes e sempre reconsulta o mais recente.
        if numero not in mapa_novo or numero == numero_atual:

            if numero == numero_atual:
                dados = dados_atual
            else:
                dados = consultar_concurso(numero)

            registro = converter_resultado_api(dados)

            if registro["concurso"] != numero:
                raise ValueError(
                    f"A API retornou o concurso "
                    f"{registro['concurso']} ao solicitar {numero}."
                )

            if numero not in mapa_anterior:
                novos_concursos += 1

            mapa_novo[numero] = registro
            consultas += 1

        if consultas and consultas % 10 == 0:
            print(
                f"Consultas individuais concluídas: {consultas}"
            )

    resultado = sorted(
        mapa_novo.values(),
        key=lambda item: item["concurso"],
    )

    resultado = validar_historico(resultado)

    if len(resultado) != total_necessario:
        raise ValueError(
            f"Histórico incompleto: esperados {total_necessario}, "
            f"obtidos {len(resultado)}."
        )

    if len(resultado) > TOTAL_CONCURSOS:
        resultado = resultado[-TOTAL_CONCURSOS:]

    if len(resultado) != total_necessario:
        raise ValueError("Quantidade final de concursos inválida.")

    alterado = resultado != anterior

    if alterado:
        gravar_atomicamente(resultado)
        print("CSV atualizado com sucesso.")
    else:
        print("Nenhuma alteração necessária. CSV preservado.")

    return {
        "arquivo": str(ARQUIVO_CSV),
        "concurso_atual": numero_atual,
        "primeiro_concurso": resultado[0]["concurso"],
        "ultimo_concurso": resultado[-1]["concurso"],
        "total_concursos": len(resultado),
        "novos_concursos": novos_concursos,
        "consultas_individuais": consultas,
        "arquivo_alterado": alterado,
        "status": "sucesso",
    }


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    try:
        resultado = atualizar_historico()

        print("\nRESUMO DA ATUALIZAÇÃO")
        print("-" * 40)

        for chave, valor in resultado.items():
            print(f"{chave}: {valor}")

    except Exception as erro:
        print("\nERRO NA ATUALIZAÇÃO")
        print(f"Motivo: {erro}")
        print("O CSV anterior foi preservado.")
        raise
