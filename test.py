import time
from datetime import timedelta

# 1. Transformar o DataFrame filtrado de volta no formato de dicionário que seu código já usa
itens_payload = df_filtrado.to_dict("records")

# 2. Variáveis de controle para o progresso e cálculo de tempo
total = len(itens_payload)
tempo_inicio = time.time()
atualizados = 0

print(f"\nIniciando atualização de {total} itens via Service Layer...")

# 3. O seu loop original mantido, mas iterando sobre a lista nova e limpa (apenas com diferenças)
for item in itens_payload:
    # Chamando a sua função intacta, passando as variáveis soltas
    atualizar_tabela_sap(
        cookies,
        item["ItemCode"],
        item["Price"],
        item.get(
            "PriceList", LISTA_PRECO_ID
        ),  # Usa a do dict, ou a constante se não houver no TXT
    )

    # Atualiza contador
    atualizados += 1

    # 4. Lógica do log de progresso a cada 50 itens
    if atualizados % 50 == 0 or atualizados == total:
        tempo_decorrido = time.time() - tempo_inicio
        tempo_medio = tempo_decorrido / atualizados
        itens_restantes = total - atualizados
        eta_segundos = itens_restantes * tempo_medio

        eta_formatado = str(timedelta(seconds=int(eta_segundos)))
        print(f"[{atualizados}/{total}] Atualizados... ETA Restante: {eta_formatado}")

print(f"\nConcluído! {atualizados} itens foram atualizados com sucesso.")
