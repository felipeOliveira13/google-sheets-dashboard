import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def conectar_planilha():
    sheet_id = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
    aba = "carros"

    try:
        # Permissões necessárias
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # Autenticação com credentials.json
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        print("✔ Credenciais carregadas com sucesso!")

        # Abrir planilha pelo ID
        sheet = client.open_by_key(sheet_id)
        print("✔ Planilha acessada!")

        # Abrir a aba específica
        worksheet = sheet.worksheet(aba)
        print(f"✔ Aba '{aba}' carregada!")

        # Obter dados
        dados = worksheet.get_all_records()

        if not dados:
            print("⚠ A aba está vazia!")
        else:
            print("✔ Dados carregados com sucesso!")

        # Converter para DataFrame
        df = pd.DataFrame(dados)
        return df

    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


# -------------------------
# TESTE
# -------------------------
df = conectar_planilha()

if df is not None:
    print("\n📊 Dados da planilha:")
    print(df)
