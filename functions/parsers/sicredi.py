# Nome do arquivo: sicredi.py
# Módulo especialista em analisar extratos do Sicredi (VERSÃO OTIMIZADA)

import re
from datetime import datetime

# --- INFORMAÇÕES DO BANCO ---
def get_info():
    """Retorna um dicionário com as informações da conta Sicredi."""
    # O CÓDIGO DO BANCO SICREDI É 748
    return {
        "AGENCIA": "0001",
        "CONTA": "99999",
        "BANK_ID": "0999", # Código genérico para "outros bancos"
        "CURRENCY": "BRL"
    }

# --- FUNÇÃO DE ANÁLISE (PARSER) ---
def parse(texto_completo):
    """
    Recebe o texto extraído de um PDF do Sicredi e retorna uma lista
    de dicionários, cada um representando uma transação.
    """
    transacoes = []
    
    # Padrão para identificar uma linha que é uma data (início de um bloco)
    date_pattern = re.compile(r"^\d{2}\/\d{2}\/\d{4}$")
    # Palavras-chave que indicam o fim da lista de transações
    end_of_transactions_keywords = ['Sicredi Fone', 'SAC 0800']

    linhas = texto_completo.split('\n')
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        if not linha:
            i += 1
            continue

        # Se a linha atual é uma data, encontramos um potencial início de bloco
        if date_pattern.match(linha):
            bloco_candidato = []
            j = i
            # Coleta as linhas até a próxima data ou uma palavra-chave de fim
            while j < len(linhas):
                proxima_linha = linhas[j].strip()
                if (j > i and date_pattern.match(proxima_linha)) or \
                   any(kw in proxima_linha for kw in end_of_transactions_keywords):
                    break
                
                if proxima_linha:
                    bloco_candidato.append(proxima_linha)
                j += 1
            
            # Um bloco válido tem no mínimo 3 linhas (Data, Descrição, Valor, Saldo)
            # O valor é a penúltima linha, o saldo é a última
            if len(bloco_candidato) >= 3:
                # Tenta extrair valor e saldo das duas últimas linhas
                try:
                    valor_str = bloco_candidato[-2]
                    saldo_str = bloco_candidato[-1]

                    # Limpa os valores para verificar se são números
                    valor_limpo_check = valor_str.replace('.', '').replace(',', '').replace('-', '').strip()
                    saldo_limpo_check = saldo_str.replace('.', '').replace(',', '').replace('-', '').strip()

                    # Se ambos forem numéricos, processa o bloco
                    if valor_limpo_check.isdigit() and saldo_limpo_check.isdigit():
                        data_str = bloco_candidato[0]
                        descricao_linhas = bloco_candidato[1:-2]
                        
                        data_obj = datetime.strptime(data_str, '%d/%m/%Y')
                        data_final = data_obj.strftime('%Y%m%d')

                        descricao_final = " ".join(descricao_linhas)

                        valor_limpo = valor_str.replace('.', '').replace(',', '.').strip()
                        valor = float(valor_limpo)

                        tipo_transacao = "DEBIT" if valor < 0 else "CREDIT"

                        transacoes.append({
                            "data": data_final,
                            "descricao": re.sub(r'\s+', ' ', descricao_final).strip(),
                            "valor": valor,
                            "tipo": tipo_transacao
                        })
                except (ValueError, IndexError):
                    # Ignora blocos que não se encaixam no padrão
                    pass
            
            i = j
            continue

        i += 1
        
    return sorted(transacoes, key=lambda x: x['data'])