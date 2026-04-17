import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAZIONE IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="AgriSmart Vivaio", layout="wide")

st.title("🌱 AgriSmart: Gestione Vivaio & Food Cost")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📅 Ciclo di Vita", "💰 Calcolo Costi", "👁️ IA Agronomo"])

with tab1:
    st.header("Andamento Aziendale")
    col1, col2, col3 = st.columns(3)
    col1.metric("Fatturato Lordo", "€ 1.250") 
    col2.metric("Costo Produzione Medio", "€ 0,42")
    col3.metric("% Successo Nascite", "88%")

with tab2:
    st.header("Monitoraggio Lotti in Corso")
    nome_p = st.text_input("Nome Varietà (es. Basilico)")
    data_s = st.date_input("Data di Semina", datetime.now())
    giorni_passati = (datetime.now().date() - data_s).days
    st.info(f"Questa piantina è al **Giorno {giorni_passati}** dalla semina.")
    
    if giorni_passati < 7:
        st.warning("Fase: **Germinazione**. Controlla l'umidità.")
    elif giorni_passati < 21:
        st.info("Fase: **Accrescimento**. Valuta concimazione.")
    else:
        st.success("Fase: **Pronta per la vendita**.")

with tab3:
    st.header("Calcolo Prezzi e Margini")
    c_seme = st.number_input("Costo unitario seme (€)", format="%.4f", value=0.02)
    c_terra = st.number_input("Costo terra per vasetto (€)", format="%.2f", value=0.10)
    c_vaso = st.number_input("Costo vasetto (€)", format="%.2f", value=0.08)
    n_semi = st.number_input("Semi piantati", value=100)
    n_nati = st.number_input("Piantine nate", value=85)

    success_rate = (n_nati / n_semi) * 100
    costo_reale = ((c_seme + c_terra + c_vaso) * n_semi) / n_nati
    
    st.subheader(f"Analisi {nome_p}")
    st.write(f"**Costo Produzione Reale:** € {costo_reale:.2f}")
    prezzo_v = st.number_input("Prezzo di Vendita (€)", value=1.50)
    st.metric("Margine Netto", f"€ {prezzo_v - costo_reale:.2f}")

with tab4:
    st.header("Analisi IA Migliorativa")
    foto = st.file_uploader("Scatta o carica foto", type=['jpg', 'png', 'jpeg'])
    if foto:
        img = Image.open(foto)
        st.image(img, width=300)
        if st.button("Analizza con IA"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(["Agisci come agronomo esperto. Analizza la salute di questa piantina e dai consigli per migliorare la crescita.", img])
            st.write(response.text)
