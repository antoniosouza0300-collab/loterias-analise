
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
    "portaldeloterias/api/lotofacil/"
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
# REQUISIÇÕES HTTP
# ============================================================

def aguardar_intervalo() -> None:
    """Evita realizar requisições em sequência muito rápida."""

    global _ultima_requisicao

    agora = time.monotonic()
    decorrido = agora - _ultima_requisicao

    if decorrido < INTERVALO_REQUISICOES:
        time.sleep(INTERVALO_REQUISICOES - decorrido)

    _ultima_requisicao = time.monotonic()


def requisitar_json(url: str) -> dict[str, Any]:
    """Consulta a CAIXA com timeout e tentativas controladas."""

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
                        f"A CAIXA retornou JSON inesperado: {url}"
                    )

                return dados

        except urllib.error.HTTPError as erro:
            if erro.code == 404:
                raise RuntimeError(
                    f"Concurso ou endereço não encontrado (HTTP 404): {url}"
                ) from erro

            if erro.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(
                    f"Erro HTTP {erro.code} ao consultar: {url}"
                ) from erro

            retry_after = erro.headers.get("Retry-After")

            try:
                espera = float(retry_after)
            except (TypeError, ValueError):
                espera = 2 ** tentativa

            mensagem_erro = str(erro)

        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as erro:
            espera = 2 ** tentativa
            mensagem_erro = str(erro)

        if tentativa == MAX_TENTATIVAS - 1:
            raise RuntimeError(
                f"Falha após {MAX_TENTATIVAS} tentativas: "
                f"{url}. Motivo: {mensagem_erro}"
            )

        print(
            f"Tentativa {tentativa + 1} falhou. "
            f"Nova tentativa em {espera} segundos."
        )

        time.sleep(min(espera, 60))

    raise RuntimeError(f"Não foi possível consultar: {url}")


def consultar_concurso(numero: int | None = None) -> dict:
    """Consulta o último concurso ou um número específico."""

    if numero is None:
        url = URL_API
    else:
        if numero < 1:
            raise ValueError("Número de concurso inválido.")

        url = f"{URL_API}{numero}"

    return requisitar_json(url)


# ============================================================
# CONVERSÃO E VALIDAÇÃO
# ============================================================

def converter_data(valor: str) -> str:
    """Normaliza datas para YYYY-MM-DD."""

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
            pass

    raise ValueError(f"Data inválida: {valor}")


def converter_resultado_api(dados: dict) -> dict:
    """Converte a resposta da CAIXA para um registro CSV."""

    try:
        concurso = int(dados["numero"])
        data = converter_data(dados["dataApuracao"])

        dezenas = [
            int(valor)
            for valor in dados["listaDezenas"]
        ]

    except (KeyError, TypeError, ValueError) as erro:
        raise ValueError(
            f"Resposta da CAIXA em formato inesperado: {erro}"
        ) from erro

    if concurso < 1:
        raise ValueError("Número de concurso inválido.")

    if len(dezenas) != 15:
        raise ValueError(
            f"Concurso {concurso}: quantidade diferente de 15 dezenas."
        )

    if len(set(dezenas)) != 15:
        raise ValueError(
            f"Concurso {concurso}: existem dezenas repetidas."
        )

    if any(numero < 1 or numero > 25 for numero in dezenas):
        raise ValueError(
            f"Concurso {concurso}: dezena fora do intervalo de 1 a 25."
        )

    registro = {
        "concurso": concurso,
        "data": data,
    }

    for indice, dezena in enumerate(sorted(dezenas), start=1):
        registro[f"bola{indice}"] = dezena

    return registro


def validar_registro(registro: dict) -> dict:
    """Valida um registro já existente ou recebido da API."""

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

    if any(numero < 1 or numero > 25 for numero in dezenas):
        raise ValueError(
            f"Concurso {concurso}: dezenas fora do intervalo."
        )

    resultado = {
        "concurso": concurso,
        "data": data,
    }

    for indice, dezena in enumerate(sorted(dezenas), start=1):
        resultado[f"bola{indice}"] = dezena

    return resultado


def validar_historico(registros: list[dict]) -> list[dict]:
    """Verifica duplicidades e continuidade dos concursos."""

    resultado = [
        validar_registro(registro)
        for registro in registros
    ]

    resultado.sort(key=lambda item: item["concurso"])

    numeros = [
        registro["concurso"]
        for registro in resultado
    ]

    if len(numeros) != len(set(numeros)):
        raise ValueError("O histórico contém concursos duplicados.")

    for anterior, atual in zip(numeros, numeros[1:]):
        if atual != anterior + 1:
            raise ValueError(
                f"Sequência interrompida entre "
                f"os concursos {anterior} e {atual}."
            )

    return resultado


# ============================================================
# LEITURA DO CSV
# ============================================================

def ler_historico() -> list[dict]:
    """Lê e valida o CSV sem modificá-lo."""

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

        if not set(COLUNAS).issubset(nomes):
            raise ValueError(
                "O CSV não possui todas as colunas obrigatórias."
            )

        for linha in leitor:
            normalizada = {
                str(chave).strip().lower(): valor
                for chave, valor in linha.items()
                if chave is not None
            }

            registros.append(validar_registro(normalizada))

    return validar_historico(registros)


# ============================================================
# GRAVAÇÃO ATÔMICA
# ============================================================

def gravar_atomicamente(registros: list[dict]) -> None:
    """
    Grava em arquivo temporário e substitui o CSV original
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

        # Tenta sincronizar também o diretório.
        try:
            descritor = os.open(
                ARQUIVO_CSV.parent,
                os.O_RDONLY,
            )
            try:
                os.fsync(descritor)
            finally:
                os.close(descritor)
        except OSError:
            pass

    finally:
        if (
            arquivo_temporario is not None
            and arquivo_temporario.exists()
        ):
            arquivo_temporario.unlink()


# ============================================================
# ATUALIZAÇÃO INCREMENTAL
# ============================================================

def atualizar_historico() -> dict:
    """
    Mantém os últimos 100 concursos da Lotofácil.

    Primeira execução:
        Consulta individualmente os últimos 100 concursos.

    Execuções seguintes:
        Consulta concursos ausentes na janela e reconsulta
        o concurso mais recente para detectar retificações.

    Não grava o CSV quando os dados finais não mudaram.
    """

    print("Consultando o último concurso da CAIXA...")

    dados_ultimo = consultar_concurso()
    registro_ultimo = converter_resultado_api(dados_ultimo)

    numero_atual = registro_ultimo["concurso"]

    primeiro_concurso = max(
        1,
        numero_atual - TOTAL_CONCURSOS + 1,
    )

    anterior = ler_historico()

    mapa_anterior = {
        registro["concurso"]: registro
        for registro in anterior
    }

    if mapa_anterior:
        maior_local = max(mapa_anterior)

        if maior_local > numero_atual:
            raise ValueError(
                "O CSV contém um concurso posterior ao informado pela CAIXA."
            )

    mapa_final = {
        numero: registro
        for numero, registro in mapa_anterior.items()
        if primeiro_concurso <= numero <= numero_atual
    }

    novos_concursos = 0
    consultas_individuais = 0

    total_esperado = numero_atual - primeiro_concurso + 1

    print(
        f"Janela desejada: concursos "
        f"{primeiro_concurso} a {numero_atual}."
    )

    for numero in range(primeiro_concurso, numero_atual + 1):

        # O concurso mais recente sempre é consultado novamente.
        if numero == numero_atual:
            dados = dados_ultimo

        elif numero not in mapa_final:
            dados = consultar_concurso(numero)

        else:
            continue

        registro = converter_resultado_api(dados)

        if registro["concurso"] != numero:
            raise ValueError(
                f"Foi solicitado o concurso {numero}, "
                f"mas a CAIXA retornou {registro['concurso']}."
            )

        if numero not in mapa_anterior:
            novos_concursos += 1

        mapa_final[numero] = registro
        consultas_individuais += 1

        if consultas_individuais % 10 == 0:
            print(
                f"Consultas concluídas: {consultas_individuais}"
            )

    resultado = sorted(
        mapa_final.values(),
        key=lambda item: item["concurso"],
    )

    resultado = validar_historico(resultado)

    if len(resultado) != total_esperado:
        raise ValueError(
            f"Histórico incompleto: esperados {total_esperado}, "
            f"recebidos {len(resultado)}."
        )

    resultado = resultado[-TOTAL_CONCURSOS:]

    alterado = resultado != anterior

    if alterado:
        gravar_atomicamente(resultado)
        print("CSV gravado e atualizado.")
    else:
        print("Nenhuma alteração encontrada. CSV preservado.")

    return {
        "arquivo": str(ARQUIVO_CSV),
        "primeiro_concurso": resultado[0]["concurso"],
        "ultimo_concurso": resultado[-1]["concurso"],
        "total_concursos": len(resultado),
        "novos_concursos": novos_concursos,
        "consultas_individuais": consultas_individuais,
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
        print("\nFALHA NA ATUALIZAÇÃO")
        print(f"Motivo: {erro}")
        print("O CSV anterior foi preservado.")
        raise
