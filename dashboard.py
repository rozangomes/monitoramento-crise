import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from transformers import pipeline
from fpdf import FPDF
from wordcloud import WordCloud
import os

# --- 1. CONFIGURAÇÃO DA IA ---
@st.cache_resource
def carregar_ia():
    return pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

def classificar_sentimento(texto, analisador):
    if not texto or len(str(texto)) < 3: return "Neutro"
    res = analisador(str(texto)[:512])[0]
    estrelas = int(res['label'].split()[0])
    if estrelas <= 2: return "Negativo"
    elif estrelas == 3: return "Neutro"
    else: return "Positivo"

# --- 2. FUNÇÃO NUVEM DE PALAVRAS ---
def gerar_nuvem(df, coluna_texto, salvar_caminho=None):
    texto_negativo = " ".join(df[df['Sentimento'] == 'Negativo'][coluna_texto].astype(str))
    if len(texto_negativo) > 10:
        stopwords_pt = ["de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "não", "uma", "os", "no", "se", "na", "este", "esta", "por", "mais", "tem"]
        nuvem = WordCloud(width=800, height=400, background_color='white', colormap='Reds', stopwords=stopwords_pt).generate(texto_negativo)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(nuvem, interpolation='bilinear')
        ax.axis("off")
        
        if salvar_caminho:
            plt.savefig(salvar_caminho, bbox_inches='tight', dpi=150)
            plt.close(fig)
        else:
            st.pyplot(fig)
    else:
        if not salvar_caminho:
            st.info("Amostra insuficiente de críticas para gerar a nuvem de palavras.")

# --- 3. FUNÇÃO PDF COMPLETA ---
def gerar_pdf_completo(df_final, perc_neg, col_texto, caminho_grafico, caminho_nuvem, caminho_logo, link_post):
    pdf = FPDF()
    pdf.add_page()
    
    # Inserir Logo
    if caminho_logo and os.path.exists(caminho_logo):
        try:
            pdf.image(caminho_logo, x=10, y=8, w=35)
        except:
            pass
            
    pdf.set_font("Arial", 'B', 16)
    pdf.ln(15)
    pdf.cell(200, 10, txt="Relatorio de Monitoramento Digital", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Impulso Marketing Politico", ln=True, align='C')
    
    # Inserir Link se existir
    if link_post:
        pdf.ln(5)
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(200, 10, txt=f"Link do Post: {link_post}", ln=True, align='C', link=link_post)
        pdf.set_text_color(0, 0, 0)

    # Inserir Gráfico de Pizza
    pdf.ln(5)
    if os.path.exists(caminho_grafico):
        pdf.image(caminho_grafico, x=60, y=pdf.get_y() + 5, w=90)
        pdf.ln(85)

    # Inserir Nuvem de Palavras no PDF
    if os.path.exists(caminho_nuvem):
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(200, 10, txt="Nuvem de Palavras das Criticas:", ln=True)
        pdf.image(caminho_nuvem, x=40, y=pdf.get_y() + 2, w=130)
        pdf.ln(70)

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Indice de Negatividade: {perc_neg:.1f}%", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, txt="Amostra de Comentarios:", ln=True)
    
    pdf.set_font("Arial", size=9)
    for index, row in df_final.head(20).iterrows():
        texto_limpo = str(row[col_texto]).encode('latin-1', 'replace').decode('latin-1')
        linha = f"- [{row['Sentimento']}]: {texto_limpo[:85]}..."
        pdf.cell(200, 7, txt=linha, ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE ---
st.set_page_config(page_title="Impulso - Monitoramento", layout="wide")

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
CAMINHO_LOGO = os.path.join(diretorio_atual, "logo_impulso.png")

col_l, col_t = st.columns([1, 4])
with col_l:
    if os.path.exists(CAMINHO_LOGO):
        st.image(CAMINHO_LOGO, width=150)
with col_t:
    st.title("🛡️ Gestão de Crise e Reputação")
    st.markdown("Análise de sentimentos e monitoramento estratégico - **Impulso**")

analisador = carregar_ia()
arquivo = st.file_uploader("Carregue a sua folha de Excel ou CSV", type=["xlsx", "csv"])

if arquivo:
    df = pd.read_excel(arquivo) if arquivo.name.endswith('xlsx') else pd.read_csv(arquivo)
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        coluna_texto = st.selectbox("Selecione a coluna de texto:", df.columns)
        link_post = st.text_input("Link do Post (opcional):", placeholder="https://instagram.com/p/...")
        btn_analisar = st.button("🚀 Iniciar Processamento")

    if btn_analisar:
        with st.spinner("Analisando dados com IA..."):
            df['Sentimento'] = df[coluna_texto].apply(lambda x: classificar_sentimento(x, analisador))
        
        contagem = df['Sentimento'].value_counts()
        total = len(df)
        perc_neg = (contagem.get('Negativo', 0) / total) * 100

        # Dashboard Visual
        c1, c2 = st.columns([1, 1.5])

        with c1:
            st.subheader("📊 Resumo Executivo")
            st.metric("Total Analisado", total)
            
            if perc_neg > 30:
                st.error(f"Alerta de Crise: {perc_neg:.1f}%")
            else:
                st.success(f"Clima Positivo: {perc_neg:.1f}% Negativo")
            
            # Gerar Gráficos Temporários
            caminho_img = "grafico_temp.png"
            caminho_nuvem_img = "nuvem_temp.png"
            
            fig_temp, ax_temp = plt.subplots(figsize=(5, 4))
            cores_map = {'Positivo': '#2ecc71', 'Negativo': '#e74c3c', 'Neutro': '#95a5a6'}
            cores_lista = [cores_map.get(x, '#333') for x in contagem.index]
            contagem.plot(kind='pie', autopct='%1.1f%%', colors=cores_lista, ax=ax_temp)
            plt.ylabel("")
            plt.savefig(caminho_img, bbox_inches='tight', dpi=150)
            plt.close(fig_temp)

            # Gera a nuvem silenciosamente para salvar o arquivo do PDF
            gerar_nuvem(df, coluna_texto, salvar_caminho=caminho_nuvem_img)

            # Botão de PDF atualizado
            pdf_bytes = gerar_pdf_completo(df, perc_neg, coluna_texto, caminho_img, caminho_nuvem_img, CAMINHO_LOGO, link_post)
            st.download_button(
                label="📥 Descarregar Relatório Oficial PDF",
                data=pdf_bytes,
                file_name="Relatorio_Impulso.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with c2:
            st.subheader("📈 Gráfico de Sentimento")
            fig, ax = plt.subplots(figsize=(5, 3))
            contagem.plot(kind='pie', autopct='%1.1f%%', colors=cores_lista, ax=ax, textprops={'fontsize': 8})
            plt.ylabel("")
            st.pyplot(fig)

        st.divider()
        st.subheader("🗣️ Temas Centrais nas Críticas (Nuvem de Palavras)")
        gerar_nuvem(df, coluna_texto) # Mostra na tela

        st.divider()
        st.subheader("📑 Detalhamento dos Comentários")
        st.dataframe(df[[coluna_texto, 'Sentimento']], use_container_width=True)
        
        # Limpeza de arquivos temporários
        for temp_file in [caminho_img, caminho_nuvem_img]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
