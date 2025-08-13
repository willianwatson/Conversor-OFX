# Nome do arquivo: infinitepay.py (VERSÃO FINAL COM HISTÓRICO COMPLETO)
# Parser com lógica ajustada para o formato de extrato da InfinitePay.

import re
from datetime import datetime

# InfinitePay é uma instituição de pagamento (CloudWalk) e seu código é 301.
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
    """Converte o valor do formato '+91,04' ou '-59,79' para um float."""
    if not texto_valor:
        return 0.0
    # Remove o sinal de '+' para consistência e substitui a vírgula por ponto
    return float(texto_valor.replace('+', '').replace('.', '').replace(',', '.'))

def parse(texto_cru):
    """
    Analisa o texto bruto extraído de um extrato PDF da InfinitePay e retorna uma lista de transações.
    """
    transacoes = []
    data_atual = None
    
    # Buffer para construir a descrição de uma transação através de múltiplas linhas
    buffer_descricao = []

    linhas = texto_cru.split('\n')
    
    padroes_ignorar = [
        re.compile(r'^Relatório de movimentações'),
        re.compile(r'^Período de'),
        re.compile(r'^CLOSET PIMENTEL'),
        re.compile(r'^Data\s+Tipo de transação'),
        re.compile(r'^Nossa equipe de atendimento'),
        re.compile(r'^Também estamos (à|a) disposição'),
        re.compile(r'^\s*$'),
    ]

    for i, linha in enumerate(linhas):
        linha_strip = linha.strip()
        if not linha_strip or any(p.match(linha_strip) for p in padroes_ignorar):
            continue

        # Lógica para encontrar a data na linha anterior à linha "Saldo do dia"
        if "Saldo do dia" in linha_strip and i > 0:
            linha_anterior = linhas[i-1].strip()
            match_data = re.match(r'^(\d{2}/\d{2}/\d{4})$', linha_anterior)
            if match_data:
                data_atual = datetime.strptime(match_data.group(1), '%d/%m/%Y').strftime('%Y%m%d')
                buffer_descricao = [] # Limpa o buffer para o novo dia
                continue

        if not data_atual:
            continue

        # Verifica se a linha ATUAL é um valor. Isso marca o fim de uma transação.
        match_valor = re.match(r'^([+\-][\d\.]*,\d{2})$', linha_strip)
        if match_valor:
            try:
                # Se temos uma descrição no buffer, este valor pertence a ela.
                if buffer_descricao:
                    valor_str = match_valor.group(1)
                    valor = limpar_valor(valor_str)
                    tipo = "CREDIT" if valor > 0 else "DEBIT"
                    
                    # Junta as partes da descrição que foram acumuladas
                    descricao = " ".join(buffer_descricao)
                    descricao = re.sub(r'\s+', ' ', descricao)

                    transacoes.append({
                        "data": data_atual,
                        "descricao": descricao,
                        "valor": valor,
                        "tipo": tipo
                    })
                    
                    # Limpa o buffer para a próxima transação
                    buffer_descricao = []
            except (ValueError, IndexError):
                buffer_descricao = [] # Limpa em caso de erro
                continue
        else:
            # Se não for um valor, é parte da descrição. Adiciona ao buffer.
            buffer_descricao.append(linha_strip)
                
    # O extrato da InfinitePay vem com as datas em ordem decrescente.
    # O formato OFX geralmente espera a ordem crescente, então invertemos a lista no final.
    return transacoes[::-1]