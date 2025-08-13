# Nome do arquivo: nubank.py
# Módulo especialista em analisar extratos do Nubank. (VERSÃO OTIMIZADA E CORRIGIDA)

import re

# --- INFORMAÇÕES DO BANCO ---
def get_info():
    """Retorna um dicionário com as informações da conta Nubank."""
    return {
        "AGENCIA": "0001",
        "CONTA": "99999",
        "BANK_ID": "0999", # Código genérico para "outros bancos"
        "CURRENCY": "BRL"
    }

# --- FUNÇÃO DE ANÁLISE (PARSER) ---
def parse(texto_completo):
    """
    Recebe o texto extraído de um PDF do Nubank pela biblioteca PyMuPDF/fitz
    e retorna uma lista de dicionários de transações.
    """
    MESES = {
        "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04", "MAI": "05", "JUN": "06",
        "JUL": "07", "AGO": "08", "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
    }

    transacoes = []
    linhas = texto_completo.split('\n')
    
    data_atual_str = None
    tipo_bloco = None # 'ENTRADA' ou 'SAIDA'

    transaction_keywords = [
        'Transferência recebida', 'Transferência enviada', 
        'Compra no débito', 'Pagamento de fatura', 'Aplicação RDB',
        'Transferência Recebida'
    ]
    value_pattern = re.compile(r"^[\d\.,]+$")

    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        # Se a linha for vazia, pula para a próxima
        if not linha:
            i += 1
            continue

        # Procura pela data
        match_data = re.search(r"^(\d{2}) ([A-Z]{3}) (\d{4})", linha)
        if match_data:
            dia, mes_str, ano = match_data.groups()
            data_atual_str = f"{ano}{MESES.get(mes_str.upper())}{dia}"
            i += 1
            continue
        
        # ### LÓGICA CORRIGIDA AQUI ###
        # Procura por linhas que definem o CONTEXTO (entrada ou saída)
        if linha.startswith("Total de entradas"):
            tipo_bloco = "ENTRADA"
            i += 1
            continue
        if linha.startswith("Total de saídas"):
            tipo_bloco = "SAIDA"
            i += 1
            continue

        # Procura pelo início de um bloco de transação
        if any(linha.startswith(keyword) for keyword in transaction_keywords):
            descricao_completa = [linha]
            j = i + 1
            valor_encontrado = None

            while j < len(linhas):
                proxima_linha = linhas[j].strip()
                if value_pattern.match(proxima_linha):
                    valor_encontrado = proxima_linha
                    j += 1
                    break
                # Se a próxima linha for uma nova data, encerra o bloco atual sem valor
                elif re.search(r"^(\d{2}) ([A-Z]{3}) (\d{4})", proxima_linha):
                    break
                else:
                    descricao_completa.append(proxima_linha)
                    j += 1
            
            if valor_encontrado:
                descricao_final = " ".join(descricao_completa)
                valor = float(valor_encontrado.replace('.', '').replace(',', '.'))
                
                # Usa o 'tipo_bloco' para definir o sinal do valor
                if tipo_bloco == 'SAIDA':
                    valor = -abs(valor)
                else:
                    valor = abs(valor)

                tipo_transacao = "DEBIT" if valor < 0 else "CREDIT"

                transacoes.append({
                    "data": data_atual_str,
                    "descricao": re.sub(r'\s+', ' ', descricao_final).strip(),
                    "valor": valor,
                    "tipo": tipo_transacao
                })
            
            i = j
            continue

        # Se não for nada de interesse, apenas avança a linha
        i += 1
        
    return sorted(transacoes, key=lambda x: x['data'])