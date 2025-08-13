# Nome do arquivo: bancodobrasil.py (VERSÃO FINAL COM HISTÓRICO CORRIGIDO)
# Parser com lógica robusta para o formato de extrato do Banco do Brasil.

import re
from datetime import datetime

# Informações genéricas para maior compatibilidade e privacidade.
INFO = {
    "AGENCIA": "0001",
    "CONTA": "99999",
    "BANK_ID": "0999", # Código genérico para "outros bancos"
    "CURRENCY": "BRL"
}

def get_info():
    """Retorna as informações estáticas da conta e do banco."""
    return INFO

def limpar_valor(texto_valor):
    """Converte o valor do formato '1.234,56' para um float."""
    if not texto_valor:
        return 0.0
    return float(texto_valor.replace('.', '').replace(',', '.'))

def parse(texto_cru):
    """
    Analisa o texto bruto extraído de um extrato PDF do Banco do Brasil e retorna uma lista de transações.
    """
    transacoes = []
    
    try:
        # Isola a área de lançamentos para maior precisão
        conteudo_util = texto_cru.split("Lançamentos")[1].split("OBSERVAÇÕES:")[0]
    except IndexError:
        conteudo_util = texto_cru

    # Divide o extrato em blocos, onde cada bloco começa com uma data
    blocos = re.split(r'\n(?=\d{2}/\d{2}/\d{4})', conteudo_util)

    for bloco in blocos:
        bloco_limpo = bloco.strip()
        if not bloco_limpo:
            continue
        
        try:
            # A primeira palavra do bloco deve ser a data
            data_str = bloco_limpo.split()[0]
            data_formatada = datetime.strptime(data_str, '%d/%m/%Y').strftime('%Y%m%d')
        except (ValueError, IndexError):
            # Ignora blocos que não começam com uma data válida
            continue
            
        descricao = "Lançamento não identificado"
        valor = 0.0
        tipo = ""

        # Junta todas as linhas do bloco para facilitar a busca
        texto_bloco_completo = " ".join(bloco_limpo.split('\n'))
        texto_bloco_completo = re.sub(r'\s+', ' ', texto_bloco_completo)

        # 1. Encontra a descrição (Histórico) com uma regex mais específica
        match_desc = re.search(r'\d{3}\s+[A-Za-zÀ-ú][\w\s-]+', texto_bloco_completo)
        if match_desc:
            # Pega a descrição encontrada e a limpa de possíveis partes indesejadas que vêm depois
            descricao_bruta = match_desc.group(0)
            descricao = re.split(r'\s{2,}|(?=\s\d{3,}\.\d{3,})', descricao_bruta)[0].strip()

        # 2. Encontra o valor e o tipo (Crédito/Débito)
        match_valor = re.search(r'([\d\.]*,\d{2})\s+([CD])', texto_bloco_completo)
        if match_valor:
            valor = limpar_valor(match_valor.group(1))
            tipo_str = match_valor.group(2)
            
            tipo = "CREDIT" if tipo_str == "C" else "DEBIT"
            if tipo == "DEBIT":
                valor = -abs(valor)
        
        # Adiciona a transação apenas se um valor válido foi encontrado
        if valor != 0.0:
            transacoes.append({
                "data": data_formatada,
                "descricao": descricao,
                "valor": valor,
                "tipo": tipo
            })
            
    return transacoes