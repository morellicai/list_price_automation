import csv
from pathlib import Path

import urllib3

urllib3.disable_warnings()
tab18 = Path("./src/TAB18.txt")


def limpar_preco(valor_str: str) -> float | None:
    """Converte 'R$ 28,87' para float (28.87).

    Retorna None se o valor for inválido (ex: '#N/D', '#VALOR!').
    """
    texto_limpo = (
        valor_str.replace("R$", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )
    try:
        return float(texto_limpo)
    except ValueError:
        return None


# Lista para armazenar os itens processados para o payload
itens_payload = []
itens_invalidos = []
with open(tab18, mode="r", encoding="utf-16") as f:
    # O DictReader utiliza a 1ª linha como chave de cada coluna automaticamente
    leitor = csv.DictReader(f, delimiter="\t")
    for linha in leitor:
        item_code = linha.get("Nº do item", "").strip()
        preco_bruto = linha.get("Preço unitário", "").strip()
        if not item_code:
            continue
        preco_unitario = limpar_preco(preco_bruto)
        # Trata itens com erro no Excel (#N/D ou #VALOR!)
        if preco_unitario is None:
            itens_invalidos.append(
                {"ItemCode": item_code, "PrecoOriginal": preco_bruto}
            )
            continue
        # Estrutura pronta para o payload
        item_data = {
            "ItemCode": item_code,
            "Price": preco_unitario,  # ou preco_bruto caso a API espere a string original
        }
        itens_payload.append(item_data)
print(f"Total de itens válidos processados: {len(itens_payload)}")
print(f"Total de itens com erro de fórmula (#N/D, #VALOR!): {len(itens_invalidos)}")
