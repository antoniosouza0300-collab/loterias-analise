
import sys

try:
    from .atualizador import atualizar_historico
except ImportError:
    from atualizador import atualizar_historico


def main():
    print("Iniciando Análise da Lotofácil...")
    print("Atualizando os últimos 100 concursos da CAIXA...")

    try:
        resultado = atualizar_historico()

        print("\nHISTÓRICO PRONTO")
        print("-" * 40)

        for chave, valor in resultado.items():
            print(f"{chave}: {valor}")

    except Exception as erro:
        print("\nERRO NA ATUALIZAÇÃO")
        print(f"Motivo: {erro}")
        print("O CSV anterior foi preservado.")
        return 1

    print("\nInicialização concluída.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
