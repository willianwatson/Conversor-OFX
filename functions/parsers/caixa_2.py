# Nome do arquivo: caixa_2.py (VERSÃO FINAL COM HISTÓRICO LIMPO)
# Parser para o segundo modelo de extrato da Caixa Econômica Federal.

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
    Analisa o texto bruto extraído de um extrato PDF da Caixa (modelo 2).
    """
    transacoes = []
    
    # Pré-processamento: remove cabeçalhos e rodapés para focar na área de transações.
    try:
        conteudo_util = re.split(r'HISTÓRICO\s+DOCUMENTO', texto_cru, flags=re.IGNORECASE)[1]
        conteudo_util = re.split(r'SALDO DO DIA', conteudo_util, flags=re.IGNORECASE)[0]
    except IndexError:
        conteudo_util = texto_cru

    # Divide o texto em blocos que começam com uma data.
    blocos = re.split(r'\n(?=\d{2}/\d{2}/\d{4})', conteudo_util)

    for bloco in blocos:
        bloco_limpo = bloco.strip()
        
        if not bloco_limpo or "SALDO ANTERIOR" in bloco_limpo:
            continue

        linhas_bloco = [linha.strip() for linha in bloco_limpo.split('\n') if linha.strip()]
        if not linhas_bloco:
            continue
        
        try:
            data_str_match = re.match(r'(\d{2}/\d{2}/\d{4})', linhas_bloco[0])
            if not data_str_match:
                continue
            
            data_formatada = datetime.strptime(data_str_match.group(1), '%d/%m/%Y').strftime('%Y%m%d')

            texto_completo = " ".join(linhas_bloco)
            
            matches = re.findall(r'([\d\.]*,\d{2})\s*([CD])', texto_completo)
            
            if len(matches) >= 1:
                valor_str, tipo_str = matches[0]
                
                valor = limpar_valor(valor_str)
                tipo = "CREDIT" if tipo_str == "C" else "DEBIT"
                if tipo == "DEBIT":
                    valor = -abs(valor)
                
                descricao_bruta = texto_completo.split(valor_str)[0]
                
                # --- LÓGICA DE LIMPEZA DO HISTÓRICO ---
                # Remove data, horário e número de documento do início
                descricao_limpa = re.sub(r'^\d{2}/\d{2}/\d{4}\s*', '', descricao_bruta).strip()
                descricao_limpa = re.sub(r'^\d{2}:\d{2}:\d{2}\s*', '', descricao_limpa).strip()
                descricao_limpa = re.sub(r'^\d+\s*', '', descricao_limpa).strip()
                
                # Remove CPFs e CNPJs
                descricao_limpa = re.sub(r'\s*\d{3}\.\d{3}\.\d{3}-\d{2}\s*', ' ', descricao_limpa)
                descricao_limpa = re.sub(r'\s*\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\s*', ' ', descricao_limpa)
                
                # Remove espaços duplicados
                descricao_final = re.sub(r'\s+', ' ', descricao_limpa).strip()
                # ----------------------------------------

                transacoes.append({
                    "data": data_formatada,
                    "descricao": descricao_final if descricao_final else "Lançamento Caixa",
                    "valor": valor,
                    "tipo": tipo
                })
        except (ValueError, IndexError):
            continue
            
    return transacoes