from typing import Any, Dict, List

def validar_dezena(valor: Any) -> int:
    """Valida se o valor é estritamente um inteiro válido (1 a 25 para Lotofácil).
    
    Rejeita explicitamente booleanos (já que bool é subclasse de int em Python)
    e números de ponto flutuante.
    """
    if type(valor) is not int or isinstance(valor, bool):
        raise ValueError(f"Dezena inválida (tipo incorreto): {valor} (tipo: {type(valor).__name__})")
    
    if not (1 <= valor <= 25):
        raise ValueError(f"Dezena fora do intervalo permitido [1, 25]: {valor}")
    
    return valor

def validar_registro(registro: Dict[str, Any]) -> Dict[str, Any]:
    """Valida um registro completo de concurso, incluindo número do concurso,
    data e as 15 dezenas obrigatórias.
    """
    # 1. Validação do Concurso
    concurso = registro.get("concurso")
    if not isinstance(concurso, int) or isinstance(concurso, bool) or concurso <= 0:
        raise ValueError(f"Número de concurso inválido: {concurso}")

    # 2. Validação das Dezenas (bola1 até bola15)
    dezenas = []
    for i in range(1, 16):
        coluna = f"bola{i}"
        if coluna not in registro:
            raise ValueError(f"Coluna obrigatória ausente: {coluna}")
        
        dezena_validada = validar_dezena(registro[coluna])
        dezenas.append(dezena_validada)

    # 3. Validação de dezenas repetidas no mesmo concurso
    if len(dezenas) != len(set(dezenas)):
        raise ValueError(f"O concurso {concurso} possui dezenas repetidas: {dezenas}")

    return registro
