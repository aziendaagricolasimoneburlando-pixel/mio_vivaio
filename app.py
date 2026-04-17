import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="AgriSmart Vivaio", layout="wide")

# CONNESSIONE DIRETTA ALL'URL
conn = st.connection("gsheets", type=GSheetsConnection)

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.title("🌱 AgriSmart: Gestione Vivaio")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📅 Ciclo di Vita", "💰 Gestione Costi", "👁️ IA Agronomo"])

with tab2:
    st.header("Registra Nuova Semina")
    with st.form("form_semina"):
        v = st.text_input("Nome Varietà")
        d = st.date_input("Data Semina", datetime.now())
        s = st.number_input("Numero Semi", min_value=1, value=100)
        n = st.number_input("Piantine Nate", value=0)
        c = st.number_input("Costo totale (€)", value=0.0)
        submit = st.form_submit_button("Salva nel Database")

        if submit:
            try:
                # Legge il foglio usando l'URL dei secrets
                df = conn.read(worksheet="Lotti", ttl=0)
                
                nuovo_dato = pd.DataFrame([{
                    "Varietà": v, "Data_Semina": str(d), 
                    "Semi": s, "Nati": n, "Costo_Totale": c
                }])
                
                df_finale = pd.concat([df, nuovo_dato], ignore_index=True)
                conn.update(worksheet="Lotti", data=df_finale)
                
                st.success("✅ Salvato con successo!")
                st.balloons()
            except Exception as e:
                st.error(f"Errore: {e}")
# ... il resto del codice rimane uguale

with tab1:
    st.header("Storico Produzione")
    try:
        storico = conn.read(worksheet="Lotti", ttl=0)
        st.dataframe(storico, use_container_width=True)
    except:
        st.info("Nessun dato trovato o foglio non configurato.")

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
