# Nome do arquivo: bradesco.py (VERSÃO CORRIGIDA)
# Parser com lógica ajustada para o formato de extrato do Bradesco.

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
    """Converte o valor do formato '1.234,56' para o formato numérico 1234.56"""
    if not texto_valor:
        return 0.0
    return float(texto_valor.replace('.', '').replace(',', '.'))

def parse(texto_cru):
    """
    Analisa o texto bruto extraído de um extrato PDF do Bradesco e retorna uma lista de transações.
    """
    transacoes = []
    data_atual = None
    descricao_buffer = []

    linhas = texto_cru.split('\n')
    
    padroes_ignorar = [
        re.compile(r'^\s*Extrato Mensal / Por Período'), re.compile(r'^\s*C LICK DA SILVA'),
        re.compile(r'^\s*Nome do usuário:'), re.compile(r'^\s*bradesco'), re.compile(r'^\s*Data da operação:'),
        re.compile(r'^\s*net empresa'), re.compile(r'^\s*Agência \| Conta'), re.compile(r'^\s*Total Disponivel'),
        re.compile(r'^\s*Extrato de:'), re.compile(r'^\s*Folha \d+/\d+'), re.compile(r'^\s*Data\s+Lançamento\s+Dcto.'),
        re.compile(r'^\s*SALDO ANTERIOR'), re.compile(r'^\s*Total\s'), re.compile(r'^\s*$'),
        re.compile(r'^\s*Os dados acima têm como base'), re.compile(r'^\s*Últimos Lançamentos'),
        re.compile(r'^\s*Saldos Invest Fácil / Plus'), re.compile(r'^\s*Data\s+Histórico\s+Valor'),
    ]

    for linha in linhas:
        linha_strip = linha.strip()
        if any(p.match(linha_strip) for p in padroes_ignorar):
            continue

        match_data = re.match(r'^(\d{2}/\d{2}/\d{4})', linha_strip)
        if match_data:
            data_atual = datetime.strptime(match_data.group(1), '%d/%m/%Y').strftime('%Y%m%d')
            conteudo = re.sub(r'^\d{2}/\d{2}/\d{4}\s*', '', linha_strip).strip()
            # Uma nova data significa uma nova transação, então limpa o buffer antigo
            descricao_buffer = [conteudo] if conteudo else []
        else:
            conteudo = linha_strip
            descricao_buffer.append(conteudo)

        if not data_atual:
            continue

        descricao_completa = " ".join(descricao_buffer).strip()
        
        # Regex mais restrita: procura por um valor monetário (com vírgula) seguido por outro
        match_valores = re.search(r'(-?[\d\.]*,\d{2})\s+(-?[\d\.]*,\d{2})$', descricao_completa)
        
        if match_valores:
            try:
                valor_str = match_valores.group(1)
                valor = limpar_valor(valor_str)
                
                if valor == 0:
                    continue
                
                tipo = "CREDIT" if valor > 0 else "DEBIT"
                
                descricao_final = descricao_completa[:match_valores.start()].strip()
                descricao_final = re.sub(r'\s+\d+$', '', descricao_final).strip()

                transacoes.append({
                    "data": data_atual,
                    "descricao": descricao_final,
                    "valor": valor,
                    "tipo": tipo
                })
                
                # Limpa o buffer pois a transação foi concluída com sucesso
                descricao_buffer = []
            except (ValueError, IndexError):
                continue
                
    return transacoes