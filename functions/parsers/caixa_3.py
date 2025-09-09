# Nome do arquivo: parsers/caixa_3.py
# Etapa 4: Lógica final usando re.split para máxima precisão.

import re
import sys
import fitz # PyMuPDF

# --- INFORMAÇÕES DO BANCO (extraídas do cabeçalho do PDF) ---
def get_info():
    """Retorna um dicionário com as informações da conta."""
    return {
        "AGENCIA": "03114",
        "CONTA": "000577253152-9",
        "BANK_ID": "104", # Código da Caixa Econômica Federal
        "CURRENCY": "BRL"
    }

# --- FUNÇÃO DE ANÁLISE (PARSER) - ETAPA 4 (FINAL) ---
def parse(texto_completo):
    """
    Recebe o texto extraído de um PDF da Caixa e usa uma abordagem de
    divisão por regex para extrair as transações de forma robusta.
    """
    transacoes = []
    
    # Pré-processa o texto, removendo quebras de linha que não sejam antes de uma data.
    # Isso junta linhas de uma mesma transação que foram quebradas incorretamente.
    texto_processado = re.sub(r'\n(?!\d{2}/\d{2}/\d{4})', ' ', texto_completo)
    
    # Separa o texto em blocos de transação, usando a data como delimitador.
    # O parêntese em (\d{2}/\d{2}/\d{4}) faz com que a data seja mantida na lista resultante.
    blocos = re.split(r'(\d{2}/\d{2}/\d{4})', texto_processado)
    
    # Padrão para encontrar o valor da transação e o saldo no texto do bloco.
    padrao_valores = re.compile(r'(\d{1,3}(?:\.\d{3})*,\d{2}\s[CD])\s+(\d{1,3}(?:\.\d{3})*,\d{2}\s[CD])')

    # A lista 'blocos' vem em pares: [texto antes da data, data, texto depois da data, ...].
    # Por isso, iteramos de 2 em 2, começando pelo primeiro par.
    for i in range(1, len(blocos), 2):
        data_str = blocos[i]
        texto_bloco = blocos[i+1]

        if "= Saldo do Dia" in texto_bloco:
            continue

        match_valores = padrao_valores.search(texto_bloco)
        if not match_valores:
            continue
        
        data_ofx = data_str[6:] + data_str[3:5] + data_str[:2]

        valor_str_completo = match_valores.group(1) # O valor da transação é o primeiro capturado
        partes_valor = valor_str_completo.split()
        valor_numerico_str, tipo_str = partes_valor[0], partes_valor[1]
        
        valor = float(valor_numerico_str.replace('.', '').replace(',', '.'))
        
        if tipo_str == 'D':
            valor = -abs(valor)
            tipo_ofx = "DEBIT"
        else:
            valor = abs(valor)
            tipo_ofx = "CREDIT"

        # A descrição é todo o texto do bloco que vem ANTES do padrão de valores.
        descricao = texto_bloco[:match_valores.start()].strip()
        
        transacoes.append({
            "data": data_ofx,
            "descricao": re.sub(r'\s+', ' ', descricao).strip(),
            "valor": valor,
            "tipo": tipo_ofx
        })

    return transacoes