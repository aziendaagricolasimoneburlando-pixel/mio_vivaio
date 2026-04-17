# 🌱 Vivaio — App gestione colture

App Streamlit per gestire un vivaio: varietà, fasi di crescita, contenitori, materiali e calcolo costi/margini. Dati salvati su Google Sheet, deploy gratuito su Streamlit Cloud.

---

## 📋 Cosa ti serve (tutto gratis)

- Un account **GitHub** → https://github.com
- Un account **Google** (per Sheet + Cloud Console)
- Un account **Streamlit Cloud** → https://streamlit.io/cloud (entri con GitHub)

Tempo stimato: **15–20 minuti** la prima volta.

---

## 🚀 Guida completa passo-passo

### Passo 1 — Crea il repo su GitHub

1. Vai su https://github.com/new
2. Nome repo: `vivaio-app` (o quello che vuoi)
3. Impostalo **Private** (consigliato, visto che l'app è tua)
4. Crea il repo vuoto
5. Carica i file di questo progetto:
   - `app.py`
   - `requirements.txt`
   - `.gitignore`
   - `README.md` (questo file)
   - `secrets.toml.example`
   
   **Non caricare mai il vero `secrets.toml` su GitHub!** È escluso dal `.gitignore`.

Puoi farlo via interfaccia web ("Add file" → "Upload files") o da terminale se conosci git.

---

### Passo 2 — Crea il Google Sheet

1. Vai su https://sheets.google.com e crea un nuovo foglio vuoto
2. Chiamalo **Vivaio DB** (o come vuoi)
3. Copia l'**ID del foglio** dall'URL. L'URL è tipo:
   ```
   https://docs.google.com/spreadsheets/d/1aBcDe...XyZ/edit
                                        └───── questo è l'ID ─────┘
   ```
4. Salvalo da parte, ti servirà tra poco.

**Nota:** non serve creare tu i fogli interni (varieta, contenitori, ecc.). L'app li crea automaticamente al primo avvio.

---

### Passo 3 — Crea il Service Account Google (10 min)

Questo ti dà una "identità robot" che può scrivere sul foglio senza login.

1. Vai su https://console.cloud.google.com/
2. In alto crea un **nuovo progetto** (nome: "vivaio" o simile) e selezionalo
3. Menu → **APIs & Services** → **Library**
4. Cerca e abilita queste due API (una per volta, clicca "Enable"):
   - **Google Sheets API**
   - **Google Drive API**
5. Menu → **APIs & Services** → **Credentials**
6. In alto clicca **+ CREATE CREDENTIALS** → **Service account**
7. Compila:
   - Name: `vivaio-app`
   - Role: lascia vuoto (premi "Continue")
   - Clicca "Done"
8. Nella lista dei Service Account, **clicca su quello appena creato**
9. Tab **Keys** → **Add Key** → **Create new key** → formato **JSON** → **Create**
10. Si scarica un file `.json`. **Custodiscilo bene.**
11. Apri il file JSON con un editor di testo e nota il valore di `client_email`. È tipo:
    ```
    vivaio-app@vivaio-123456.iam.gserviceaccount.com
    ```

### Passo 4 — Condividi il foglio col Service Account

1. Torna al tuo Google Sheet "Vivaio DB"
2. Clicca **Condividi** (in alto a destra)
3. Incolla l'email `client_email` del service account (quella `vivaio-app@...iam.gserviceaccount.com`)
4. Dagli il ruolo **Editor**
5. **Togli la spunta** "Notifica le persone" (tanto è un robot)
6. Clicca **Condividi**

---

### Passo 5 — Deploy su Streamlit Cloud

1. Vai su https://share.streamlit.io e fai login con GitHub
2. Clicca **Create app** → **Deploy a public app from GitHub**
3. Seleziona:
   - **Repository**: il tuo `vivaio-app`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **Non cliccare ancora Deploy!** Prima → **Advanced settings** → vai alla sezione **Secrets**
5. Nel box dei secrets incolla questo (compilando i valori):

   ```toml
   app_password = "la-tua-password"
   sheet_id = "incolla-qui-l-ID-del-foglio"

   [gcp_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "vivaio-app@....iam.gserviceaccount.com"
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."
   universe_domain = "googleapis.com"
   ```

   **Come riempire la sezione `[gcp_service_account]`**: apri il file JSON che hai scaricato dal Service Account, e copia ogni valore nelle righe corrispondenti. Le virgolette sono importanti. Per `private_key` **mantieni i `\n`** così come sono nel JSON (Streamlit li interpreta correttamente).

6. Clicca **Save** → poi **Deploy**

Dopo 1-2 minuti l'app è online. L'URL è tipo `https://tuo-nome-vivaio-app.streamlit.app`

---

## 🔒 Sicurezza

- **Password**: al primo accesso l'app chiede la password che hai impostato in `app_password`. Solo tu la conosci.
- **Secrets**: sono salvati su Streamlit Cloud, **mai nel repo GitHub**. Il `.gitignore` protegge da errori.
- **Foglio Google**: rimane privato sul tuo account. Solo tu e il service account possono accederci.

---

## 🛠 Uso dell'app

Prima configurazione consigliata:

1. Vai nella sezione **Materiali** → apri **Terriccio** → aggiungi un acquisto (data, quantità in L, totale €)
2. Aggiungi acquisti per altri materiali che usi (concimi, acqua, ecc.)
3. Vai in **Contenitori** → aggiungi alveoli e vasetti con il loro volume in ml
4. Vai in **Varietà** → aggiungi la prima coltura, scegli un preset di fasi, seleziona i contenitori usati
5. Apri la **Dashboard** per vedere lo stato generale

Il costo per piantina si calcola automaticamente dai contenitori, dal terriccio e dai consumi che inserisci.

---

## 🐛 Problemi comuni

**"Errore connessione Google Sheet"**
→ Controlla di aver condiviso il foglio col service account come Editor. Controlla che `sheet_id` sia corretto.

**"API not enabled"**
→ Torna su Google Cloud Console e verifica che Google Sheets API e Google Drive API siano abilitate nel tuo progetto.

**"Password errata" ma ho inserito quella giusta**
→ Controlla che `app_password` in Secrets sia esattamente quella che digiti (occhio a spazi e maiuscole).

**L'app è lenta nel salvare**
→ Normale: ogni salvataggio scrive sul Google Sheet (servono 1-2 secondi). È il prezzo della persistenza gratis.

**Voglio cambiare la password**
→ Streamlit Cloud → la tua app → Settings → Secrets → modifica `app_password` → l'app si riavvia da sola.

---

## 🔧 Sviluppo in locale (opzionale)

Se vuoi provare l'app sul tuo computer prima di deploy:

```bash
# Clona il repo
git clone https://github.com/TUO-USER/vivaio-app.git
cd vivaio-app

# Installa dipendenze
pip install -r requirements.txt

# Crea la cartella dei secrets
mkdir .streamlit
cp secrets.toml.example .streamlit/secrets.toml
# Modifica .streamlit/secrets.toml con i tuoi valori

# Avvia
streamlit run app.py
```

---

## 📦 Struttura dati (Google Sheet)

L'app crea automaticamente 5 fogli:

- **varieta**: colture con categoria, data semina, quantità, prezzo. Fasi/note/consumi in JSON compatto.
- **contenitori**: alveoli/vasetti con volume e costo
- **materiali**: lista materiali (terriccio, acqua, manodopera, +custom)
- **acquisti**: storico acquisti, una riga per acquisto, legati al materiale
- **settings**: configurazione (regola prezzo: media ponderata / ultimo / max)

Puoi aprire il Google Sheet e vedere/modificare i dati a mano in qualsiasi momento (utile per backup o bulk edit).

---

Buon vivaio! 🌱
