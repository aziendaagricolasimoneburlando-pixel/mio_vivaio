import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import webbrowser

st.set_page_config(page_title="AgriSmart Vivaio", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.title("🌱 AgriSmart: Gestione Vivaio")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📅 Ciclo di Vita", "💰 Calcolo Costi", "👁️ IA Agronomo"])

with tab2:
    st.header("Registra Nuova Semina")
    st.info("Inserisci i dati e clicca sul tasto per registrarli nel tuo database.")
    
    v = st.text_input("Nome Varietà")
    d = st.date_input("Data Semina", datetime.now())
    s = st.number_input("Numero Semi", min_value=1, value=100)
    n = st.number_input("Piantine Nate", value=0)
    c = st.number_input("Costo totale (€)", value=0.0)
    
    # QUI INCOLLA IL LINK DEL TUO MODULO GOOGLE
    url_modulo = "INCOLLA_QUI_IL_LINK_DEL_TUO_MODULO_GOOGLE"
    
    if st.button("Vai a registrare il lotto"):
        st.success("Reindirizzamento al database in corso...")
        # Questo apre il modulo per salvare i dati in sicurezza
        webbrowser.open_new_tab(url_modulo)

with tab1:
    st.header("Dashboard Aziendale")
    st.write("Puoi visualizzare i dati storici direttamente sul tuo foglio Google.")
    st.link_button("Apri il tuo Foglio Google", "https://docs.google.com/spreadsheets/d/1L_4hrKZ5UMgMmgx0gXtcySPG2N95c15MNcp2quy8-Xo/")

with tab4:
    st.header("Analisi IA Migliorativa")
    foto = st.file_uploader("Carica foto", type=['jpg', 'png', 'jpeg'])
    if foto:
        img = Image.open(foto)
        st.image(img, width=300)
        if st.button("Analizza con IA"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(["Analizza questa pianta e dai consigli tecnici.", img])
            st.write(response.text)
