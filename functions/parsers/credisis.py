# Nome do arquivo: credisis.py
# Módulo especialista em analisar extratos da CrediSIS. (VERSÃO FINAL 3)

import re
from datetime import datetime

# --- INFORMAÇÕES DO BANCO ---
def get_info():
    """Retorna um dicionário com as informações da conta CrediSIS."""
    # Usando dados reais do extrato, pois são mais corretos.
    # O OFX Fácil costuma usar dados genéricos, mas os reais são melhores se o seu sistema aceitar.
    return {
        "AGENCIA": "0001",
        "CONTA": "99999",
        "BANK_ID": "0999", # Código genérico para "outros bancos"
        "CURRENCY": "BRL"
    }

# --- FUNÇÃO DE ANÁLISE (PARSER) ---
def parse(texto_completo):
    """
    Recebe o texto extraído de um PDF da CrediSIS e retorna uma lista
    de dicionários, cada um representando uma transação.
    """
    transacoes = []
    linhas = texto_completo.split('\n')
    
    # Padrão para identificar uma linha que é uma data de transação (início de um bloco)
    date_pattern = re.compile(r"^\d{2}\/\d{2}\/\d{4}$")
    # Palavras-chave que indicam o fim da lista de transações
    end_of_transactions_keywords = ['Saldo final', 'Saldos em']

    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        if not linha:
            i += 1
            continue

        # A lógica agora começa diretamente procurando pela data completa
        if date_pattern.match(linha):
            bloco_candidato = []
            j = i
            # Coleta as linhas até a próxima data ou uma palavra-chave de fim
            while j < len(linhas):
                proxima_linha = linhas[j].strip()
                if (j > i and date_pattern.match(proxima_linha)) or \
                   any(proxima_linha.startswith(kw) for kw in end_of_transactions_keywords):
                    break
                
                # Adiciona apenas se a linha não for vazia
                if proxima_linha:
                    bloco_candidato.append(proxima_linha)
                j += 1
            
            # Um bloco válido tem no mínimo 4 linhas (Data, Código, Descrição, Valor, Saldo)
            if len(bloco_candidato) >= 4:
                valor_str = bloco_candidato[-2]
                saldo_str = bloco_candidato[-1]

                # Valida se o que pegamos parece ser realmente valor e saldo
                if (valor_str.upper().startswith('R$') or valor_str.upper().startswith('RS')) and \
                   (saldo_str.upper().startswith('R$') or saldo_str.upper().startswith('RS')):
                    
                    data_str = bloco_candidato[0]
                    codigo_str = bloco_candidato[1]
                    descricao_linhas = bloco_candidato[2:-2]
                    
                    data_obj = datetime.strptime(data_str, '%d/%m/%Y')
                    data_final = data_obj.strftime('%Y%m%d')

                    descricao_final = " ".join(descricao_linhas)

                    valor_limpo = valor_str.upper().replace('R$', '').replace('RS', '').replace('.', '').replace(',', '.').replace(' ', '').replace('\xa0', '').strip()
                    valor = float(valor_limpo)

                    tipo_transacao = "DEBIT" if valor < 0 else "CREDIT"

                    transacoes.append({
                        "data": data_final,
                        "descricao": re.sub(r'\s+', ' ', descricao_final).strip(),
                        "valor": valor,
                        "tipo": tipo_transacao,
                        "id": codigo_str
                    })
            
            # Avança o índice principal para depois do bloco que lemos
            i = j
            continue

        # Se a linha não é o início de um bloco, apenas avança
        i += 1
        
    return sorted(transacoes, key=lambda x: (x['data'], x['id']))