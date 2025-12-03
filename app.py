import streamlit as st
import gspread
import pandas as pd
import json

# Removemos a importação de 'oauth2client' pois ela está obsoleta
# from oauth2client.service_account import ServiceAccountCredentials 

# O cache garante que a conexão só seja feita uma vez, economizando recursos e tempo
@st.cache_resource(ttl=3600)
def get_sheets_client():
    """
    Função para estabelecer a conexão com o Google Sheets usando 
    as credenciais armazenadas no st.secrets.
    
    A chave esperada no secrets.toml é 'google_credentials', contendo o JSON inteiro.
    """
    try:
        # 1. Obtém a string JSON multi-linha da chave 'google_credentials'
        creds_json_string = st.secrets["google_credentials"]
        
        # 2. Converte a string JSON para um dicionário Python
        creds_dict = json.loads(creds_json_string)
        
        # 3. Autoriza o cliente gspread usando o dicionário de credenciais (método moderno)
        client = gspread.service_account_from_dict(creds_dict)
        return client

    except KeyError:
        st.error("Erro de Configuração: A chave 'google_credentials' não foi encontrada no Streamlit Secrets. Certifique-se de que o TOML foi copiado corretamente.")
        return None
    except Exception as e:
        st.error(f"Erro na Conexão com o Google Sheets: {e}")
        return None

# -----------------------------------------
# Conectar e obter dados da planilha
# -----------------------------------------
def conectar_planilha(client, sheet_id, aba):
    """Obtém os dados da aba especificada e retorna um DataFrame."""
    try:
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(aba)

        # Usamos get_all_records para obter os dados como uma lista de dicionários
        dados = worksheet.get_all_records()
        df = pd.DataFrame(dados)
        return df

    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Erro: A aba '{aba}' não foi encontrada na planilha.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler os dados da planilha: {e}")
        return None


# -----------------------------------------
# STREAMLIT APP
# -----------------------------------------
st.title("📊 Dashboard - Google Sheets (Cloud)")

# Planilha de destino e aba
SHEET_ID = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
ABA = "carros"

# 1. Tenta obter o cliente gspread
client = get_sheets_client()

if client:
    # 2. Se a conexão foi bem-sucedida, tenta ler a planilha
    df = conectar_planilha(client, SHEET_ID, ABA)

    if df is not None:
        st.success(f"Dados lidos com sucesso da aba '{ABA}'!")
        st.dataframe(df)

# Lembre-se de compartilhar a planilha '1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE' 
# com o email: tiquinho@sacred-highway-445119-e2.iam.gserviceaccount.com