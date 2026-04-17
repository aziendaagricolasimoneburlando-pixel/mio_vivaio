import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAZIONI ---
st.set_page_config(page_title="AgriSmart Vivaio", layout="wide")

# Connessione a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Configurazione IA
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.title("🌱 AgriSmart: Gestione Vivaio & Food Cost")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📅 Ciclo di Vita", "💰 Gestione Costi", "👁️ IA Agronomo"])

# --- TAB 2: REGISTRAZIONE ---
with tab2:
    st.header("Registra Nuova Semina")
    with st.form("nuovo_lotto"):
        v = st.text_input("Nome Varietà")
        d = st.date_input("Data Semina", datetime.now())
        s = st.number_input("Numero Semi", min_value=1, value=100)
        n = st.number_input("Piantine Nate", value=0)
        c = st.number_input("Costo totale produzione (€)", value=0.0)
        submit = st.form_submit_button("Salva nel Database")
        
        if submit:
            try:
                # Legge dati esistenti
                df_esistente = conn.read(worksheet="Lotti")
                # Crea nuova riga
                nuovo_dato = pd.DataFrame([{
                    "Varietà": v, "Data_Semina": str(d), 
                    "Semi": s, "Nati": n, "Costo_Totale": c
                }])
                # Unisce e aggiorna
                df_aggiornato = pd.concat([df_esistente, nuovo_dato], ignore_index=True)
                conn.update(worksheet="Lotti", data=df_aggiornato)
                st.success("Lotto salvato con successo!")
            except Exception as e:
                st.error(f"Errore nel salvataggio: {e}")

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header("Storico Produzione")
    try:
        dati = conn.read(worksheet="Lotti")
        if not dati.empty:
            st.dataframe(dati)
            st.metric("Totale Lotti", len(dati))
        else:
            st.info("Nessun dato. Inserisci il primo lotto nella tab Ciclo di Vita.")
    except:
        st.warning("Assicurati che il foglio Google si chiami 'Lotti' in basso!")

# --- TAB 4: IA ---
with tab4:
    st.header("Analisi IA Migliorativa")
    foto = st.file_uploader("Scatta o carica foto", type=['jpg', 'png', 'jpeg'])
    if foto:
        img = Image.open(foto)
        st.image(img, width=300)
        if st.button("Analizza con IA"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(["Analizza questa pianta e dai consigli tecnici.", img])
            st.write(response.text)
