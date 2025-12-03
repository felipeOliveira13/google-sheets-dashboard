import streamlit as st
import gspread
import pandas as pd
import math
import altair as alt # Importar Altair para criar gráficos mais avançados

# -----------------------------------------
# Configurações da Planilha
# -----------------------------------------
SHEET_ID = "1zAoEQQqDaBA2E9e6eLOB2xWbmDmYa5Vyxduk9AvKqzE"
ABA = "carros"
ROWS_PER_PAGE = 10 # Definição do número de linhas por página

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
        # Tenta obter todos os registros. NOTA: Se houver linhas vazias completas no final,
        # 'get_all_records()' tende a ignorá-las, o que ajuda na limpeza.
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
    # ⚠️ Nome da coluna de Preço, ajuste se for diferente!
    COL_PRECO = 'Preço (R$)' 
    
    # Validação de colunas necessárias
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
        
        # 3. BOTÃO DE RECARGA MANUAL (Sidebar)
        st.sidebar.markdown("---")
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
            
            # 5. GRÁFICO DE BARRAS: Contagem por Modelo
            st.subheader("Visualização: Contagem de Veículos por Modelo")
            
            # Agrupa e conta os modelos
            contagem_modelo = df_filtrado[COL_MODELO].value_counts().reset_index()
            contagem_modelo.columns = [COL_MODELO, 'Contagem']
            
            # Cria o gráfico usando Altair para melhor visualização
            chart = alt.Chart(contagem_modelo).mark_bar().encode(
                x=alt.X('Contagem', title='Número de Carros'),
                y=alt.Y(COL_MODELO, sort='-x', title='Modelo'),
                tooltip=[COL_MODELO, 'Contagem']
            ).properties(
                title='Distribuição de Modelos (Dados Filtrados)'
            ).interactive() # Permite zoom e pan
            
            st.altair_chart(chart, use_container_width=True)
            
            # 6. HISTOGRAMA DE PREÇOS (Se a coluna de preço existir)
            if COL_PRECO in df.columns:
                try:
                    # Tenta converter a coluna de preço para um tipo numérico
                    # NOTA: O Google Sheets retorna tudo como string, então isso é crucial.
                    df_filtrado[COL_PRECO] = pd.to_numeric(df_filtrado[COL_PRECO], errors='coerce')
                    df_precos = df_filtrado.dropna(subset=[COL_PRECO])

                    if not df_precos.empty:
                        st.subheader("Visualização: Distribuição de Preços")
                        # Cria o histograma
                        hist_chart = alt.Chart(df_precos).mark_bar().encode(
                            alt.X(COL_PRECO, bin=True, title='Preço (R$)'),
                            alt.Y('count()', title='Frequência'),
                            tooltip=[COL_PRECO, 'count()']
                        ).properties(
                            title='Histograma de Preços'
                        ).interactive()

                        st.altair_chart(hist_chart, use_container_width=True)

                except Exception as e:
                    st.warning(f"Não foi possível gerar o histograma de preços. Verifique se a coluna '{COL_PRECO}' contém apenas números (sem caracteres como 'R$' ou pontos, exceto vírgula decimal, que deve ser ajustada). Erro: {e}")
            
            # --- PAGINAÇÃO E TABELA ---

            total_rows = len(df_filtrado)
            total_pages = math.ceil(total_rows / ROWS_PER_PAGE)

            if st.session_state.current_page > total_pages and total_pages > 0:
                st.session_state.current_page = total_pages
            elif total_pages == 0:
                 st.session_state.current_page = 1
            
            start_row = (st.session_state.current_page - 1) * ROWS_PER_PAGE
            end_row = start_row + ROWS_PER_PAGE
            
            df_paginado = df_filtrado.iloc[start_row:end_row]

            # 7. EXIBIÇÃO DA TABELA
            st.subheader(f"Dados da Tabela: {total_rows} registros")
            
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

                # 8. BOTÕES DE NAVEGAÇÃO
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("<< Anterior", disabled=(st.session_state.current_page == 1)):
                        st.session_state.current_page -= 1
                        st.rerun()
                
                with col3:
                    st.markdown(
                        f"<p style='text-align: center; font-weight: bold;'>Página {st.session_page.current_page} de {total_pages}</p>", 
                        unsafe_allow_html=True
                    )

                with col5:
                    if st.button("Próximo >>", disabled=(st.session_state.current_page >= total_pages)):
                        st.session_state.current_page += 1
                        st.rerun()

st.caption("Status: Dashboard com filtros, paginação e visualizações dinâmicas.")