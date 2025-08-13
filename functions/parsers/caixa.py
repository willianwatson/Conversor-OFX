# Nome do arquivo: caixa.py
# Módulo especialista em analisar extratos da CAIXA. (VERSÃO CORRIGIDA)

import re
from datetime import datetime

# --- INFORMAÇÕES DO BANCO ---
def get_info():
    """Retorna um dicionário com as informações da conta CAIXA."""
    # O CÓDIGO DA CAIXA É 104
    return {
        "AGENCIA": "0001",
        "CONTA": "99999",
        "BANK_ID": "0999", # Código genérico para "outros bancos"
        "CURRENCY": "BRL"
    }

# --- FUNÇÃO DE ANÁLISE (PARSER) ---
def parse(texto_completo):
    """
    Recebe o texto extraído de um PDF da CAIXA e retorna uma lista
    de dicionários, cada um representando uma transação.
    """
    transacoes = []
    
    # Padrão para identificar uma linha que é uma data (início de um bloco)
    date_pattern = re.compile(r"^\d{2}\/\d{2}\/\d{4}$")
    # Padrão para validar uma linha de valor (ex: "73,99 C" ou "0,08 D")
    value_pattern = re.compile(r"^-?[\d\.,]+\s+[CD]$")
    # Palavras-chave em linhas que devem ser ignoradas
    ignore_keywords = ['SALDO ANTERIOR', 'SALDO DIA', 'Data Mov.']

    linhas = texto_completo.split('\n')
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        if not linha or any(keyword in linha for keyword in ignore_keywords):
            i += 1
            continue

        # Se a linha atual é uma data, encontramos um potencial início de bloco
        if date_pattern.match(linha):
            # Um bloco da Caixa parece ter 5 linhas: Data, Doc, Hist, Valor, Saldo
            if i + 4 < len(linhas):
                bloco = [linhas[j].strip() for j in range(i, i + 5)]
                
                # Extrai as partes do bloco
                data_str = bloco[0]
                doc_str = bloco[1]
                historico_str = bloco[2]
                valor_completo_str = bloco[3]
                
                # Valida se a linha de valor tem o formato esperado (ex: "1.234,56 C")
                if re.match(value_pattern, valor_completo_str):
                    try:
                        # Separa o valor do indicador C/D
                        partes_valor = valor_completo_str.split()
                        valor_str = partes_valor[0]
                        tipo_valor = partes_valor[1]

                        # Converte a data para YYYYMMDD
                        data_obj = datetime.strptime(data_str, '%d/%m/%Y')
                        data_final = data_obj.strftime('%Y%m%d')

                        # Limpa o valor para conversão
                        valor = float(valor_str.replace('.', '').replace(',', '.').strip())

                        # Define o sinal e o tipo da transação
                        if tipo_valor == 'D':
                            tipo_transacao = "DEBIT"
                            valor = -abs(valor)
                        else: # tipo_valor == 'C'
                            tipo_transacao = "CREDIT"
                            valor = abs(valor)

                        # Junta o número do documento na descrição
                        descricao_final = f"{historico_str} (Doc: {doc_str})"

                        transacoes.append({
                            "data": data_final,
                            "descricao": re.sub(r'\s+', ' ', descricao_final).strip(),
                            "valor": valor,
                            "tipo": tipo_transacao,
                            "id": doc_str
                        })
                        
                        # Se o bloco foi válido, pula as 5 linhas
                        i += 5
                        continue

                    except (ValueError, IndexError):
                        # Se algo der errado na conversão, apenas ignora o bloco e continua
                        pass
        
        # Se a linha não iniciou um bloco válido, apenas avança
        i += 1
        
    return sorted(transacoes, key=lambda x: (x['data'], x['id']))