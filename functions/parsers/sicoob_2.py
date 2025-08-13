# Nome do arquivo: sicoob_2.py (VERSÃO FINAL COM LÓGICA DE BLOCOS CORRIGIDA)
# Parser para o extrato Sicoob com múltiplas linhas por transação (Modelo 2).

import re
from datetime import datetime

# Informações da conta extraídas do PDF de exemplo.
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
    Analisa o texto bruto extraído do extrato PDF do Sicoob (modelo 2).
    """
    transacoes = []
    
    # Encontra o ano do extrato na linha "PERÍODO"
    match_ano = re.search(r'PERÍODO:\s*\d{2}/\d{2}/(\d{4})', texto_cru)
    ano_extrato = match_ano.group(1) if match_ano else str(datetime.now().year)

    # Remove o cabeçalho para focar apenas nos lançamentos
    try:
        conteudo_util = re.split(r'HISTÓRICO DE MOVIMENTAÇÃO|DATA\s+DOCUMENTO\s+HISTÓRICO', texto_cru, flags=re.IGNORECASE)[1]
    except IndexError:
        conteudo_util = texto_cru

    # Divide o texto em blocos de transação, cada um começando com uma data
    blocos = re.split(r'\n(?=\d{2}/\d{2}/\d{4})', conteudo_util)

    for bloco in blocos:
        bloco_limpo = " ".join(bloco.strip().splitlines())
        
        # Ignora blocos que são apenas informativos
        if not bloco_limpo or "SALDO ANTERIOR" in bloco_limpo or "SALDO BLOQUEADO" in bloco_limpo:
            continue
        
        # Padrão para encontrar a data, a descrição principal e o valor
        padrao = r"(\d{2}/\d{2}/\d{4})\s+(?:.*?)\s+([A-ZÇÃ-Õ\.\s/-]+)\s+([\d\.]*,\d{2})([CD])"
        match = re.search(padrao, bloco_limpo)

        if match:
            try:
                data_str, descricao, valor_str, tipo_str = match.groups()
                
                data_formatada = datetime.strptime(data_str, '%d/%m/%Y').strftime('%Y%m%d')
                valor = limpar_valor(valor_str)
                tipo = "CREDIT" if tipo_str == "C" else "DEBIT"
                if tipo == "DEBIT":
                    valor = -abs(valor)

                # Limpa a descrição para remover espaços extras e garantir consistência
                descricao_final = re.sub(r'\s+', ' ', descricao).strip()

                transacoes.append({
                    "data": data_formatada,
                    "descricao": descricao_final,
                    "valor": valor,
                    "tipo": tipo
                })
            except (ValueError, IndexError):
                continue
            
    return transacoes