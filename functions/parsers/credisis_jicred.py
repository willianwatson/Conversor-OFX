# Nome do arquivo: credisis_jicred.py
# Módulo especialista em analisar extratos da CrediSIS Jicred.

import re
from datetime import datetime

# --- INFORMAÇÕES DO BANCO ---
def get_info():
    """Retorna um dicionário com as informações da conta CrediSIS Jicred."""
    return {
        "AGENCIA": "0001",
        "CONTA": "99999",
        "BANK_ID": "0999", # Código genérico para "outros bancos"
        "CURRENCY": "BRL"
    }

# --- FUNÇÃO DE ANÁLISE (PARSER) ---
def parse(texto_completo):
    """
    Recebe o texto extraído de um PDF da CrediSIS Jicred e retorna uma lista
    de dicionários, cada um representando uma transação.
    """
    transacoes = []
    
    # Remove cabeçalhos e rodapés repetidos para limpar o texto
    texto_limpo = re.sub(r'Data\s+N\.Doc\.\s+Histórico.*?\n', '', texto_completo)
    texto_limpo = re.sub(r'CHEQUES ORDEM NUMÉRICA.*?\n', '', texto_limpo)
    texto_limpo = re.sub(r'Num\.\s+Data\s+Valor\n', '', texto_limpo)
    
    linhas = texto_limpo.split('\n')

    bloco_atual = []
    data_atual = None
    
    # Palavras-chave que indicam que um valor é DÉBITO
    debit_keywords = ['ENVIADO', 'BOLETO', 'DEBITO', 'DÉBITOS', 'TARIFA', 'LIQUIDACAO']

    for linha in linhas:
        linha = linha.strip()
        if not linha or "SALDO ANTERIOR" in linha:
            continue

        # Tenta encontrar uma data na linha
        match_data = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
        if match_data:
            data_atual = datetime.strptime(match_data.group(1), '%d/%m/%Y').strftime('%Y%m%d')
            # Remove a data da linha para não atrapalhar o resto da análise
            linha = linha.replace(match_data.group(1), '').strip()

        # Adiciona a linha (sem a data) ao bloco atual
        bloco_atual.append(linha)
        
        # O fim de uma transação é marcado por uma linha que termina com " C" ou " D" (o saldo)
        if linha.endswith((' C', ' D')) and re.search(r'[\d\.,]+', linha):
            
            # Se não houver data no bloco, pula (é lixo do cabeçalho/rodapé)
            if not data_atual:
                bloco_atual = []
                continue

            # O valor da transação é a penúltima linha numérica do bloco
            valores_numericos = re.findall(r'([\d\.]*,\d{2})', " ".join(bloco_atual))
            
            if len(valores_numericos) >= 2:
                valor_str = valores_numericos[-2] # Pega o penúltimo valor numérico, que é o da transação
                
                # Monta a descrição com tudo que não for os valores numéricos
                descricao_completa = []
                for item in bloco_atual:
                    # Limpa o item dos valores encontrados para formar a descrição
                    item_limpo = item
                    for val in valores_numericos:
                        item_limpo = item_limpo.replace(val, '')
                    # Remove o C/D do final e espaços extras
                    item_limpo = re.sub(r'\s+[CD]$', '', item_limpo).strip()
                    if item_limpo:
                        descricao_completa.append(item_limpo)
                
                descricao_final = " ".join(descricao_completa)
                
                valor = float(valor_str.replace('.', '').replace(',', '.'))
                
                # Determina o tipo da transação por palavras-chave
                is_debit = any(keyword in descricao_final.upper() for keyword in debit_keywords)
                
                if is_debit:
                    tipo_transacao = "DEBIT"
                    valor = -abs(valor)
                else:
                    tipo_transacao = "CREDIT"
                    valor = abs(valor)

                # Evita adicionar transações de R$ 0,00 que são apenas marcadores
                if valor != 0:
                    transacoes.append({
                        "data": data_atual,
                        "descricao": re.sub(r'\s+', ' ', descricao_final).strip(),
                        "valor": valor,
                        "tipo": tipo_transacao,
                        "id": data_atual + str(len(transacoes)) # Cria um ID único
                    })

            # Zera o bloco para a próxima transação
            bloco_atual = []
            
    return transacoes