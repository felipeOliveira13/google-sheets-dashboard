import streamlit as st
import gspread
import pandas as pd
import math
import altair as alt

# --- CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA CHAMADA STREAMLIT) ---
st.set_page_config(
    page_title="Painel exibição de dados",
    page_icon="📈", 
    layout="wide"
)

# -----------------------------------------
# Configurações da Planilha
# -----------------------------------------
SHEET_ID = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
ABA = "carros"
# ROWS_PER_PAGE AGORA SERÁ DEFINIDO NO CORPO PRINCIPAL PELO USUÁRIO
# -----------------------------------------

# -----------------------------------------
# FUNÇÃO AUXILIAR PARA CALCULAR ALTURA
# -----------------------------------------
def calcular_altura_tabela(num_rows):
    """Calcula a altura ideal em pixels para exibir exatamente o número de linhas, sem rolagem."""
    HEADER_HEIGHT = 35
    ROW_HEIGHT = 35
    MAX_HEIGHT = 800
    
    altura_dinamica = HEADER_HEIGHT + (num_rows * ROW_HEIGHT)
    
    return min(altura_dinamica, MAX_HEIGHT)

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

        # Adicionar uma etapa de limpeza: remover linhas onde a coluna 'Modelo' está vazia
        if 'Modelo' in df.columns:
            df = df.dropna(subset=['Modelo'])
        
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ou carregar dados: {e}")
        st.info("Verifique a chave 'google' no Streamlit Secrets (secrets.toml).")
        return None


# -----------------------------------------
# STREAMLIT APP PRINCIPAL
# -----------------------------------------
st.title("Painel exibição de dados") 

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
    COL_PRECO = 'Preço (R$)' 
    
    required_cols = [COL_MODELO, COL_ANO]
    if not all(col in df.columns for col in required_cols):
        st.error(f"As colunas necessárias {required_cols} não foram encontradas na planilha.")
    else:
        
        # 2. FILTROS (Sidebar)
        modelos_unicos = sorted(df[COL_MODELO].unique())
        lista_modelos = ["Todos"] + modelos_unicos
        selected_model = st.sidebar.selectbox("Modelo do Carro:", lista_modelos)

        anos_unicos = sorted([str(a) for a in df[COL_ANO].unique()], reverse=True)
        lista_anos = ["Todos"] + anos_unicos
        selected_year = st.sidebar.selectbox("Ano de Fabricação:", lista_anos)
        
        # 2a. SELETOR DE EXIBIÇÃO (Sidebar)
        st.sidebar.markdown("---")
        display_mode = st.sidebar.radio(
            "Modo de Exibição:",
            ["Ambos", "Apenas Gráfico", "Apenas Tabela"]
        )
        
        # 2b. O SELETOR DE PAGINAÇÃO FOI REMOVIDO DA SIDEBAR
        # st.sidebar.slider(...)
        
        st.sidebar.markdown("---")
        
        # 3. BOTÃO DE RECARGA MANUAL (Sidebar)
        if st.sidebar.button("🔄 Recarregar Dados Agora"):
            st.cache_data.clear()
            st.session_state.current_page = 1 
            st.rerun() 
            st.sidebar.success("Dados recarregados!")

        # 4. APLICAÇÃO DE FILTROS (Lógica principal)
        df_filtrado = df.copy()
        if selected_model != "Todos":
            df_filtrado = df_filtrado[df_filtrado[COL_MODELO] == selected_model]
        if selected_year != "Todos":
            df_filtrado = df_filtrado[df_filtrado[COL_ANO].astype(str) == selected_year]
        
        # --- LÓGICA DE VISUALIZAÇÃO E PAGINAÇÃO ---

        if df_filtrado.empty:
            st.info("Nenhum registro encontrado com os filtros selecionados.")
        else:
            
            # 5. GRÁFICO (Exibe se a opção for "Ambos" ou "Apenas Gráfico")
            if display_mode in ["Ambos", "Apenas Gráfico"]:
                if COL_PRECO not in df.columns:
                     st.warning(f"A coluna de preço '{COL_PRECO}' é necessária para o gráfico e não foi encontrada.")
                else:
                    try:
                        # Limpeza e conversão para numérico
                        df_filtrado[COL_PRECO] = pd.to_numeric(
                            df_filtrado[COL_PRECO].astype(str).str.replace(',', '.', regex=False),
                            errors='coerce'
                        )
                        df_precos_validos = df_filtrado.dropna(subset=[COL_PRECO])

                        if not df_precos_validos.empty:
                            st.subheader("Visualização: Média de Preço por Modelo (R$)")
                            
                            # 5a. Calcular a Média de Preço por Modelo
                            media_precos = df_precos_validos.groupby(COL_MODELO)[COL_PRECO].mean().reset_index()
                            media_precos.columns = [COL_MODELO, 'Preço Médio (R$)']
                            
                            # 5b. Criar o Gráfico de Barras com Altair
                            chart = alt.Chart(media_precos).mark_bar().encode(
                                x=alt.X('Preço Médio (R$)', title='Preço Médio (R$)', axis=alt.Axis(format='$,.2f')),
                                y=alt.Y(COL_MODELO, sort='-x', title='Modelo'),
                                tooltip=[COL_MODELO, alt.Tooltip('Preço Médio (R$)', format='$,.2f')]
                            ).properties(
                                title='Média de Preços por Modelo (Dados Filtrados)'
                            ).interactive()
                            
                            st.altair_chart(chart, use_container_width=True)

                        else:
                            st.info(f"Não há dados válidos na coluna '{COL_PRECO}' para calcular a média e gerar o gráfico.")

                    except Exception as e:
                        st.error(f"Erro ao gerar o gráfico de média de preços. Verifique o formato dos dados: {e}")
            
            # 6. EXIBIÇÃO DA TABELA E PAGINAÇÃO (Exibe se a opção for "Ambos" ou "Apenas Tabela")
            if display_mode in ["Ambos", "Apenas Tabela"]:
                
                # Definir o valor padrão da paginação antes de calculá-la
                # Usaremos um valor inicial de 10 se a variável ROWS_PER_PAGE não estiver definida (embora deva ser definida mais tarde)
                # Vamos definir ROWS_PER_PAGE temporariamente para 10 para o cálculo inicial
                ROWS_PER_PAGE = 10 
                
                if 'rows_per_page_value' in st.session_state:
                    ROWS_PER_PAGE = st.session_state.rows_per_page_value
                
                total_rows = len(df_filtrado)
                total_pages = math.ceil(total_rows / ROWS_PER_PAGE) 

                # Tratamento de erro de página após a alteração do filtro/itens por página
                if st.session_state.current_page > total_pages and total_pages > 0:
                    st.session_state.current_page = total_pages
                elif total_pages == 0:
                    st.session_state.current_page = 1
                
                start_row = (st.session_state.current_page - 1) * ROWS_PER_PAGE
                end_row = start_row + ROWS_PER_PAGE
                
                df_paginado = df_filtrado.iloc[start_row:end_row]

                st.subheader(f"Dados da Tabela: {total_rows} registros (Exibindo {ROWS_PER_PAGE} por página)")
                
                if df_paginado.empty:
                    st.info("Nenhum registro para exibir na tabela.")
                else:
                    table_height = calcular_altura_tabela(len(df_paginado))
                    st.dataframe(
                        df_paginado, 
                        use_container_width=True, 
                        height=table_height,
                        hide_index=True 
                    )

                    # 7. BOTÕES DE NAVEGAÇÃO E CONTROLE DE ITENS POR PÁGINA (NOVA ESTRUTURA)
                    
                    # 7a. Linha principal com botões de navegação e o Slider centralizado
                    # Alterando a distribuição de colunas de [1, 2, 1] para [1, 1.5, 1] para reduzir o tamanho do slider
                    col_prev, col_slider, col_next = st.columns([1, 1.5, 1])

                    with col_prev:
                        if st.button("<< Anterior", disabled=(st.session_state.current_page == 1), use_container_width=True):
                            st.session_state.current_page -= 1
                            st.rerun()
                    
                    with col_slider:
                        # Seletor de Paginação movido e armazenado no session_state para persistência
                        rows_per_page_selection = st.slider(
                            "Itens por Página (1-15)",
                            min_value=1,
                            max_value=15,
                            value=ROWS_PER_PAGE, 
                            step=1,
                            key='rows_per_page_value',
                            label_visibility="collapsed" # Remove o label para centralizar melhor
                        )
                        # Se o valor mudar, o Streamlit vai rerunnar e usar o novo valor
                        ROWS_PER_PAGE = rows_per_page_selection
                        
                        # NOVO: Texto descritivo abaixo do slider, agora CENTRALIZADO usando st.markdown com CSS
                        st.markdown(
                            "<p style='text-align: center; font-size: 0.8em;'>ajuste para visualização de número de itens por página</p>",
                            unsafe_allow_html=True
                        )


                    with col_next:
                        if st.button("Próximo >>", disabled=(st.session_state.current_page >= total_pages), use_container_width=True):
                            st.session_state.current_page += 1
                            st.rerun()

                    # 7b. Linha secundária para a identificação da página (Abaixo do botão Próximo)
                    # Colunas para alinhar o texto à direita (sob o botão Próximo)
                    col_info_left, col_info_right = st.columns([3, 1])
                    
                    with col_info_right:
                        # Texto informativo abaixo e alinhado à direita
                        st.markdown(
                            f"<p style='text-align: right; font-weight: bold;'>Página {st.session_state.current_page} de {total_pages}</p>", 
                            unsafe_allow_html=True
                        )

st.caption("Status: Dashboard com controle de visualização.")