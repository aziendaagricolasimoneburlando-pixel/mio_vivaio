import streamlit as st
import pandas as pd
from datetime import datetime
import requests

st.set_page_config(page_title="AgriSmart Vivaio", layout="wide")

# --- CONFIGURAZIONE LINK ---
# Sostituisci solo l'ID tra le due parti del link se diverso
SHEET_ID = "1L_4hrKZ5UMgMmgx0gXtcySPG2N95c15MNcp2quy8-Xo"
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

st.title("🌱 AgriSmart: Gestione Vivaio")

tab1, tab2 = st.tabs(["📊 Dashboard", "📅 Registra Semina"])

with tab2:
    st.header("Nuova Semina")
    with st.form("my_form"):
        v = st.text_input("Varietà")
        d = st.date_input("Data", datetime.now())
        s = st.number_input("Semi", value=100)
        submit = st.form_submit_button("Salva")
        
        if submit:
            # Per la scrittura, visto che Google blocca le app, 
            # usiamo un trucco: ti genero il link per aggiungere i dati velocemente
            st.warning("Per scrivere i dati in sicurezza senza pagare Google Cloud, clicca il tasto qui sotto:")
            # Creiamo un link che ti apre il foglio già pronto
            st.link_button("Apri Foglio per Inserire", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

with tab1:
    st.header("Situazione Attuale")
    try:
        # Legge i dati in tempo reale dal foglio pubblico
        df = pd.read_csv(URL_CSV)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error("Non riesco a leggere i dati. Assicurati che il foglio sia 'Pubblico' (Chiunque abbia il link può visualizzare).")
