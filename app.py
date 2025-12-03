import streamlit as st
import gspread
import pandas as pd
import math # Importar para usar a função ceil

# -----------------------------------------
# Configurações da Planilha
# -----------------------------------------
SHEET_ID = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
ABA = "carros"
ROWS_PER_PAGE = 10 # Definição do número de linhas por página

# -----------------------------------------
# FUNÇÃO AUXILIAR PARA CALCULAR ALTURA
# -----------------------------------------
def calcular_altura_tabela(df):
    """Calcula a altura ideal em pixels para exibir todas as linhas sem rolagem."""
    HEADER_HEIGHT = 35
    ROW_HEIGHT = 35
    MAX_HEIGHT = 800
    
    # A altura será baseada no ROWS_PER_PAGE para manter o layout fixo
    # Mesmo se houver menos de 10 linhas na última página, a tabela terá o mesmo tamanho.
    altura_fixa = HEADER_HEIGHT + (ROWS_PER_PAGE * ROW_HEIGHT)
    
    return min(altura_fixa, MAX_HEIGHT)

# -----------------------------------------
# Conectar e Carregar Planilha
# -----------------------------------------
@st.cache_data(ttl=60) 
def conectar_planilha(sheet_id, aba):
    """Função para autenticar e carregar o DataFrame da planilha."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["google"])
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.worksheet(aba)
        dados = worksheet.get_all_records()
        df = pd.DataFrame(dados)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ou carregar dados: {e}")
        st.info("Verifique a chave 'google' no Streamlit Secrets (secrets.toml).")
        return None


# -----------------------------------------
# STREAMLIT APP PRINCIPAL
# -----------------------------------------
st.title("📊 Dashboard - Google Sheets (Carros)")

# 1. INICIALIZAÇÃO DO ESTADO DA PÁGINA
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# --- Início da Barra Lateral (Sidebar) ---
st.sidebar.header("⚙️ Opções e Filtros")

# Carregamento do DataFrame
df = conectar_planilha(SHEET_ID, ABA)

if df is not None and not df.empty:
    
    COL_MODELO = 'Modelo' 
    COL_ANO = 'Ano'
    
    if COL_MODELO not in df.columns or COL_ANO not in df.columns:
        st.error(f"As colunas '{COL_MODELO}' ou '{COL_ANO}' não foram encontradas na planilha.")
    else:
        
        # 2. FILTROS (Sidebar)
        
        modelos_unicos = sorted(df[COL_MODELO].unique())
        lista_modelos = ["Todos"] + modelos_unicos
        selected_model = st.sidebar.selectbox("Modelo do Carro:", lista_modelos)

        anos_unicos = sorted([str(a) for a in df[COL_ANO].unique()], reverse=True)
        lista_anos = ["Todos"] + anos_unicos
        selected_year = st.sidebar.selectbox("Ano de Fabricação:", lista_anos)
        
        # 3. BOTÃO DE RECARGA MANUAL (Sidebar)
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Recarregar Dados Agora"):
            st.cache_data.clear()
            st.session_state.current_page = 1 # Reinicia a página após recarregar
            st.rerun() 
            st.sidebar.success("Dados recarregados!")

        # 4. APLICAÇÃO DE FILTROS (Lógica principal)
        df_filtrado = df.copy()
        if selected_model != "Todos":
            df_filtrado = df_filtrado[df_filtrado[COL_MODELO] == selected_model]
        if selected_year != "Todos":
            df_filtrado = df_filtrado[df_filtrado[COL_ANO].astype(str) == selected_year]
        
        # --- LÓGICA DE PAGINAÇÃO ---
        total_rows = len(df_filtrado)
        total_pages = math.ceil(total_rows / ROWS_PER_PAGE)

        # Garante que a página atual não exceda o total de páginas (ocorre após a filtragem)
        if st.session_state.current_page > total_pages and total_pages > 0:
            st.session_state.current_page = total_pages
        elif total_pages == 0:
             st.session_state.current_page = 1
        
        # Calcula os índices de início e fim da fatia (slice) do DataFrame
        start_row = (st.session_state.current_page - 1) * ROWS_PER_PAGE
        end_row = start_row + ROWS_PER_PAGE
        
        # Cria o DataFrame para exibição na página atual
        df_paginado = df_filtrado.iloc[start_row:end_row]
        
        # 5. EXIBIÇÃO DA TABELA
        
        # Cabeçalho com o status de paginação
        st.subheader(f"Dados Filtrados: {total_rows} registros")
        
        if df_paginado.empty:
            st.info("Nenhum registro encontrado com os filtros selecionados.")
            
        else:
            # Exibe a tabela
            table_height = calcular_altura_tabela(df_paginado)
            st.dataframe(
                df_paginado, 
                use_container_width=True, 
                height=table_height 
            )

            # 6. BOTÕES DE NAVEGAÇÃO
            
            # Cria colunas para centralizar a navegação
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            # Botão Anterior
            with col1:
                if st.button("<< Anterior", disabled=(st.session_state.current_page == 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            # Indicador de Página
            with col3:
                st.markdown(
                    f"<p style='text-align: center; font-weight: bold;'>Página {st.session_state.current_page} de {total_pages}</p>", 
                    unsafe_allow_html=True
                )

            # Botão Próximo
            with col5:
                if st.button("Próximo >>", disabled=(st.session_state.current_page >= total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()

st.caption("Status: Paginação implementada (10 linhas por página).")