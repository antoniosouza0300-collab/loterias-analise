from __future__ import annotations

import csv
import json
import os
import random
import re
import tempfile
import time
import urllib.error
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

URL_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_CSV = DIRETORIO_PROJETO / "data" / "lotofacil.csv"

TOTAL_CONCURSOS = 100
TOTAL_DEZENAS = 15
DEZENA_MINIMA = 1
DEZENA_MAXIMA = 25
TIMEOUT = 30
TENTATIVAS = 4
MAX_WORKERS = 5

COLUNAS = ["concurso", "data", *[f"bola{i}" for i in range(1, 16)]]


def converter_data(valor: Any) -> str:
    if valor is None or valor == "":
        return ""
    if not isinstance(valor, str):
        raise ValueError(f"Data inválida: {valor}")
    texto = valor.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    raise ValueError(f"Formato de data inválido: {valor}")


def validar_dezena(valor: Any) -> int:
    if isinstance(valor, bool):
        raise ValueError(f"Dezena inválida: {valor}")
    if type(valor) is int:
        dezena = valor
    elif isinstance(valor, str) and re.fullmatch(r"\d+", valor.strip()):
        dezena = int(valor.strip())
    else:
        raise ValueError(f"Dezena inválida: {valor}")
    if not DEZENA_MINIMA <= dezena <= DEZENA_MAXIMA:
        raise ValueError(f"Dezena fora do intervalo: {valor}")
    return dezena


def limpar_registro_para_csv(registro: Dict[str, Any]) -> Dict[str, Any]:
    return {c: registro[c] for c in COLUNAS}


def validar_registro(registro: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(registro, dict):
        raise ValueError("Registro deve ser dicionário")
    dados = dict(registro)
    if "concurso" not in dados and "numero" in dados:
        dados["concurso"] = dados["numero"]
    if "dezenas" in dados and isinstance(dados["dezenas"], list):
        for i, d in enumerate(dados["dezenas"][:15], 1):
            dados[f"bola{i}"] = d
    elif "listaDezenas" in dados and isinstance(dados["listaDezenas"], list):
        for i, d in enumerate(dados["listaDezenas"][:15], 1):
            dados[f"bola{i}"] = d
    if "data" not in dados:
        dados["data"] = dados.get("dataApuracao", "")
    concurso = dados.get("concurso")
    if type(concurso) is not int or concurso <= 0:
        raise ValueError(f"Concurso inválido: {concurso}")
    dados["data"] = converter_data(dados.get("data"))
    dezenas = []
    for i in range(1, TOTAL_DEZENAS + 1):
        col = f"bola{i}"
        if col not in dados:
            raise ValueError(f"Coluna ausente: {col}")
        dezena = validar_dezena(dados[col])
        dados[col] = dezena
        dezenas.append(dezena)
    if len(set(dezenas)) != TOTAL_DEZENAS:
        raise ValueError("Dezena repetida")
    return limpar_registro_para_csv(dados)


def converter_resultado_api(dados: Any) -> Dict[str, Any]:
    if not isinstance(dados, dict):
        raise ValueError("Resposta da API deve ser um dicionário")
    concurso = dados.get("numero") or dados.get("concurso") or dados.get("id")
    if isinstance(concurso, str) and concurso.isdigit():
        concurso = int(concurso)
    if type(concurso) is not int or concurso <= 0:
        raise ValueError("Concurso inválido na API")
    dezenas = dados.get("listaDezenas") or dados.get("dezenas") or dados.get("bolas")
    if not isinstance(dezenas, list) or len(dezenas) != 15:
        raise ValueError("Quantidade de dezenas inválida na API")
    registro = {
        "concurso": concurso,
        "data": dados.get("dataApuracao") or dados.get("data") or "",
    }
    for i, d in enumerate(dezenas, 1):
        registro[f"bola{i}"] = d
    return validar_registro(registro)


def requisitar_json(url: str) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0", "Accept": "application/json",
    })
    for tentativa in range(TENTATIVAS):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
            if not isinstance(dados, dict):
                raise ValueError("Resposta não é um dicionário JSON")
            return dados
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(f"Concurso não encontrado: {url}") from e
            if e.code not in (429, 500, 502, 503, 504):
                raise ValueError(f"Erro HTTP: {e}") from e
            if tentativa == TENTATIVAS - 1:
                raise ValueError(f"Falha HTTP após tentativas: {e}") from e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if tentativa == TENTATIVAS - 1:
                raise ValueError(f"Falha na consulta: {e}") from e
        time.sleep(min(2 ** tentativa + random.random(), 10))
    raise ValueError("Não foi possível consultar a API")


def consultar_concurso(numero: Optional[int] = None) -> Dict[str, Any]:
    if numero is not None:
        if type(numero) is not int or numero <= 0:
            raise ValueError("Número de concurso inválido")
        url = f"{URL_API}/{numero}"
    else:
        url = URL_API
    return requisitar_json(url)


def validar_historico(historico: List[Dict[str, Any]]) -> bool:
    if not isinstance(historico, list):
        raise ValueError("Histórico inválido")
    if not historico:
        return True
    numeros = [validar_registro(r)["concurso"] for r in historico]
    if len(numeros) != len(set(numeros)):
        raise ValueError("Concursos duplicados")
    numeros.sort()
    for a, b in zip(numeros, numeros[1:]):
        if b != a + 1:
            raise ValueError(f"Lacuna entre {a} e {b}")
    return True


def ler_historico(caminho: Optional[str] = None) -> List[Dict[str, Any]]:
    path = Path(caminho) if caminho else ARQUIVO_CSV
    if not path.exists():
        return []
    historico = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        if not leitor.fieldnames or any(c not in leitor.fieldnames for c in COLUNAS):
            raise ValueError("Cabeçalho sem colunas obrigatórias")
        for linha in leitor:
            try:
                reg = {"concurso": int(linha["concurso"]), "data": linha["data"]}
                for i in range(1, 16):
                    reg[f"bola{i}"] = linha[f"bola{i}"]
                historico.append(validar_registro(reg))
            except (TypeError, ValueError, KeyError) as e:
                raise ValueError(f"Registro inválido: {e}") from e
    validar_historico(historico)
    historico.sort(key=lambda x: x["concurso"])
    return historico


def gravar_historico(
    historico: List[Dict[str, Any]], caminho: Optional[str] = None
) -> None:
    path = Path(caminho) if caminho else ARQUIVO_CSV
    registros = sorted(
        [validar_registro(r) for r in historico],
        key=lambda x: x["concurso"],
    )
    validar_historico(registros)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUNAS)
            w.writeheader()
            for r in registros:
                w.writerow(limpar_registro_para_csv(r))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _buscar_concurso(numero: int) -> tuple[int, Dict[str, Any]]:
    """Worker para ThreadPool — busca um concurso com rate limit suave."""
    time.sleep(random.uniform(0.1, 0.3))
    return numero, consultar_concurso(numero)


def atualizar(
    url_api: Optional[str] = None,
    caminho: Optional[str] = None,
) -> Dict[str, Any]:
    path = Path(caminho) if caminho else ARQUIVO_CSV
    consultar = consultar_concurso

    historico_anterior = ler_historico(str(path))
    resposta_atual = consultar()
    registro_atual = converter_resultado_api(resposta_atual)
    numero_atual = registro_atual["concurso"]

    if numero_atual <= 0:
        raise ValueError("Número do concurso atual inválido")

    if historico_anterior:
        maior_local = max(r["concurso"] for r in historico_anterior)
        if maior_local > numero_atual:
            raise ValueError("CSV local está à frente da CAIXA.")

    primeiro = max(1, numero_atual - TOTAL_CONCURSOS + 1)
    existentes = {
        r["concurso"]: r for r in historico_anterior
        if primeiro <= r["concurso"] <= numero_atual
    }
    existentes[numero_atual] = registro_atual
    novos_concursos = 0

    faltantes = [n for n in range(primeiro, numero_atual) if n not in existentes]

    if faltantes:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(_buscar_concurso, n): n for n in faltantes
            }
            for future in as_completed(futures):
                numero, resposta = future.result()
                registro = converter_resultado_api(resposta)
                if registro["concurso"] != numero:
                    raise ValueError(
                        f"Erro: solicitado {numero}, retornado {registro['concurso']}"
                    )
                existentes[numero] = registro
                novos_concursos += 1

    if not any(r["concurso"] == numero_atual for r in historico_anterior):
        novos_concursos += 1

    resultado = [existentes[n] for n in range(primeiro, numero_atual + 1)]
    validar_historico(resultado)

    if resultado != historico_anterior:
        gravar_historico(resultado, str(path))

    return {
        "arquivo": str(path),
        "primeiro_concurso": resultado[0]["concurso"],
        "ultimo_concurso": resultado[-1]["concurso"],
        "total_concursos": len(resultado),
        "novos_concursos": novos_concursos,
        "consultas_api": 1 + len(faltantes),
        "arquivo_alterado": resultado != historico_anterior,
        "status": "sucesso",
    }


def atualizar_historico(caminho: Optional[str] = None) -> Dict[str, Any]:
    return atualizar(caminho=caminho)
