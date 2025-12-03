import streamlit as st
import gspread
import pandas as pd

# -----------------------------------------
# Carregar dados da Planilha
# -----------------------------------------

# Nome da aba (WORKSHEET) e ID da Planilha (SHEET_ID)
SHEET_ID = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
ABA = "carros"

@st.cache_data(ttl=600)  # Armazena os dados em cache por 10 minutos para performance
def conectar_planilha(sheet_id, aba):
    try:
        # 1. Autenticação usando o dicionário de segredos "google"
        # O gspread lê o JSON formatado diretamente do st.secrets["google"]
        gc = gspread.service_account_from_dict(st.secrets["google"])

        # 2. Abrir a planilha
        sheet = gc.open_by_key(sheet_id)
        
        # 3. Selecionar a aba (worksheet)
        worksheet = sheet.worksheet(aba)

        # 4. Obter todos os registros (converte a primeira linha em cabeçalhos de coluna)
        dados = worksheet.get_all_records()
        
        # 5. Converter para DataFrame
        df = pd.DataFrame(dados)
        
        return df

    except Exception as e:
        # Se houver um erro de credencial, exibirá a mensagem de erro.
        # Certifique-se de que o e-mail da Conta de Serviço (tiquinho@...) 
        # está compartilhado na planilha do Google Sheets.
        st.error(f"Erro ao conectar ou carregar dados: {e}")
        return None


# -----------------------------------------
# STREAMLIT APP
# -----------------------------------------
st.title("📊 Dashboard - Google Sheets (Cloud)")

df = conectar_planilha(SHEET_ID, ABA)

if df is not None:
    st.subheader(f"Dados da aba '{ABA}'")
    st.dataframe(df)

st.caption("Verifique o arquivo '.streamlit/secrets.toml' para as credenciais.")