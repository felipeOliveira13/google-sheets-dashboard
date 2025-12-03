import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json

# -----------------------------------------
# Carregar credenciais do Streamlit Secrets
# -----------------------------------------
def get_credentials():
    creds_json = st.secrets["google"]["credentials"]
    creds_dict = json.loads(creds_json)

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return creds


# -----------------------------------------
# Conectar à planilha
# -----------------------------------------
def conectar_planilha(sheet_id, aba):
    try:
        creds = get_credentials()
        client = gspread.authorize(creds)

        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(aba)

        dados = worksheet.get_all_records()
        df = pd.DataFrame(dados)
        return df

    except Exception as e:
        st.error(f"Erro: {e}")
        return None


# -----------------------------------------
# STREAMLIT APP
# -----------------------------------------
st.title("📊 Dashboard - Google Sheets (Cloud)")

SHEET_ID = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
ABA = "carros"

df = conectar_planilha(SHEET_ID, ABA)

if df is not None:
    st.dataframe(df)
