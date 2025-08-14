# Nome do arquivo: main.py
# Adaptado para rodar como uma Google Cloud Function para o Firebase.

import importlib
from datetime import datetime
from flask import Flask, request, make_response, jsonify
from flask_cors import CORS # Essencial para a comunicação entre site e função
import fitz
from unidecode import unidecode

# --- CONFIGURAÇÕES DE SEGURANÇA ---
# 1. Chave de API Secreta: Apenas requisições com esta chave serão aceitas.
#    Troque por uma chave longa e segura de sua preferência.
SECRET_API_KEY = "pdf-ofxnFfrTShSn3xA8mF59KcILP7CyIj602AgWwn71Z078lDH3i0XFKqykfMnYsRn8j1Jj6LjJZ7cgy0TtkSO42pqo9Il7Jb7KBaNyjrtAf0ALDOF9lgmqEOzG6tcp"

# 2. Limite de Tamanho do Arquivo (em bytes)
#    10 * 1024 * 1024 = 10 Megabytes. É um limite generoso para PDFs de extrato.
MAX_FILE_SIZE = 10 * 1024 * 1024
# ------------------------------------


# Inicializa a aplicação Flask
app = Flask(__name__)
# Habilita o CORS para permitir que seu site chame esta função
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE # Aplica o limite de tamanho do arquivo
CORS(app)

def gerar_ofx_string(transacoes, info_conta):
    """Gera o conteúdo do arquivo OFX como uma string de texto."""
    if not transacoes:
        return None
    
    # Usando informações genéricas para privacidade e compatibilidade
    info_conta_generica = {
        "AGENCIA": "0001", "CONTA": "99999", "BANK_ID": "0999", "CURRENCY": "BRL"
    }
    
    ofx_content = f"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE
<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS><DTSERVER>{datetime.now().strftime('%Y%m%d%H%M%S')}</DTSERVER><LANGUAGE>POR</LANGUAGE></SONRS></SIGNONMSGSRSV1><BANKMSGSRSV1><STMTTRNRS><TRNUID>1</TRNUID><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS><STMTRS><CURDEF>{info_conta_generica['CURRENCY']}</CURDEF><BANKACCTFROM><BANKID>{info_conta_generica['BANK_ID']}</BANKID><BRANCHID>{info_conta_generica['AGENCIA']}</BRANCHID><ACCTID>{info_conta_generica['CONTA']}</ACCTID><ACCTTYPE>CHECKING</ACCTTYPE></BANKACCTFROM><BANKTRANLIST><DTSTART>{transacoes[0]['data']}</DTSTART><DTEND>{transacoes[-1]['data']}</DTEND>"""
    fitid_counters = {}
    for t in transacoes:
        data_transacao = t['data']
        if data_transacao not in fitid_counters: fitid_counters[data_transacao] = 0
        fitid_counters[data_transacao] += 1
        fitid = f"{data_transacao}{fitid_counters[data_transacao]:02d}"

        descricao_original = t['descricao']
        descricao_normalizada = unidecode(descricao_original.upper())
        descricao_final = (descricao_normalizada[:250] + '...') if len(descricao_normalizada) > 255 else descricao_normalizada
        
        ofx_content += f"""<STMTTRN><TRNTYPE>{t['tipo']}</TRNTYPE><DTPOSTED>{t['data']}</DTPOSTED><TRNAMT>{t['valor']:.2f}</TRNAMT><FITID>{fitid}</FITID><CHECKNUM>{fitid}</CHECKNUM><MEMO>{descricao_final}</MEMO></STMTTRN>"""
    
    ofx_content += """</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"""
    return ofx_content

# A rota /converter agora é a rota principal da nossa função
@app.route('/', methods=['POST'])
def converter():
    # --- VERIFICAÇÃO DE SEGURANÇA ---
    # Verifica se a chave de API foi enviada no cabeçalho da requisição
    if request.headers.get('X-API-KEY') != SECRET_API_KEY:
        return jsonify({'success': False, 'message': 'Acesso não autorizado.'}), 401 # 401 Unauthorized
    # --------------------------------

    banco_selecionado = request.form.get('banco')
    arquivo_pdf = request.files.get('arquivo_pdf')

    if not banco_selecionado or not arquivo_pdf:
        return jsonify({'success': False, 'message': 'Erro: Banco ou arquivo PDF não selecionado.'}), 400

    try:
        parser_modulo = importlib.import_module(f"parsers.{banco_selecionado}")
        
        pdf_bytes = arquivo_pdf.read()
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            texto_cru = "".join([pagina.get_text("text") + "\\n" for pagina in doc])

        info_conta = parser_modulo.get_info() # Ainda chamamos para manter a estrutura
        transacoes = parser_modulo.parse(texto_cru)

        if not transacoes:
            return jsonify({'success': False, 'message': 'Nenhuma transação foi encontrada. Verifique se o PDF não é uma imagem e se o modelo de banco selecionado está correto.'}), 400

        ofx_string = gerar_ofx_string(transacoes, info_conta)
        nome_arquivo_final = f"extrato_{banco_selecionado}_{datetime.now().strftime('%Y%m%d')}.ofx"

        response = make_response(ofx_string)
        response.headers["Content-Disposition"] = f"attachment; filename={nome_arquivo_final}"
        response.headers["Content-Type"] = "application/x-ofx"
        return response

    except ImportError:
        return jsonify({'success': False, 'message': f"Erro: O parser para o banco '{banco_selecionado}' não foi encontrado."}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f"Ocorreu um erro inesperado: {e}"}), 500