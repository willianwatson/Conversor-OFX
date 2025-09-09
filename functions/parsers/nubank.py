# Nome do arquivo: functions/nubank.py
# ARQUIVO DE TESTE PARA NOVAS PALAVRAS-CHAVE

import re
import sys
import fitz # PyMuPDF

# --- INFORMAÇÕES DO BANCO ---
def get_info():
    """Retorna um dicionário com as informações da conta Nubank."""
    return {
        "AGENCIA": "0001",
        "CONTA": "64943506-8", # Conta correta do extrato
        "BANK_ID": "0260",       # Código oficial do Nubank
        "CURRENCY": "BRL"
    }

# --- FUNÇÃO DE ANÁLISE (PARSER) ---
def parse(texto_completo):
    """
    Recebe o texto extraído de um PDF do Nubank e retorna uma lista de transações.
    """
    MESES = {
        "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04", "MAI": "05", "JUN": "06",
        "JUL": "07", "AGO": "08", "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
    }

    transacoes = []
    linhas = texto_completo.split('\n')
    
    data_atual_str = None
    
    # ### CORREÇÃO AQUI ###
    # Adicionamos a nova palavra-chave encontrada no extrato.
    transaction_keywords = [
        'Transferência recebida', 'Transferência enviada', 'Compra no débito', 
        'Pagamento de fatura', 'Aplicação RDB', 'Transferência Recebida', 
        'Depósito recebido',
        'Pagamento de boleto efetuado' # <-- NOVA LINHA ADICIONADA
    ]

    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        if not linha:
            i += 1
            continue

        match_data = re.search(r"^(\d{2}) ([A-Z]{3}) (\d{4})", linha)
        if match_data:
            dia, mes_str, ano = match_data.groups()
            data_atual_str = f"{ano}{MESES.get(mes_str.upper())}{dia}"
            i += 1
            continue
        
        if linha.startswith("Total de"):
            i += 1
            continue

        if any(linha.startswith(keyword) for keyword in transaction_keywords):
            bloco_linhas = [linha]
            j = i + 1

            while j < len(linhas):
                proxima_linha = linhas[j].strip()
                is_new_transaction = any(proxima_linha.startswith(kw) for kw in transaction_keywords)

                if (re.search(r"^(\d{2}) ([A-Z]{3}) (\d{4})", proxima_linha) or
                    proxima_linha.startswith("Total de") or
                    is_new_transaction or
                    "SALDO DO DIA" in proxima_linha.upper()):
                    break
                
                if "TEM ALGUMA DÚVIDA" in proxima_linha.upper():
                    j += 1
                    continue
                
                if proxima_linha:
                    bloco_linhas.append(proxima_linha)
                j += 1
            
            texto_bloco = " ".join(bloco_linhas)
            valor_regex = re.compile(r'(\d{1,3}(?:\.\d{3})*,\d{2})')
            
            valores_encontrados = valor_regex.findall(texto_bloco)
            
            if valores_encontrados:
                valor_encontrado_str = valores_encontrados[-1]
                descricao_final = texto_bloco.replace(valor_encontrado_str, "")
                valor_encontrado = float(valor_encontrado_str.replace('.', '').replace(',', '.'))

                debit_keywords = ['Transferência enviada', 'Compra no débito', 'Pagamento de fatura', 'Aplicação RDB', 'Pagamento de boleto efetuado']
                is_debit = any(texto_bloco.startswith(kw) for kw in debit_keywords)

                if is_debit:
                    valor = -abs(valor_encontrado)
                    tipo_transacao = "DEBIT"
                else:
                    valor = abs(valor_encontrado)
                    tipo_transacao = "CREDIT"

                transacoes.append({
                    "data": data_atual_str,
                    "descricao": re.sub(r'\s+', ' ', descricao_final).strip(),
                    "valor": valor,
                    "tipo": tipo_transacao
                })
            
            i = j
            continue

        i += 1
        
    return sorted(transacoes, key=lambda x: x['data'])

# --- Bloco de Debug para Teste Local ---
if __name__ == "__main__":
    import sys
    import fitz
    
    if len(sys.argv) < 2:
        print("Uso: python functions/nubank.py <caminho_do_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text("text", sort=True)
        doc.close()
        
        parsed_data = parse(full_text)
        
        print(f"--- Encontradas {len(parsed_data)} transações ---")
        for t in parsed_data:
            print(f"Data: {t['data']}, Valor: {t['valor']:.2f}, Tipo: {t['tipo']}, Descrição: {t['descricao']}")
        print("--- Fim do Debug ---")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")