# Nome do arquivo: sicoob.py (VERSÃO FINAL E CORRIGIDA)
# Parser com lógica de montagem para o extrato fragmentado do Sicoob.

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
    Analisa o texto bruto extraído de um extrato PDF do Sicoob e retorna uma lista de transações.
    """
    transacoes = []
    ano_extrato = None

    # 1. Encontra o ano do extrato na linha "PERÍODO"
    match_ano = re.search(r'PERÍODO: \d{2}/\d{2}/(\d{4})', texto_cru)
    if match_ano:
        ano_extrato = match_ano.group(1)
    else:
        ano_extrato = str(datetime.now().year)

    linhas = texto_cru.split('\n')
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        # 2. O início de um bloco de transação é uma linha que contém apenas uma data "dd/mm"
        match_data = re.match(r'^(\d{2}/\d{2})$', linha)
        
        if match_data:
            data_str = match_data.group(1)
            
            # Inicia a montagem da transação
            descricao_parts = []
            valor = 0.0
            tipo = ""
            
            # 3. Olha para as próximas linhas para encontrar a descrição e o valor
            j = i + 1
            while j < len(linhas):
                proxima_linha = linhas[j].strip()

                # Condição de parada: encontrou a próxima data ou um saldo, que marca o fim do bloco
                if re.match(r'^(\d{2}/\d{2})$', proxima_linha) or "SALDO DO DIA" in proxima_linha:
                    break

                # Tenta encontrar o valor na linha atual
                match_valor = re.match(r'^([\d\.]*,\d{2})([CD])$', proxima_linha)
                if match_valor:
                    valor = limpar_valor(match_valor.group(1))
                    tipo_str = match_valor.group(2)
                    tipo = "CREDIT" if tipo_str == "C" else "DEBIT"
                    if tipo == "DEBIT":
                        valor = -abs(valor)
                # Ignora linhas de documento e linhas vazias
                elif proxima_linha.startswith("DOC.:") or not proxima_linha:
                    pass
                # Se não for nada disso, é parte da descrição
                else:
                    descricao_parts.append(proxima_linha)
                
                j += 1

            # 4. Se um valor válido foi encontrado no bloco, monta e salva a transação
            if valor != 0.0:
                data_completa = f"{data_str}/{ano_extrato}"
                data_formatada = datetime.strptime(data_completa, '%d/%m/%Y').strftime('%Y%m%d')
                
                descricao_final = " ".join(descricao_parts)
                descricao_final = re.sub(r'\s+', ' ', descricao_final).strip()

                transacoes.append({
                    "data": data_formatada,
                    "descricao": descricao_final if descricao_final else "Lançamento",
                    "valor": valor,
                    "tipo": tipo
                })
            
            # Pula o índice principal para o final do bloco que acabamos de ler
            i = j - 1
        
        i += 1
            
    return transacoes