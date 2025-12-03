import streamlit as st
import gspread
import pandas as pd
from gspread.service_account import ServiceAccountCredentials

# NOTA: O Streamlit Cloud injeta as credenciais do secrets.toml em st.secrets["google"]
# Certifique-se de que o arquivo .streamlit/secrets.toml está correto!

# -----------------------------------------
# Configurações da Planilha
# -----------------------------------------
SHEET_ID = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
ABA = "carros"

# -----------------------------------------
# Conectar à planilha
# -----------------------------------------
@st.cache_data(ttl=600)  # Armazena os dados em cache por 10 minutos para performance
def conectar_planilha(sheet_id, aba):
    """Função para autenticar e carregar o DataFrame da planilha."""
    try:
        # 1. Autenticação usando o dicionário de segredos "google"
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
        st.error(f"Erro ao conectar ou carregar dados: {e}")
        st.info("Verifique se as credenciais em '.streamlit/secrets.toml' e o compartilhamento da planilha estão corretos.")
        return None


# -----------------------------------------
# STREAMLIT APP PRINCIPAL
# -----------------------------------------
st.title("📊 Dashboard - Google Sheets (Cloud)")

df = conectar_planilha(SHEET_ID, ABA)

if df is not None and not df.empty:
    
    # ⚠️ IMPORTANTE: Ajuste os nomes das colunas ('Modelo' e 'Ano')
    # se o cabeçalho da sua planilha for diferente!
    COL_MODELO = 'Modelo' 
    COL_ANO = 'Ano'
    
    # Verifica se as colunas necessárias existem no DataFrame
    if COL_MODELO not in df.columns or COL_ANO not in df.columns:
        st.error(f"As colunas '{COL_MODELO}' ou '{COL_ANO}' não foram encontradas na planilha. Verifique os nomes das colunas.")
    else:
        
        # 1. SIDEBAR (FILTROS)
        st.sidebar.header("⚙️ Selecione os Filtros")
        
        # --- FILTRO MODELO ---
        # Adiciona a opção "Todos" e ordena os modelos
        modelos_unicos = sorted(df[COL_MODELO].unique())
        lista_modelos = ["Todos"] + modelos_unicos
        selected_model = st.sidebar.selectbox("Modelo do Carro:", lista_modelos)

        # --- FILTRO ANO ---
        # Converte o ano para string antes de adicionar "Todos" e ordena em ordem decrescente
        anos_unicos = sorted([str(a) for a in df[COL_ANO].unique()], reverse=True)
        lista_anos = ["Todos"] + anos_unicos
        selected_year = st.sidebar.selectbox("Ano de Fabricação:", lista_anos)

        # 2. APLICAR FILTROS
        df_filtrado = df.copy()

        # Filtrar por Modelo
        if selected_model != "Todos":
            df_filtrado = df_filtrado[df_filtrado[COL_MODELO] == selected_model]

        # Filtrar por Ano
        if selected_year != "Todos":
            # Converte a coluna Ano para string para garantir a comparação correta
            df_filtrado = df_filtrado[df_filtrado[COL_ANO].astype(str) == selected_year]
        
        # 3. EXIBIR RESULTADOS
        
        # Exibe o número de registros encontrados
        st.subheader(f"Dados Filtrados ({len(df_filtrado)} registros)")
        
        if df_filtrado.empty:
            st.info("Nenhum registro encontrado com os filtros selecionados.")
        else:
            st.dataframe(df_filtrado, use_container_width=True)

st.caption("Verifique o arquivo '.streamlit/secrets.toml' para as credenciais.")