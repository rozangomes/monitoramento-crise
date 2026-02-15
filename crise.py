import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from transformers import pipeline
import re

# --- CONFIGURAÇÃO DA IA ---
@st.cache_resource
def carregar_ia():
    return pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

def classificar_sentimento(texto, analisador):
    res = analisador(texto[:512])[0]
    estrelas = int(res['label'].split()[0])
    if estrelas <= 2: return "Negativo"
    elif estrelas == 3: return "Neutro"
    else: return "Positivo"

# --- INTERFACE ---
st.set_page_config(page_title="Gestão de Crise - Impulso", layout="wide")
st.title("🚨 Monitoramento de Crise e Reputação")

analisador = carregar_ia()

# Upload do Arquivo
arquivo = st.file_uploader("Suba a planilha de comentários (Excel ou CSV)", type=["xlsx", "csv"])

if arquivo:
    # Lendo os dados
    if arquivo.name.endswith('csv'):
        df = pd.read_csv(arquivo)
    else:
        df = pd.read_excel(arquivo)

    # Supondo que a coluna com os textos se chame 'comentario'
    colunas = df.columns.tolist()
    coluna_texto = st.selectbox("Selecione a coluna que contém os comentários:", colunas)

    if st.button("Analisar Clima Digital"):
        with st.spinner("IA analisando comentários..."):
            df['Sentimento'] = df[coluna_texto].apply(lambda x: classificar_sentimento(str(x), analisador))
        
        # --- MÉTRICAS DE CRISE ---
        total = len(df)
        negativos = len(df[df['Sentimento'] == 'Negativo'])
        perc_negativo = (negativos / total) * 100

        # Alerta de Crise
        if perc_negativo > 40:
            st.error(f"⚠️ ALERTA DE CRISE: {perc_negativo:.1f}% de críticas negativas!")
        elif perc_negativo > 20:
            st.warning(f"🟡 ATENÇÃO: Clima instável ({perc_negativo:.1f}% negativo).")
        else:
            st.success(f"✅ CLIMA CONTROLADO: Apenas {perc_negativo:.1f}% de negatividade.")

        # --- VISUALIZAÇÃO ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribuição de Sentimentos")
            fig, ax = plt.subplots()
            df['Sentimento'].value_counts().plot(kind='bar', color=['red', 'green', 'gray'], ax=ax)
            st.pyplot(fig)

        with col2:
            st.subheader("Nuvem de Críticas (Top Comentários Negativos)")
            st.write(df[df['Sentimento'] == 'Negativo'][coluna_texto].head(10))