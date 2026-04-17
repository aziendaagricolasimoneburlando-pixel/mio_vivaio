"""
Vivaio — Gestione colture
App Streamlit con storage su Google Sheets.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import json
import uuid
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Vivaio",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, label, button, div {
        font-family: 'Fraunces', Georgia, serif !important;
    }
    .stApp { background: #f7f3ea; }
    h1, h2, h3 { font-style: italic; letter-spacing: -0.01em; color: #1e2a1c; }
    .main-header {
        background: #2d4a2b; color: #e8dcc4;
        padding: 18px 20px; border-radius: 14px; margin-bottom: 20px;
    }
    .main-header h1 { color: #e8dcc4 !important; margin: 0; font-size: 24px; }
    .main-header .sub {
        font-size: 11px; color: rgba(232,220,196,0.7);
        text-transform: uppercase; letter-spacing: 0.15em; margin-top: 2px;
    }
    .card { background: #fff; border: 1px solid #d9d0b8; border-radius: 14px; padding: 14px; margin-bottom: 10px; }
    .card-orto { border-top: 3px solid #607e3a; }
    .card-arom { border-top: 3px solid #b8562f; }
    .card-fiori { border-top: 3px solid #c48a2a; }
    .fase-done { background: #e0ead0; border-radius: 8px; padding: 10px; margin-bottom: 6px; }
    .fase-current { background: #f5e3bc; border: 1px solid #c48a2a; border-radius: 8px; padding: 10px; margin-bottom: 6px; }
    .fase-future { background: #fff; border: 1px solid #e8e0cd; border-radius: 8px; padding: 10px; margin-bottom: 6px; }
    .stat-box { background: #fff; border: 1px solid #d9d0b8; border-radius: 14px; padding: 14px; text-align: left; }
    .stat-lbl { font-size: 10px; text-transform: uppercase; letter-spacing: 0.15em; color: #8a907e; }
    .stat-val { font-size: 22px; font-weight: 500; margin-top: 4px; font-style: italic; color: #1e2a1c; }
    .hero {
        background: linear-gradient(135deg, #2d4a2b 0%, #1a3018 100%);
        color: #e8dcc4; border-radius: 14px; padding: 20px; margin-bottom: 14px;
    }
    .hero-lbl { font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em; opacity: 0.6; }
    .hero-val { font-size: 42px; font-weight: 500; font-style: italic; margin-top: 4px; }
    .hero-sub { font-size: 13px; opacity: 0.8; margin-top: 2px; }
    .stButton>button {
        border-radius: 8px; font-style: italic; border: 1px solid #d9d0b8;
        background: #fff; color: #1e2a1c;
    }
    .stButton>button:hover { border-color: #2d4a2b; color: #2d4a2b; }
    [data-testid="stSidebar"] { background: #ede6d3; }
    .section-title {
        font-size: 11px; text-transform: uppercase; letter-spacing: 0.18em;
        color: #8a907e; margin: 20px 0 10px; font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# COSTANTI
# ============================================================
FASI_PRESETS = {
    "standard": [
        {"key": "semina", "label": "Semina", "daysFrom": 0},
        {"key": "germinazione", "label": "Germinazione", "daysFrom": 7},
        {"key": "cascetta", "label": "Prima cascetta", "daysFrom": 20},
        {"key": "alveolo", "label": "Trapianto in alveolo", "daysFrom": 35},
        {"key": "vasetto", "label": "Trapianto in vasetto", "daysFrom": 55},
        {"key": "vendita", "label": "Pronto vendita", "daysFrom": 70},
    ],
    "aromatica": [
        {"key": "semina", "label": "Semina", "daysFrom": 0},
        {"key": "germinazione", "label": "Germinazione", "daysFrom": 14},
        {"key": "alveolo", "label": "Trapianto in alveolo", "daysFrom": 30},
        {"key": "vasetto", "label": "Trapianto in vasetto", "daysFrom": 60},
        {"key": "vendita", "label": "Pronto vendita", "daysFrom": 90},
    ],
    "insalata": [
        {"key": "semina", "label": "Semina", "daysFrom": 0},
        {"key": "germinazione", "label": "Germinazione", "daysFrom": 5},
        {"key": "alveolo", "label": "Trapianto in alveolo", "daysFrom": 15},
        {"key": "vendita", "label": "Pronto vendita", "daysFrom": 35},
    ],
}

DEFAULT_MATERIALI = [
    {"id": "terriccio", "name": "Terriccio", "unit": "L", "system": True},
    {"id": "acqua", "name": "Acqua / energia", "unit": "pz", "system": True},
    {"id": "manodopera", "name": "Manodopera", "unit": "pz", "system": True},
]

CATEGORIE = {"orto": "Orticole", "arom": "Aromatiche", "fiori": "Fiori"}
SHEETS = ["varieta", "contenitori", "materiali", "acquisti", "settings"]


# ============================================================
# GOOGLE SHEETS
# ============================================================
@st.cache_resource
def get_gsheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["sheet_id"])

    existing = [ws.title for ws in sheet.worksheets()]
    for name in SHEETS:
        if name not in existing:
            sheet.add_worksheet(title=name, rows=100, cols=20)
    return sheet


def read_sheet(tab_name):
    sheet = get_gsheet()
    ws = sheet.worksheet(tab_name)
    return ws.get_all_records()


def write_sheet(tab_name, rows, headers=None):
    sheet = get_gsheet()
    ws = sheet.worksheet(tab_name)
    ws.clear()
    if not rows:
        if headers:
            ws.update([headers])
        return
    if headers is None:
        headers = list(rows[0].keys())
    data = [headers]
    for r in rows:
        data.append([r.get(h, "") for h in headers])
    ws.update(data)


# ============================================================
# DATA LAYER
# ============================================================
def load_state():
    if "loaded" in st.session_state:
        return

    try:
        varieta_raw = read_sheet("varieta")
        contenitori_raw = read_sheet("contenitori")
        materiali_raw = read_sheet("materiali")
        acquisti_raw = read_sheet("acquisti")
        settings_raw = read_sheet("settings")
    except Exception as e:
        st.error(f"Errore connessione Google Sheet: {e}")
        st.stop()

    varieta = []
    for r in varieta_raw:
        try:
            extra = json.loads(r.get("data_json", "{}")) if r.get("data_json") else {}
        except Exception:
            extra = {}
        varieta.append({
            "id": r.get("id"),
            "nome": r.get("nome", ""),
            "varieta_nome": r.get("varieta_nome", ""),
            "categoria": r.get("categoria", "orto"),
            "data_semina": r.get("data_semina", ""),
            "quantita": int(r.get("quantita", 0) or 0),
            "prezzoVendita": float(r.get("prezzoVendita", 0) or 0),
            "fasi": extra.get("fasi", []),
            "note": extra.get("note", []),
            "consumi": extra.get("consumi", {}),
            "containers": extra.get("containers", []),
            "costiExtra": extra.get("costiExtra", {}),
        })

    contenitori = []
    for r in contenitori_raw:
        contenitori.append({
            "id": r.get("id"),
            "name": r.get("name", ""),
            "type": r.get("type", "alveolo"),
            "volume": float(r.get("volume", 0) or 0),
            "materialId": r.get("materialId") or None,
            "unitCost": float(r.get("unitCost", 0) or 0),
        })

    materiali = []
    for r in materiali_raw:
        materiali.append({
            "id": r.get("id"),
            "name": r.get("name", ""),
            "unit": r.get("unit", "pz"),
            "system": str(r.get("system", "")).lower() in ("true", "1", "yes"),
        })
    if not materiali:
        materiali = [dict(m) for m in DEFAULT_MATERIALI]

    acquisti_by_mat = {}
    for r in acquisti_raw:
        mid = r.get("materialId")
        if not mid:
            continue
        qty = float(r.get("qty", 0) or 0)
        total = float(r.get("total", 0) or 0)
        acquisti_by_mat.setdefault(mid, []).append({
            "date": r.get("date", ""),
            "supplier": r.get("supplier", ""),
            "qty": qty, "total": total,
            "unitCost": total / qty if qty > 0 else 0,
        })
    for m in materiali:
        m["acquisti"] = acquisti_by_mat.get(m["id"], [])

    pricing_rule = "weighted"
    for r in settings_raw:
        if r.get("key") == "pricingRule":
            pricing_rule = r.get("value", "weighted")

    st.session_state.varieta = varieta
    st.session_state.contenitori = contenitori
    st.session_state.materiali = materiali
    st.session_state.pricingRule = pricing_rule
    st.session_state.loaded = True


def save_varieta():
    rows = []
    for v in st.session_state.varieta:
        rows.append({
            "id": v["id"], "nome": v["nome"], "varieta_nome": v["varieta_nome"],
            "categoria": v["categoria"], "data_semina": v["data_semina"],
            "quantita": v["quantita"], "prezzoVendita": v["prezzoVendita"],
            "data_json": json.dumps({
                "fasi": v.get("fasi", []), "note": v.get("note", []),
                "consumi": v.get("consumi", {}), "containers": v.get("containers", []),
                "costiExtra": v.get("costiExtra", {}),
            }, ensure_ascii=False),
        })
    write_sheet("varieta", rows,
        ["id", "nome", "varieta_nome", "categoria", "data_semina", "quantita", "prezzoVendita", "data_json"])


def save_contenitori():
    rows = [{
        "id": c["id"], "name": c["name"], "type": c["type"],
        "volume": c["volume"], "materialId": c.get("materialId") or "",
        "unitCost": c.get("unitCost", 0),
    } for c in st.session_state.contenitori]
    write_sheet("contenitori", rows,
        ["id", "name", "type", "volume", "materialId", "unitCost"])


def save_materiali():
    rows, acquisti_rows = [], []
    for m in st.session_state.materiali:
        rows.append({
            "id": m["id"], "name": m["name"], "unit": m["unit"],
            "system": "true" if m.get("system") else "false",
        })
        for a in m.get("acquisti", []):
            acquisti_rows.append({
                "materialId": m["id"], "date": a.get("date", ""),
                "supplier": a.get("supplier", ""),
                "qty": a.get("qty", 0), "total": a.get("total", 0),
            })
    write_sheet("materiali", rows, ["id", "name", "unit", "system"])
    write_sheet("acquisti", acquisti_rows, ["materialId", "date", "supplier", "qty", "total"])


def save_settings():
    rows = [{"key": "pricingRule", "value": st.session_state.get("pricingRule", "weighted")}]
    write_sheet("settings", rows, ["key", "value"])


# ============================================================
# LOGICA BUSINESS
# ============================================================
def get_unit_cost(material_id):
    m = next((x for x in st.session_state.materiali if x["id"] == material_id), None)
    if not m or not m.get("acquisti"):
        return 0
    rule = st.session_state.get("pricingRule", "weighted")
    acq = m["acquisti"]
    if rule == "last":
        return sorted(acq, key=lambda a: a["date"], reverse=True)[0]["unitCost"]
    if rule == "max":
        return max(a["unitCost"] for a in acq)
    tot_qty = sum(a["qty"] for a in acq)
    tot_spent = sum(a["total"] for a in acq)
    return tot_spent / tot_qty if tot_qty else 0


def calc_container_cost(container):
    terriccio_unit = get_unit_cost("terriccio")
    terriccio_cost = terriccio_unit * (container.get("volume", 0) or 0)
    if container.get("materialId"):
        cont_cost = get_unit_cost(container["materialId"])
    else:
        cont_cost = container.get("unitCost", 0) or 0
    return {
        "terriccio": terriccio_cost, "volume": container.get("volume", 0) or 0,
        "container": cont_cost, "total": terriccio_cost + cont_cost,
    }


def calc_food_cost(variety):
    breakdown = []
    total = 0
    terriccio_unit = get_unit_cost("terriccio")

    for cid in variety.get("containers", []):
        c = next((x for x in st.session_state.contenitori if x["id"] == cid), None)
        if not c:
            continue
        cc = calc_container_cost(c)
        breakdown.append({"label": c["name"], "detail": "contenitore", "cost": cc["container"]})
        if cc["volume"] > 0:
            breakdown.append({
                "label": "↳ terriccio",
                "detail": f"{cc['volume']*1000:.0f} ml × € {terriccio_unit:.4f}/L".replace(".", ","),
                "cost": cc["terriccio"],
            })
        total += cc["total"]

    for mat_id, qty in (variety.get("consumi") or {}).items():
        try:
            qty = float(qty)
        except Exception:
            qty = 0
        if qty > 0:
            mat = next((x for x in st.session_state.materiali if x["id"] == mat_id), None)
            if mat:
                unit_cost = get_unit_cost(mat_id)
                cost = unit_cost * qty
                breakdown.append({
                    "label": mat["name"],
                    "detail": f"{qty} {mat['unit']} × € {unit_cost:.4f}/{mat['unit']}".replace(".", ","),
                    "cost": cost,
                })
                total += cost

    for k, v in (variety.get("costiExtra") or {}).items():
        try:
            v = float(v)
        except Exception:
            v = 0
        if v > 0:
            breakdown.append({"label": k.capitalize(), "detail": "inserito a mano", "cost": v})
            total += v

    return {"breakdown": breakdown, "total": total}


def get_fasi_with_dates(variety):
    data_semina_str = variety.get("data_semina")
    if not data_semina_str:
        return []
    try:
        start = datetime.strptime(data_semina_str, "%Y-%m-%d").date()
    except Exception:
        return []
    today = date.today()
    fasi = variety.get("fasi") or []
    result = []
    for f in fasi:
        d = start + timedelta(days=f["daysFrom"])
        status = "done" if d <= today else "future"
        result.append({**f, "date": d, "status": status})
    last_done_idx = -1
    for i, f in enumerate(result):
        if f["status"] == "done":
            last_done_idx = i
    if 0 <= last_done_idx < len(result) - 1:
        result[last_done_idx]["status"] = "current"
    return result


def next_upcoming_fase(variety):
    fasi = get_fasi_with_dates(variety)
    for f in fasi:
        if f["status"] == "future":
            return f
    return None
  # ============================================================
# PAGINE
# ============================================================
def page_dashboard():
    st.markdown('<div class="main-header"><h1>📊 Dashboard</h1><div class="sub">Situazione colture</div></div>', unsafe_allow_html=True)

    varieta = st.session_state.varieta
    total_piante = sum(v["quantita"] for v in varieta)
    n_varieta = len(varieta)

    today = date.today()
    soon_limit = today + timedelta(days=7)
    pronte = 0
    for v in varieta:
        fasi = get_fasi_with_dates(v)
        if fasi and fasi[-1]["status"] != "done":
            if today <= fasi[-1]["date"] <= soon_limit:
                pronte += v["quantita"]

    investito = 0
    valore = 0
    for v in varieta:
        fc = calc_food_cost(v)
        investito += fc["total"] * v["quantita"]
        valore += v["prezzoVendita"] * v["quantita"]

    st.markdown(f"""
    <div class="hero">
        <div class="hero-lbl">Piantine in coltura</div>
        <div class="hero-val">{total_piante}</div>
        <div class="hero-sub">{n_varieta} varietà attiv{'e' if n_varieta != 1 else 'a'}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-lbl">Pronte in 7 gg</div><div class="stat-val">{pronte}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-lbl">Varietà attive</div><div class="stat-val">{n_varieta}</div></div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-lbl">Investito</div><div class="stat-val">€ {investito:.2f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-box"><div class="stat-lbl">Valore a vendita</div><div class="stat-val">€ {valore:.2f}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Prossime fasi</div>', unsafe_allow_html=True)
    upcoming = []
    for v in varieta:
        nxt = next_upcoming_fase(v)
        if nxt:
            upcoming.append((v, nxt))
    upcoming.sort(key=lambda x: x[1]["date"])

    if not upcoming:
        st.caption("Nessuna fase in programma")
    else:
        for v, f in upcoming[:10]:
            days_to = (f["date"] - today).days
            if days_to < 0:
                tag = f"🔴 in ritardo di {-days_to} gg"
            elif days_to == 0:
                tag = "🟠 oggi"
            elif days_to <= 3:
                tag = f"🟠 fra {days_to} gg"
            else:
                tag = f"⚪ fra {days_to} gg"
            st.markdown(f"""
            <div class="card">
                <b>{v['nome']}</b> — <i>{f['label']}</i><br>
                <small>{f['date'].strftime('%d %b %Y')} · {tag}</small>
            </div>
            """, unsafe_allow_html=True)


def page_varieta():
    st.markdown('<div class="main-header"><h1>🌱 Vivaio</h1><div class="sub">Le tue colture</div></div>', unsafe_allow_html=True)

    cat_options = ["all"] + list(CATEGORIE.keys())
    cat_labels = {"all": "Tutte", **CATEGORIE}
    cat = st.radio("Categoria", cat_options, format_func=lambda x: cat_labels[x], horizontal=True, label_visibility="collapsed")

    varieta = st.session_state.varieta
    if cat != "all":
        varieta = [v for v in varieta if v["categoria"] == cat]

    if st.button("➕ Nuova varietà", use_container_width=True, type="primary"):
        st.session_state.editing_variety = None
        st.session_state.show_variety_form = True
        st.rerun()

    if st.session_state.get("show_variety_form"):
        variety_form()
        return

    if not varieta:
        st.info("Nessuna varietà ancora. Clicca sopra per iniziare.")
        return

    for v in varieta:
        nxt = next_upcoming_fase(v)
        nxt_txt = f"→ {nxt['label']} il {nxt['date'].strftime('%d %b')}" if nxt else "Completata"
        cat_cls = f"card-{v['categoria']}"
        cat_lbl = CATEGORIE.get(v["categoria"], "")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
            <div class="card {cat_cls}">
                <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:#8a907e;">{cat_lbl}</div>
                <div style="font-size:18px;font-style:italic;font-weight:500;">{v['nome']}</div>
                <div style="font-size:12px;color:#4a5948;">{v.get('varieta_nome','')}</div>
                <div style="margin-top:8px;font-size:12px;color:#4a5948;">
                    <b>{v['quantita']}</b> piantine · {nxt_txt}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("Apri", key=f"open_{v['id']}", use_container_width=True):
                st.session_state.detail_variety_id = v["id"]
                st.rerun()


def variety_form():
    editing = st.session_state.get("editing_variety")
    v = None
    if editing:
        v = next((x for x in st.session_state.varieta if x["id"] == editing), None)

    st.markdown("### " + ("Modifica varietà" if v else "Nuova varietà"))

    with st.form("variety_form"):
        nome = st.text_input("Nome coltura (es. Pomodoro)", value=v["nome"] if v else "")
        varieta_nome = st.text_input("Varietà (es. Cuore di Bue)", value=v["varieta_nome"] if v else "")
        categoria = st.selectbox("Categoria", list(CATEGORIE.keys()),
            format_func=lambda x: CATEGORIE[x],
            index=list(CATEGORIE.keys()).index(v["categoria"]) if v else 0)
        data_semina = st.date_input("Data semina",
            value=datetime.strptime(v["data_semina"], "%Y-%m-%d").date() if v and v.get("data_semina") else date.today())
        quantita = st.number_input("Quantità piantine", min_value=0, step=1, value=v["quantita"] if v else 0)
        prezzo = st.number_input("Prezzo vendita unitario (€)", min_value=0.0, step=0.1,
            value=v["prezzoVendita"] if v else 0.0, format="%.2f")

        preset = st.selectbox("Preset fasi", list(FASI_PRESETS.keys()),
            format_func=lambda x: {"standard": "Standard (70 gg)", "aromatica": "Aromatica (90 gg)", "insalata": "Insalata (35 gg)"}[x])

        st.markdown("**Contenitori usati**")
        selected_containers = []
        if st.session_state.contenitori:
            for c in st.session_state.contenitori:
                default = v and c["id"] in (v.get("containers") or [])
                if st.checkbox(f"{c['name']} ({c['volume']*1000:.0f} ml)", value=default, key=f"cont_{c['id']}"):
                    selected_containers.append(c["id"])
        else:
            st.caption("Nessun contenitore. Aggiungine uno dalla sezione Contenitori.")

        st.markdown("**Consumi per piantina** (lascia 0 se non applicabile)")
        consumi = {}
        for m in st.session_state.materiali:
            if m["id"] == "terriccio":
                continue
            default_val = float((v.get("consumi") or {}).get(m["id"], 0)) if v else 0.0
            consumi[m["id"]] = st.number_input(
                f"{m['name']} ({m['unit']})",
                min_value=0.0, step=0.01, value=default_val, format="%.3f",
                key=f"cons_{m['id']}")

        seme_default = float((v.get("costiExtra") or {}).get("seme", 0)) if v else 0.0
        costo_seme = st.number_input("Costo seme per piantina (€)",
            min_value=0.0, step=0.01, value=seme_default, format="%.3f")

        c1, c2 = st.columns(2)
        with c1:
            submit = st.form_submit_button("💾 Salva", use_container_width=True, type="primary")
        with c2:
            cancel = st.form_submit_button("Annulla", use_container_width=True)

    if cancel:
        st.session_state.show_variety_form = False
        st.session_state.editing_variety = None
        st.rerun()

    if submit:
        if not nome.strip():
            st.error("Il nome è obbligatorio")
            return
        fasi_preset = FASI_PRESETS[preset]
        if v:
            v["nome"] = nome.strip()
            v["varieta_nome"] = varieta_nome.strip()
            v["categoria"] = categoria
            v["data_semina"] = data_semina.isoformat()
            v["quantita"] = int(quantita)
            v["prezzoVendita"] = float(prezzo)
            v["containers"] = selected_containers
            v["consumi"] = consumi
            v["costiExtra"] = {"seme": float(costo_seme)}
            v["fasi"] = [dict(f) for f in fasi_preset]
        else:
            st.session_state.varieta.append({
                "id": "v_" + uuid.uuid4().hex[:10],
                "nome": nome.strip(), "varieta_nome": varieta_nome.strip(),
                "categoria": categoria, "data_semina": data_semina.isoformat(),
                "quantita": int(quantita), "prezzoVendita": float(prezzo),
                "fasi": [dict(f) for f in fasi_preset],
                "note": [], "consumi": consumi,
                "containers": selected_containers,
                "costiExtra": {"seme": float(costo_seme)},
            })

        with st.spinner("Salvataggio..."):
            save_varieta()

        st.session_state.show_variety_form = False
        st.session_state.editing_variety = None
        st.success("Varietà salvata")
        st.rerun()


def page_detail():
    vid = st.session_state.get("detail_variety_id")
    v = next((x for x in st.session_state.varieta if x["id"] == vid), None)
    if not v:
        st.session_state.detail_variety_id = None
        st.rerun()
        return

    col_back, col_edit, col_del = st.columns([2, 1, 1])
    with col_back:
        if st.button("← Torna alle varietà", use_container_width=True):
            st.session_state.detail_variety_id = None
            st.rerun()
    with col_edit:
        if st.button("✏️ Modifica", use_container_width=True):
            st.session_state.editing_variety = v["id"]
            st.session_state.show_variety_form = True
            st.session_state.detail_variety_id = None
            st.rerun()
    with col_del:
        if st.button("🗑️", use_container_width=True):
            st.session_state.confirm_delete = v["id"]
            st.rerun()

    if st.session_state.get("confirm_delete") == v["id"]:
        st.warning(f"Eliminare definitivamente **{v['nome']}**?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sì, elimina", type="primary", use_container_width=True):
                st.session_state.varieta = [x for x in st.session_state.varieta if x["id"] != v["id"]]
                with st.spinner("Salvataggio..."):
                    save_varieta()
                st.session_state.confirm_delete = None
                st.session_state.detail_variety_id = None
                st.rerun()
        with c2:
            if st.button("Annulla", use_container_width=True):
                st.session_state.confirm_delete = None
                st.rerun()

    st.markdown(f"""
    <div class="card card-{v['categoria']}">
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:#8a907e;">{CATEGORIE.get(v['categoria'],'')}</div>
        <h2 style="margin:0;">{v['nome']}</h2>
        <div style="font-size:13px;color:#4a5948;">{v.get('varieta_nome','')}</div>
        <div style="margin-top:12px;font-size:13px;color:#4a5948;">
            <b>{v['quantita']}</b> piantine · semina: <b>{v['data_semina']}</b> · vendita: <b>€ {v['prezzoVendita']:.2f}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Ciclo colturale</div>', unsafe_allow_html=True)
    fasi = get_fasi_with_dates(v)
    for f in fasi:
        cls = {"done": "fase-done", "current": "fase-current", "future": "fase-future"}[f["status"]]
        icon = {"done": "✓", "current": "●", "future": "○"}[f["status"]]
        st.markdown(f"""
        <div class="{cls}">
            <b>{icon} {f['label']}</b> — {f['date'].strftime('%d %b %Y')}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Costo per piantina</div>', unsafe_allow_html=True)
    fc = calc_food_cost(v)
    if not fc["breakdown"]:
        st.caption("Nessun costo rilevato. Configura contenitori, materiali e consumi.")
    else:
        for b in fc["breakdown"]:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{b['label']}**  \n<small style='color:#8a907e;font-style:italic;'>{b['detail']}</small>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='text-align:right;'>€ {b['cost']:.4f}</div>", unsafe_allow_html=True)

    totale = fc["total"]
    vendita = v["prezzoVendita"]
    margine = vendita - totale
    marg_pct = (margine / vendita * 100) if vendita > 0 else 0
    margine_tot = margine * v["quantita"]

    st.markdown(f"""
    <div style="background:#2d4a2b;color:#e8dcc4;border-radius:8px;padding:14px 16px;margin-top:10px;display:flex;justify-content:space-between;">
        <div><div style="font-size:11px;text-transform:uppercase;letter-spacing:0.15em;opacity:0.7;">Totale per piantina</div></div>
        <div style="font-size:22px;font-weight:500;">€ {totale:.3f}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-lbl">Vendita</div><div class="stat-val">€ {vendita:.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        color = "#5c7a38" if margine >= 0 else "#9a3b2e"
        st.markdown(f'<div class="stat-box"><div class="stat-lbl">Margine/pz</div><div class="stat-val" style="color:{color};">€ {margine:.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-lbl">Margine %</div><div class="stat-val">{marg_pct:.0f}%</div></div>', unsafe_allow_html=True)

    st.caption(f"Margine totale stimato: **€ {margine_tot:.2f}**")

    st.markdown('<div class="section-title">Note</div>', unsafe_allow_html=True)
    with st.expander("➕ Aggiungi nota"):
        with st.form(f"note_form_{v['id']}"):
            note_date = st.date_input("Data", value=date.today(), key=f"nd_{v['id']}")
            note_text = st.text_area("Nota", key=f"nt_{v['id']}")
            if st.form_submit_button("Aggiungi nota", type="primary"):
                if note_text.strip():
                    v.setdefault("note", []).append({"date": note_date.isoformat(), "text": note_text.strip()})
                    with st.spinner("Salvataggio..."):
                        save_varieta()
                    st.rerun()

    notes = v.get("note") or []
    if not notes:
        st.caption("Nessuna nota")
    else:
        for i, n in enumerate(sorted(notes, key=lambda x: x.get("date", ""), reverse=True)):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{n.get('date','')}** — {n.get('text','')}")
            with c2:
                if st.button("🗑", key=f"dn_{v['id']}_{i}"):
                    v["note"].remove(n)
                    with st.spinner("Salvataggio..."):
                        save_varieta()
                    st.rerun()
def page_contenitori():
    st.markdown('<div class="main-header"><h1>🪴 Contenitori</h1><div class="sub">Alveoli e vasetti</div></div>', unsafe_allow_html=True)
    st.caption("Alveoli e vasetti con il loro volume di terriccio. Il costo del terriccio viene calcolato in automatico.")

    if st.button("➕ Nuovo contenitore", use_container_width=True, type="primary"):
        st.session_state.editing_container = None
        st.session_state.show_container_form = True
        st.rerun()

    if st.session_state.get("show_container_form"):
        container_form()
        return

    if not st.session_state.contenitori:
        st.info("Nessun contenitore. Aggiungine uno per iniziare.")
        return

    for c in st.session_state.contenitori:
        cc = calc_container_cost(c)
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            st.markdown(f"""
            <div class="card">
                <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:#8a907e;">{c['type']}</div>
                <div style="font-size:16px;font-style:italic;font-weight:500;">{c['name']}</div>
                <div style="font-size:12px;color:#4a5948;margin-top:4px;">
                    Vol: <b>{c['volume']*1000:.0f} ml</b> · Costo tot: <b>€ {cc['total']:.3f}</b>
                    <br>Contenitore: € {cc['container']:.3f} + Terriccio: € {cc['terriccio']:.3f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("✏️", key=f"edc_{c['id']}"):
                st.session_state.editing_container = c["id"]
                st.session_state.show_container_form = True
                st.rerun()
        with c3:
            if st.button("🗑", key=f"dlc_{c['id']}"):
                st.session_state.confirm_delete_container = c["id"]
                st.rerun()

        if st.session_state.get("confirm_delete_container") == c["id"]:
            st.warning(f"Eliminare **{c['name']}**? Sarà rimosso dalle varietà che lo usano.")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Sì, elimina", type="primary", key=f"yes_{c['id']}"):
                    st.session_state.contenitori = [x for x in st.session_state.contenitori if x["id"] != c["id"]]
                    for v in st.session_state.varieta:
                        if c["id"] in (v.get("containers") or []):
                            v["containers"].remove(c["id"])
                    with st.spinner("Salvataggio..."):
                        save_contenitori()
                        save_varieta()
                    st.session_state.confirm_delete_container = None
                    st.rerun()
            with cc2:
                if st.button("Annulla", key=f"no_{c['id']}"):
                    st.session_state.confirm_delete_container = None
                    st.rerun()


def container_form():
    editing = st.session_state.get("editing_container")
    c = None
    if editing:
        c = next((x for x in st.session_state.contenitori if x["id"] == editing), None)

    st.markdown("### " + ("Modifica contenitore" if c else "Nuovo contenitore"))

    with st.form("container_form"):
        name = st.text_input("Nome (es. Alveolo 104 celle)", value=c["name"] if c else "")
        ctype = st.selectbox("Tipo", ["alveolo", "vasetto"],
            index=["alveolo", "vasetto"].index(c["type"]) if c and c.get("type") in ["alveolo", "vasetto"] else 0)
        volume_ml = st.number_input("Volume (ml) — quanto terriccio contiene una cella/vaso",
            min_value=0, step=1, value=int((c["volume"] * 1000) if c else 0))
        unit_cost = st.number_input("Costo unitario (€) del singolo contenitore",
            min_value=0.0, step=0.001,
            value=float(c.get("unitCost", 0)) if c else 0.0, format="%.4f")

        c1, c2 = st.columns(2)
        with c1:
            submit = st.form_submit_button("💾 Salva", use_container_width=True, type="primary")
        with c2:
            cancel = st.form_submit_button("Annulla", use_container_width=True)

    if cancel:
        st.session_state.show_container_form = False
        st.session_state.editing_container = None
        st.rerun()

    if submit:
        if not name.strip():
            st.error("Il nome è obbligatorio")
            return
        if c:
            c["name"] = name.strip()
            c["type"] = ctype
            c["volume"] = volume_ml / 1000
            c["unitCost"] = float(unit_cost)
        else:
            st.session_state.contenitori.append({
                "id": "c_" + uuid.uuid4().hex[:10],
                "name": name.strip(), "type": ctype,
                "volume": volume_ml / 1000, "materialId": None,
                "unitCost": float(unit_cost),
            })
        with st.spinner("Salvataggio..."):
            save_contenitori()
        st.session_state.show_container_form = False
        st.session_state.editing_container = None
        st.rerun()


def page_materiali():
    st.markdown('<div class="main-header"><h1>📦 Materiali</h1><div class="sub">Acquisti e costi</div></div>', unsafe_allow_html=True)
    st.caption("Registra ogni acquisto: terriccio, concimi, acqua, manodopera. Il costo unitario viene calcolato in automatico.")

    st.markdown('<div class="section-title">Metodo di calcolo costi</div>', unsafe_allow_html=True)
    rule_labels = {"weighted": "Media ponderata", "last": "Ultimo acquisto", "max": "Prezzo massimo"}
    rule_keys = list(rule_labels.keys())
    current_rule = st.session_state.get("pricingRule", "weighted")
    new_rule = st.radio("Regola prezzo", rule_keys,
        format_func=lambda x: rule_labels[x],
        index=rule_keys.index(current_rule),
        horizontal=True, label_visibility="collapsed")
    if new_rule != current_rule:
        st.session_state.pricingRule = new_rule
        save_settings()
        st.rerun()

    if st.button("➕ Nuovo materiale", use_container_width=True, type="primary"):
        st.session_state.editing_material = None
        st.session_state.show_material_form = True
        st.rerun()

    if st.session_state.get("show_material_form"):
        material_form()
        return

    if st.session_state.get("detail_material_id"):
        material_detail()
        return

    for m in st.session_state.materiali:
        unit_cost = get_unit_cost(m["id"])
        n_acq = len(m.get("acquisti", []))
        c1, c2 = st.columns([4, 1])
        with c1:
            tag = "sistema" if m.get("system") else "custom"
            st.markdown(f"""
            <div class="card">
                <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:#8a907e;">{tag}</div>
                <div style="font-size:16px;font-style:italic;font-weight:500;">{m['name']}</div>
                <div style="font-size:12px;color:#4a5948;margin-top:4px;">
                    Unità: <b>{m['unit']}</b> · Acquisti: <b>{n_acq}</b> · Costo: <b>€ {unit_cost:.4f}/{m['unit']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("Apri", key=f"om_{m['id']}", use_container_width=True):
                st.session_state.detail_material_id = m["id"]
                st.rerun()


def material_form():
    editing = st.session_state.get("editing_material")
    m = None
    if editing:
        m = next((x for x in st.session_state.materiali if x["id"] == editing), None)

    st.markdown("### " + ("Modifica materiale" if m else "Nuovo materiale"))

    with st.form("material_form"):
        name = st.text_input("Nome", value=m["name"] if m else "")
        unit = st.text_input("Unità (es. L, kg, pz)", value=m["unit"] if m else "pz")

        c1, c2 = st.columns(2)
        with c1:
            submit = st.form_submit_button("💾 Salva", use_container_width=True, type="primary")
        with c2:
            cancel = st.form_submit_button("Annulla", use_container_width=True)

    if cancel:
        st.session_state.show_material_form = False
        st.session_state.editing_material = None
        st.rerun()

    if submit:
        if not name.strip():
            st.error("Il nome è obbligatorio")
            return
        if m:
            m["name"] = name.strip()
            m["unit"] = unit.strip()
        else:
            st.session_state.materiali.append({
                "id": "m_" + uuid.uuid4().hex[:10],
                "name": name.strip(), "unit": unit.strip(),
                "system": False, "acquisti": [],
            })
        with st.spinner("Salvataggio..."):
            save_materiali()
        st.session_state.show_material_form = False
        st.session_state.editing_material = None
        st.rerun()


def material_detail():
    mid = st.session_state.detail_material_id
    m = next((x for x in st.session_state.materiali if x["id"] == mid), None)
    if not m:
        st.session_state.detail_material_id = None
        st.rerun()
        return

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        if st.button("← Tutti i materiali", use_container_width=True):
            st.session_state.detail_material_id = None
            st.rerun()
    with c2:
        if not m.get("system") and st.button("✏️ Modifica", use_container_width=True):
            st.session_state.editing_material = m["id"]
            st.session_state.show_material_form = True
            st.session_state.detail_material_id = None
            st.rerun()
    with c3:
        if not m.get("system") and st.button("🗑", use_container_width=True):
            st.session_state.confirm_del_mat = m["id"]
            st.rerun()

    if st.session_state.get("confirm_del_mat") == m["id"]:
        st.warning(f"Eliminare **{m['name']}** e tutti i suoi acquisti?")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Sì elimina", type="primary", key="dm_yes"):
                st.session_state.materiali = [x for x in st.session_state.materiali if x["id"] != m["id"]]
                with st.spinner("Salvataggio..."):
                    save_materiali()
                st.session_state.confirm_del_mat = None
                st.session_state.detail_material_id = None
                st.rerun()
        with cc2:
            if st.button("Annulla", key="dm_no"):
                st.session_state.confirm_del_mat = None
                st.rerun()

    unit_cost = get_unit_cost(m["id"])
    st.markdown(f"""
    <div class="card">
        <h2 style="margin:0;">{m['name']}</h2>
        <div style="font-size:13px;color:#4a5948;margin-top:6px;">
            Unità: <b>{m['unit']}</b> · Costo calcolato: <b>€ {unit_cost:.4f}/{m['unit']}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Nuovo acquisto</div>', unsafe_allow_html=True)
    with st.form(f"purchase_form_{m['id']}"):
        pc1, pc2 = st.columns(2)
        with pc1:
            p_date = st.date_input("Data acquisto", value=date.today())
            p_qty = st.number_input(f"Quantità ({m['unit']})", min_value=0.0, step=0.1, format="%.3f")
        with pc2:
            p_supplier = st.text_input("Fornitore")
            p_total = st.number_input("Totale speso (€)", min_value=0.0, step=0.1, format="%.2f")
        if st.form_submit_button("💾 Aggiungi acquisto", type="primary", use_container_width=True):
            if p_qty <= 0 or p_total <= 0:
                st.error("Quantità e totale devono essere maggiori di zero")
            else:
                m.setdefault("acquisti", []).append({
                    "date": p_date.isoformat(),
                    "supplier": p_supplier.strip(),
                    "qty": float(p_qty), "total": float(p_total),
                    "unitCost": float(p_total) / float(p_qty),
                })
                with st.spinner("Salvataggio..."):
                    save_materiali()
                st.rerun()

    st.markdown('<div class="section-title">Storico acquisti</div>', unsafe_allow_html=True)
    acq = sorted(m.get("acquisti", []), key=lambda x: x.get("date", ""), reverse=True)
    if not acq:
        st.caption("Nessun acquisto registrato")
    else:
        avg = unit_cost
        for i, a in enumerate(acq):
            diff_pct = ((a["unitCost"] - avg) / avg * 100) if avg else 0
            tag = ""
            if abs(diff_pct) > 5:
                color = "#9a3b2e" if diff_pct > 0 else "#5c7a38"
                tag = f'<span style="color:{color};font-size:11px;">({diff_pct:+.0f}%)</span>'
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;">
                        <div>
                            <b>{a.get('supplier','—')}</b><br>
                            <small>{a.get('date','')} · {a['qty']:.2f} {m['unit']}</small>
                        </div>
                        <div style="text-align:right;">
                            <b>€ {a['total']:.2f}</b><br>
                            <small>€ {a['unitCost']:.4f}/{m['unit']} {tag}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("🗑", key=f"dla_{m['id']}_{i}"):
                    m["acquisti"].remove(a)
                    with st.spinner("Salvataggio..."):
                        save_materiali()
                    st.rerun()


# ============================================================
# MAIN
# ============================================================
def main():
    load_state()

    if st.session_state.get("detail_variety_id"):
        page_detail()
        st.divider()
        nav()
        return

    page = st.session_state.get("page", "varieta")

    with st.sidebar:
        st.markdown("### 🌱 Vivaio")
        if st.button("📊 Dashboard", use_container_width=True, type="primary" if page == "dashboard" else "secondary"):
            st.session_state.page = "dashboard"; _clear_subviews(); st.rerun()
        if st.button("🌱 Varietà", use_container_width=True, type="primary" if page == "varieta" else "secondary"):
            st.session_state.page = "varieta"; _clear_subviews(); st.rerun()
        if st.button("🪴 Contenitori", use_container_width=True, type="primary" if page == "contenitori" else "secondary"):
            st.session_state.page = "contenitori"; _clear_subviews(); st.rerun()
        if st.button("📦 Materiali", use_container_width=True, type="primary" if page == "materiali" else "secondary"):
            st.session_state.page = "materiali"; _clear_subviews(); st.rerun()

        st.divider()
        if st.button("🔄 Ricarica dati", use_container_width=True):
            for k in ["loaded", "varieta", "contenitori", "materiali", "pricingRule"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        st.caption(f"**{len(st.session_state.varieta)}** varietà · **{len(st.session_state.contenitori)}** contenitori · **{len(st.session_state.materiali)}** materiali")

    if page == "dashboard":
        page_dashboard()
    elif page == "contenitori":
        page_contenitori()
    elif page == "materiali":
        page_materiali()
    else:
        page_varieta()

    st.divider()
    nav()


def _clear_subviews():
    for k in ["show_variety_form", "show_container_form", "show_material_form",
              "detail_variety_id", "detail_material_id",
              "editing_variety", "editing_container", "editing_material",
              "confirm_delete", "confirm_delete_container", "confirm_del_mat"]:
        if k in st.session_state:
            st.session_state[k] = None if "editing" in k or "detail" in k or "confirm" in k else False


def nav():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📊", key="nav_d", use_container_width=True, help="Dashboard"):
            st.session_state.page = "dashboard"; _clear_subviews(); st.rerun()
    with c2:
        if st.button("🌱", key="nav_v", use_container_width=True, help="Varietà"):
            st.session_state.page = "varieta"; _clear_subviews(); st.rerun()
    with c3:
        if st.button("🪴", key="nav_c", use_container_width=True, help="Contenitori"):
            st.session_state.page = "contenitori"; _clear_subviews(); st.rerun()
    with c4:
        if st.button("📦", key="nav_m", use_container_width=True, help="Materiali"):
            st.session_state.page = "materiali"; _clear_subviews(); st.rerun()


if __name__ == "__main__":
    main()
