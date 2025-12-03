import streamlit as st
import gspread
import pandas as pd

# -----------------------------------------
# Configurações da Planilha
# -----------------------------------------
SHEET_ID = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
ABA = "carros"

# -----------------------------------------
# Conectar e Carregar Planilha
# -----------------------------------------
# O TTL (Time to Live) de 60 segundos define a frequência de recarga automática.
@st.cache_data(ttl=60) 
def conectar_planilha(sheet_id, aba):
    """Função para autenticar e carregar o DataFrame da planilha."""
    try:
        # 1. Autenticação
        gc = gspread.service_account_from_dict(st.secrets["google"])

        # 2. Abrir a planilha
        sheet = gc.open_by_key(sheet_id)
        
        # 3. Selecionar a aba (worksheet)
        worksheet = sheet.worksheet(aba)

        # 4. Obter todos os registros
        dados = worksheet.get_all_records()
        
        # 5. Converter para DataFrame
        df = pd.DataFrame(dados)
        
        return df

    except Exception as e:
        st.error(f"Erro ao conectar ou carregar dados: {e}")
        st.info("Verifique a chave 'google' no Streamlit Secrets (secrets.toml).")
        return None


# -----------------------------------------
# STREAMLIT APP PRINCIPAL
# -----------------------------------------
st.title("📊 Dashboard - Google Sheets (Cloud)")

# --- Início da Barra Lateral (Sidebar) ---
st.sidebar.header("⚙️ Opções e Filtros")

# Carregamento do DataFrame
df = conectar_planilha(SHEET_ID, ABA)

if df is not None and not df.empty:
    
    # DEFINIÇÃO DOS NOMES DAS COLUNAS (Ajuste se necessário)
    COL_MODELO = 'Modelo' 
    COL_ANO = 'Ano'
    
    # --- VERIFICAÇÃO DE COLUNAS ---
    if COL_MODELO not in df.columns or COL_ANO not in df.columns:
        st.error(f"As colunas '{COL_MODELO}' ou '{COL_ANO}' não foram encontradas na planilha. Verifique os nomes exatos das colunas.")
    else:
        
        # 1. FILTROS (VÊM PRIMEIRO NA SIDEBAR)
        
        # --- FILTRO MODELO ---
        modelos_unicos = sorted(df[COL_MODELO].unique())
        lista_modelos = ["Todos"] + modelos_unicos
        selected_model = st.sidebar.selectbox("Modelo do Carro:", lista_modelos)

        # --- FILTRO ANO ---
        anos_unicos = sorted([str(a) for a in df[COL_ANO].unique()], reverse=True)
        lista_anos = ["Todos"] + anos_unicos
        selected_year = st.sidebar.selectbox("Ano de Fabricação:", lista_anos)
        
        # 2. BOTÃO DE RECARGA MANUAL (VEM DEPOIS NA SIDEBAR)
        st.sidebar.markdown("---") # Linha separadora para organização
        if st.sidebar.button("🔄 Recarregar Dados Agora"):
            # Ação: Limpa o cache e força a reexecução do script
            st.cache_data.clear()
            st.rerun() 
            st.sidebar.success("Dados recarregados!")

        # 3. APLICAR FILTROS (Lógica principal)
        df_filtrado = df.copy()

        # Filtrar por Modelo
        if selected_model != "Todos":
            df_filtrado = df_filtrado[df_filtrado[COL_MODELO] == selected_model]

        # Filtrar por Ano
        if selected_year != "Todos":
            df_filtrado = df_filtrado[df_filtrado[COL_ANO].astype(str) == selected_year]
        
        # 4. EXIBIR RESULTADOS (Corpo do aplicativo)
        st.subheader(f"Dados Filtrados ({len(df_filtrado)} registros)")
        
        if df_filtrado.empty:
            st.info("Nenhum registro encontrado com os filtros selecionados.")
        else:
            st.dataframe(df_filtrado, use_container_width=True)

st.caption("Nota: A recarga automática ocorre a cada 60 segundos. O botão de recarga manual força a busca por novos dados.")