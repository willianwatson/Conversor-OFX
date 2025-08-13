# Nome do arquivo: inter.py (VERSÃO FINAL E CORRIGIDA)
# Parser para o extrato em PDF do Banco Inter.

import re
from datetime import datetime
import locale

# Configura o locale para Português para poder traduzir os nomes dos meses
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except locale.Error:
        print("Aviso: Locale 'pt_BR' não encontrado. Nomes de meses podem não ser reconhecidos.")

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
    """Converte o valor do formato '-R$ 1.234,56' para um float."""
    if not texto_valor:
        return 0.0
    # Remove "R$", espaços, e o ponto de milhar, substituindo a vírgula por ponto decimal.
    valor_limpo = texto_valor.replace('R$', '').replace('.', '').replace(',', '.').replace(' ', '')
    return float(valor_limpo)

def parse(texto_cru):
    """
    Analisa o texto bruto extraído de um extrato PDF do Banco Inter.
    """
    transacoes = []
    data_atual = None
    
    linhas = texto_cru.split('\n')
    
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        # Procura por uma linha de data para definir o contexto do dia
        match_data = re.match(r'^(\d{1,2} de [A-Za-zç]+ de \d{4})', linha)
        if match_data:
            try:
                data_atual = datetime.strptime(match_data.group(1), '%d de %B de %Y').strftime('%Y%m%d')
            except ValueError:
                i += 1
                continue
        
        # Se temos uma data, procuramos por uma transação
        if data_atual:
            # Garante que não vai dar erro se for a última transação do arquivo
            descricao = linhas[i].strip()
            linha_valor = linhas[i+1].strip() if i+1 < len(linhas) else ''
            linha_saldo = linhas[i+2].strip() if i+2 < len(linhas) else ''

            # Garante que só fique o valor monetário mesmo que tenha texto extra (ex: rodapé)
            if "R$" in linha_valor:
                m_valor = re.search(r'-?R\$\s*[\d\.]*,\d{2}', linha_valor)
                linha_valor = m_valor.group(0) if m_valor else ''
            else:
                linha_valor = ''

            if "R$" in linha_saldo:
                m_saldo = re.search(r'-?R\$\s*[\d\.]*,\d{2}', linha_saldo)
                linha_saldo = m_saldo.group(0) if m_saldo else ''
            else:
                linha_saldo = ''

            # Regex corrigida para encontrar o valor (com o '$' escapado)
            match_valor = re.match(r'^(-?R\$\s*[\d\.]*,\d{2})$', linha_valor)
            match_saldo = re.match(r'^(-?R\$\s*[\d\.]*,\d{2})$', linha_saldo)

            if match_valor and match_saldo:
                try:
                    valor = limpar_valor(match_valor.group(1))
                    tipo = "CREDIT" if valor >= 0 else "DEBIT"
                    if tipo == "DEBIT":
                        valor = -abs(valor)

                    transacoes.append({
                        "data": data_atual,
                        "descricao": descricao,
                        "valor": valor,
                        "tipo": tipo
                    })

                    # Pula as 2 linhas que já processamos (valor e saldo)
                    i += 2
                except (ValueError, IndexError):
                    pass
        
        i += 1
            
    return transacoes