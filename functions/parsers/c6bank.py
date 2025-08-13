# Nome do arquivo: c6bank.py
# Módulo especialista em analisar extratos do C6 Bank. (VERSÃO 4.1 - CORREÇÃO FINALÍSSIMA)

import re

# --- INFORMAÇÕES DO BANCO ---
def get_info():
    """
    Retorna um dicionário com as informações da conta.
    NOTA: Usando valores genéricos conforme o arquivo OFX de exemplo para
    garantir a compatibilidade com o software de destino.
    """
    return {
        "AGENCIA": "1",
        "CONTA": "99999999",
        "BANK_ID": "0999",
        "CURRENCY": "USD"
    }

# --- FUNÇÃO DE ANÁLISE (PARSER) ---
def parse(texto_completo):
    """
    Recebe o texto extraído de um PDF do C6 Bank e retorna uma lista
    de dicionários, cada um representando uma transação.
    """
    transacoes = []
    current_year = None
    
    linhas = texto_completo.split('\n')
    
    year_pattern = re.compile(r"^\w+\s+(\d{4})\s+\(")
    date_pattern = re.compile(r"^\d{2}\/\d{2}$")
    value_pattern = re.compile(r"^-?R\$\s?[\d\.,]+$")

    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        match_year = year_pattern.search(linha)
        if match_year:
            current_year = match_year.group(1)
            i += 1
            continue

        if not current_year:
            i += 1
            continue
            
        if date_pattern.match(linha) and i + 4 < len(linhas) and value_pattern.match(linhas[i+4].strip()):
            
            data_str = linhas[i].strip()
            tipo = linhas[i+2].strip()
            descricao = linhas[i+3].strip()
            valor_str = linhas[i+4].strip()

            dia, mes = data_str.split('/')
            data_completa = f"{current_year}{mes}{dia}"

            descricao_final = f"{tipo} {descricao}"

            # ### CORREÇÃO APLICADA AQUI ###
            # Adicionado .replace('\xa0', '') para remover o "espaço não-separável"
            valor_limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').replace(' ', '').replace('\xa0', '').strip()
            valor = float(valor_limpo)

            tipo_transacao = "DEBIT" if valor < 0 else "CREDIT"
            
            transacoes.append({
                "data": data_completa,
                "descricao": descricao_final,
                "valor": valor,
                "tipo": tipo_transacao
            })
            
            i += 5
            continue

        i += 1
        
    return sorted(transacoes, key=lambda x: x['data'])