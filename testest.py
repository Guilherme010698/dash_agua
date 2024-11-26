import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
from scipy.stats import spearmanr

# Configurações do Streamlit
st.title("Análise de Qualidade da Água")
st.sidebar.header("Configurações")

# Upload do arquivo Excel
uploaded_file = st.sidebar.file_uploader("Faça upload do arquivo Excel", type=["xlsx", "xls"])

if uploaded_file:
    try:
        # Ler os dados do Excel
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        st.success("Dados carregados com sucesso!")

        # Mostrar os primeiros registros para conferência
        st.subheader("Prévia dos Dados")
        st.write(df.head())

        # Verificar se a coluna de Data está presente
        if "Data" not in df.columns:
            st.error("O arquivo Excel deve conter uma coluna chamada 'Data'.")
        else:
            # Converter a coluna 'Data' para o formato datetime
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

            # Filtro para o intervalo de datas
            min_data = df['Data'].min().date()
            max_data = df['Data'].max().date()

            periodo = st.sidebar.date_input(
                "Selecione o período",
                value=(min_data, max_data),
                min_value=min_data,
                max_value=max_data,
            )

            # Filtrar os dados com base no período selecionado
            df_filtrado = df[(df['Data'] >= pd.to_datetime(periodo[0])) & (df['Data'] <= pd.to_datetime(periodo[1]))]

            # Filtro para selecionar a estação de monitoramento
            estacoes = df_filtrado["Estação"].unique()
            estacao_selecionada = st.sidebar.multiselect(
                "Selecione a(s) estação(ões) de monitoramento",
                options=estacoes,
                default=estacoes,
            )

            # Filtrar os dados com base na estação selecionada
            df_filtrado = df_filtrado[df_filtrado["Estação"].isin(estacao_selecionada)]

            # Adicionar mapa de localização com tema escuro, marcador de triângulo e nome da estação
            st.header("Mapa de Localização das Estações")
            mapa = pdk.Deck(
                map_style="mapbox://styles/mapbox/dark-v10",  # Tema escuro
                initial_view_state=pdk.ViewState(
                    latitude=df_filtrado["y"].mean(),
                    longitude=df_filtrado["x"].mean(),
                    zoom=10,
                    pitch=50,
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=df_filtrado,
                        get_position=["x", "y"],
                        get_color="[200, 30, 0, 160]",  # Cor vermelha com transparência
                        get_radius=200,
                        pickable=True,
                        # Usando um triângulo como marcador
                        icon_data={
                            "url": "https://upload.wikimedia.org/wikipedia/commons/1/19/Red_triangle_icon.svg",  # Triângulo vermelho
                            "width": 24,
                            "height": 24,
                            "anchor": "center",
                        },
                        get_text="Estação",  # Coloca o nome da estação acima do marcador
                        get_text_anchor="middle",  # Alinha o texto centralizado
                        get_text_size=12,  # Tamanho do texto
                        get_text_color="[255, 255, 255, 255]",  # Cor do texto em branco
                    ),
                ],
            )
            st.pydeck_chart(mapa)

            # Seleção de colunas para gráfico de barras
            if "Ano" in df_filtrado.columns:
                coluna_ano = "Ano"  # Assumimos que a coluna 'Ano' já existe na tabela
                # Excluindo as colunas 'Ano', 'x' e 'y' dos parâmetros disponíveis para o gráfico de barras
                parametros = [col for col in df_filtrado.select_dtypes(include=["float64", "int64"]).columns if col not in ["Ano", "x", "y"]]

                # Título e filtro para o gráfico de barras
                st.header(f"Gráfico de Barras: {coluna_ano} vs Parâmetro")
                parametro_escolhido = st.selectbox(
                    "Escolha um parâmetro para o gráfico de barras",
                    options=parametros,
                )

                # Criar o gráfico de barras
                df_barras = df_filtrado.groupby(coluna_ano)[parametro_escolhido].mean().reset_index()

                fig_barras = px.bar(
                    df_barras,
                    x=coluna_ano,
                    y=parametro_escolhido,
                    title=f"Variação do {parametro_escolhido} ao longo dos anos",
                    labels={coluna_ano: "Ano", parametro_escolhido: parametro_escolhido},
                    color=coluna_ano,
                )
                st.plotly_chart(fig_barras, use_container_width=True)

            # Seleção de colunas numéricas para o gráfico de dispersão
            numeric_columns = [col for col in df_filtrado.select_dtypes(include=["float64", "int64"]).columns if col not in ["Ano", "x", "y"]]

            if len(numeric_columns) < 2:
                st.warning("O conjunto de dados precisa ter pelo menos duas colunas numéricas.")
            else:
                # Título e filtro para o gráfico de dispersão
                st.header(f"Gráfico de Dispersão")
                x_axis = st.selectbox("Selecione o eixo X", numeric_columns)
                y_axis = st.selectbox("Selecione o eixo Y", numeric_columns)

                # Verificar dados ausentes e tratar
                df_corr = df_filtrado.dropna(subset=[x_axis, y_axis])

                if len(df_corr) < 2:
                    st.warning("Dados insuficientes para calcular a correlação ou plotar o gráfico.")
                else:
                    # Plotar gráfico de dispersão interativo com Plotly
                    fig = px.scatter(
                        df_corr,
                        x=x_axis,
                        y=y_axis,
                        color="Estação",
                        title=f"{x_axis} vs {y_axis}",
                        labels={x_axis: x_axis, y_axis: y_axis},
                        hover_data=df_corr.columns,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Calcular e exibir o coeficiente de Spearman
                    if x_axis != y_axis:
                        spearman_corr, _ = spearmanr(df_corr[x_axis], df_corr[y_axis])
                        st.subheader("Coeficiente de Correlação de Spearman")
                        st.write(f"**{spearman_corr:.2f}**")
                    else:
                        st.warning("Selecione variáveis diferentes para calcular a correlação.")
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
else:
    st.info("Por favor, faça upload de um arquivo Excel com os dados de qualidade da água.")



