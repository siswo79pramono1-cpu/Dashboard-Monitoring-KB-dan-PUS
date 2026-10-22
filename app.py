import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime
from io import BytesIO

# Google Sheets (opsional — aktif jika secrets tersedia)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Monitoring KB & PUS",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 1.8rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 40px rgba(15, 32, 39, 0.3);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.9rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .main-header p {
        margin: 0.4rem 0 0 0;
        opacity: 0.85;
        font-size: 0.95rem;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.7rem !important;
        font-weight: 700 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #f1f5f9;
        padding: 6px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 10px 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #0f2027 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2027 0%, #1a3a4a 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #e2e8f0 !important;
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA PATHS & STORAGE ====================
DATA_DIR = "data_kb"
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    "pus": os.path.join(DATA_DIR, "pus_bulanan.csv"),
    "kb_total": os.path.join(DATA_DIR, "peserta_kb_total.csv"),
    "kb_baru": os.path.join(DATA_DIR, "peserta_kb_baru.csv"),
    "pra_ks": os.path.join(DATA_DIR, "keluarga_pra_ks.csv"),
    "pus_bukan_kb": os.path.join(DATA_DIR, "pus_bukan_kb.csv"),
    "master": os.path.join(DATA_DIR, "master_wilayah.csv"),
}

# Nama worksheet di Google Sheets (harus sama)
SHEET_NAMES = {
    "pus": "PUS",
    "kb_total": "KB_TOTAL",
    "kb_baru": "KB_BARU",
    "pra_ks": "PRA_KS",
    "pus_bukan_kb": "PUS_BUKAN_KB",
    "master": "MASTER",
}

def _use_sheets():
    """Cek apakah Google Sheets dikonfigurasi di secrets."""
    try:
        return HAS_GSPREAD and "gcp_service_account" in st.secrets and "sheets" in st.secrets
    except Exception:
        return False

@st.cache_resource(ttl=300)
def _get_gspread_client():
    creds_info = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(credentials)

def _get_spreadsheet():
    client = _get_gspread_client()
    sid = st.secrets["sheets"]["spreadsheet_id"]
    return client.open_by_key(sid)

def _get_or_create_worksheet(spreadsheet, title):
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=1000, cols=20)

METODE_KB = ["IUD", "MOP", "MOW", "IMP", "Suntik", "PIL", "Kondom", "MAL", "Tradisional"]

BULAN_NAMA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

KOORDINAT_KECAMATAN = {
    "Batang": {"lat": -6.908, "lon": 109.730},
    "Warungasem": {"lat": -6.945, "lon": 109.695},
    "Bandar": {"lat": -7.035, "lon": 109.785},
    "Blado": {"lat": -7.080, "lon": 109.840},
    "Reban": {"lat": -7.100, "lon": 109.890},
    "Bawang": {"lat": -7.050, "lon": 109.920},
    "Tersono": {"lat": -7.020, "lon": 109.960},
    "Gringsing": {"lat": -6.980, "lon": 110.020},
    "Limpung": {"lat": -6.990, "lon": 109.920},
    "Subah": {"lat": -6.960, "lon": 109.870},
    "Tulis": {"lat": -6.940, "lon": 109.820},
    "Kandeman": {"lat": -6.920, "lon": 109.780},
    "Pecalungan": {"lat": -7.010, "lon": 109.830},
    "Wonotunggal": {"lat": -6.970, "lon": 109.760},
    "Banyuputih": {"lat": -6.950, "lon": 110.050},
}

# ==================== HELPER FUNCTIONS ====================
def init_master_wilayah():
    if not os.path.exists(FILES["master"]):
        data = {"kecamatan": list(KOORDINAT_KECAMATAN.keys()), "desa": [""] * len(KOORDINAT_KECAMATAN)}
        pd.DataFrame(data).to_csv(FILES["master"], index=False)
    return pd.read_csv(FILES["master"])

def load_data(key):
    """Load data dari Google Sheets (jika dikonfigurasi) atau CSV lokal."""
    if _use_sheets():
        try:
            ss = _get_spreadsheet()
            ws = _get_or_create_worksheet(ss, SHEET_NAMES[key])
            records = ws.get_all_records()
            if not records:
                return pd.DataFrame()
            df = pd.DataFrame(records)
            # Normalisasi tipe numerik
            for col in df.columns:
                if col in ("tahun", "bulan", "jumlah", "jumlah_pus", "jumlah_pra_ks"):
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            if "desa" in df.columns:
                df["desa"] = df["desa"].fillna("").astype(str)
                df.loc[df["desa"].isin(["nan", "None"]), "desa"] = ""
            return df
        except Exception as e:
            st.warning(f"Gagal baca Google Sheets ({key}): {e}. Menggunakan data lokal.")
    
    # Fallback lokal
    path = FILES[key]
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(key, df):
    """Simpan data ke Google Sheets (jika dikonfigurasi) dan/atau CSV lokal."""
    df = df.copy()
    # Pastikan desa string
    if "desa" in df.columns:
        df["desa"] = df["desa"].fillna("").astype(str)
    
    if _use_sheets():
        try:
            ss = _get_spreadsheet()
            ws = _get_or_create_worksheet(ss, SHEET_NAMES[key])
            ws.clear()
            if df.empty:
                return
            # Header + values
            values = [df.columns.tolist()] + df.astype(str).fillna("").values.tolist()
            ws.update(values, value_input_option="USER_ENTERED")
            return
        except Exception as e:
            st.error(f"Gagal simpan ke Google Sheets ({key}): {e}")
            # tetap coba simpan lokal sebagai backup
    
    df.to_csv(FILES[key], index=False)

def get_kecamatan_list():
    master = init_master_wilayah()
    return sorted(master["kecamatan"].unique().tolist())

def get_desa_list(kecamatan=None):
    master = init_master_wilayah()
    if kecamatan:
        desa = master[master["kecamatan"] == kecamatan]["desa"].dropna().unique().tolist()
        return sorted([d for d in desa if d and str(d).strip()])
    return []

def add_desa(kecamatan, desa):
    master = init_master_wilayah()
    exists = ((master["kecamatan"] == kecamatan) & (master["desa"] == desa)).any()
    if not exists:
        new_row = pd.DataFrame([{"kecamatan": kecamatan, "desa": desa}])
        master = pd.concat([master, new_row], ignore_index=True)
        master.to_csv(FILES["master"], index=False)

def filter_df(df, tahun, bulan_list, kecamatan):
    if df.empty:
        return df
    mask = (df["tahun"] == tahun) & (df["bulan"].isin(bulan_list))
    if kecamatan != "Semua":
        mask = mask & (df["kecamatan"] == kecamatan)
    return df[mask]

def get_stock_df(df, tahun, bulan_list, kecamatan):
    """Untuk data stok/akumulasi: ambil bulan terakhir yang tersedia dalam periode."""
    filtered = filter_df(df, tahun, bulan_list, kecamatan)
    if filtered.empty or "bulan" not in filtered.columns:
        return filtered
    latest = int(filtered["bulan"].max())
    return filtered[filtered["bulan"] == latest]

def import_sheet_data(df_import, key, required_cols):
    """Import data from dataframe, overwrite matching keys"""
    if df_import.empty:
        return 0, "Data kosong"
    
    # Normalize column names
    df_import.columns = [str(c).strip().lower() for c in df_import.columns]
    
    missing = [c for c in required_cols if c not in df_import.columns]
    if missing:
        return 0, f"Kolom wajib tidak ditemukan: {', '.join(missing)}"
    
    df_import = df_import[required_cols].copy()
    
    # Clean
    if "desa" in df_import.columns:
        df_import["desa"] = df_import["desa"].fillna("").astype(str).str.strip()
        df_import.loc[df_import["desa"].isin(["nan", "None", ""]), "desa"] = ""
    
    for col in ["tahun", "bulan"]:
        if col in df_import.columns:
            df_import[col] = pd.to_numeric(df_import[col], errors="coerce")
    
    if "jumlah" in df_import.columns:
        df_import["jumlah"] = pd.to_numeric(df_import["jumlah"], errors="coerce").fillna(0).astype(int)
    if "jumlah_pus" in df_import.columns:
        df_import["jumlah_pus"] = pd.to_numeric(df_import["jumlah_pus"], errors="coerce").fillna(0).astype(int)
    if "jumlah_pra_ks" in df_import.columns:
        df_import["jumlah_pra_ks"] = pd.to_numeric(df_import["jumlah_pra_ks"], errors="coerce").fillna(0).astype(int)
    
    df_import = df_import.dropna(subset=["tahun", "bulan", "kecamatan"])
    df_import["tahun"] = df_import["tahun"].astype(int)
    df_import["bulan"] = df_import["bulan"].astype(int)
    df_import["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    existing = load_data(key)
    
    if existing.empty:
        save_data(key, df_import)
        return len(df_import), "Berhasil"
    
    # Remove overlapping records
    if key in ["pus", "pra_ks"]:
        merge_keys = ["tahun", "bulan", "kecamatan", "desa"]
    elif key in ["kb_total", "kb_baru"]:
        merge_keys = ["tahun", "bulan", "kecamatan", "desa", "metode"]
    else:  # pus_bukan_kb
        merge_keys = ["tahun", "bulan", "kecamatan", "desa", "status_hamil", "keinginan"]
    
    # Ensure desa exists
    for d in [existing, df_import]:
        if "desa" not in d.columns:
            d["desa"] = ""
        d["desa"] = d["desa"].fillna("").astype(str)
    
    # Build mask to remove old matching rows
    existing["_key"] = existing.apply(lambda r: tuple(str(r[k]) for k in merge_keys if k in existing.columns), axis=1)
    df_import["_key"] = df_import.apply(lambda r: tuple(str(r[k]) for k in merge_keys if k in df_import.columns), axis=1)
    
    keys_to_replace = set(df_import["_key"].tolist())
    existing = existing[~existing["_key"].isin(keys_to_replace)].drop(columns=["_key"], errors="ignore")
    df_import = df_import.drop(columns=["_key"], errors="ignore")
    
    combined = pd.concat([existing, df_import], ignore_index=True)
    save_data(key, combined)
    return len(df_import), "Berhasil"

# ==================== HEADER ====================
st.markdown("""
<div class="main-header">
    <h1>👨‍👩‍👧‍👦 Sistem Monitoring Keluarga Berencana & PUS</h1>
    <p>Input Data • Dashboard Analitik • Visualisasi Spasial • Import Excel • Multi-Periode</p>
</div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### 🧭 Navigasi")
    menu = st.radio(
        "Menu",
        ["📥 Input Data", "📊 Dashboard", "🗺️ Peta Spasial", "📍 Manajemen Wilayah", "📁 Data & Export"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    if _use_sheets():
        st.success("☁️ Google Sheets terhubung")
        st.caption("Data tersimpan permanen")
    else:
        st.warning("💾 Mode lokal (data bisa hilang saat update)")
        st.caption("Hubungkan Google Sheets agar data aman")
    st.caption("v2.4 • Sheets + Import Excel + Spasial")

# ==================== MENU: INPUT DATA ====================
if menu == "📥 Input Data":
    st.subheader("📥 Form Input Data Bulanan")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        tahun = st.number_input("Tahun", min_value=2020, max_value=2030, value=datetime.now().year)
    with c2:
        bulan = st.selectbox("Bulan", options=list(BULAN_NAMA.keys()), format_func=lambda x: BULAN_NAMA[x])
    with c3:
        kecamatan = st.selectbox("Kecamatan", options=get_kecamatan_list())
    
    desa_list = get_desa_list(kecamatan)
    c_d1, c_d2 = st.columns([3, 1])
    with c_d1:
        if desa_list:
            desa = st.selectbox("Desa/Kelurahan (opsional)", options=["(Semua/Kecamatan)"] + desa_list)
            if desa == "(Semua/Kecamatan)":
                desa = ""
        else:
            desa = st.text_input("Desa/Kelurahan (opsional)", placeholder="Kosongkan jika tingkat kecamatan")
    with c_d2:
        st.write("")
        st.write("")
        if st.button("➕ Desa Baru"):
            st.session_state["show_add_desa"] = True
    
    if st.session_state.get("show_add_desa", False):
        with st.expander("Tambah Desa Baru", expanded=True):
            new_desa = st.text_input("Nama Desa/Kelurahan")
            if st.button("Simpan Desa"):
                if new_desa.strip():
                    add_desa(kecamatan, new_desa.strip())
                    st.success(f"Desa '{new_desa}' ditambahkan")
                    st.session_state["show_add_desa"] = False
                    st.rerun()
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1️⃣ PUS", "2️⃣ KB Total", "3️⃣ KB Baru", "4️⃣ Pra KS", "5️⃣ PUS Bukan KB"
    ])
    
    with tab1:
        st.markdown(f"**Jumlah PUS** — {BULAN_NAMA[bulan]} {tahun} | {kecamatan}" + (f" / {desa}" if desa else ""))
        jumlah_pus = st.number_input("Jumlah PUS", min_value=0, value=0, step=1, key="inp_pus")
        if st.button("💾 Simpan PUS", type="primary", key="sv_pus"):
            df = load_data("pus")
            mask = (df.get("tahun", pd.Series()) == tahun) & (df.get("bulan", pd.Series()) == bulan) & \
                   (df.get("kecamatan", pd.Series()) == kecamatan) & (df.get("desa", pd.Series()).fillna("") == desa)
            if not df.empty and mask.any():
                df = df[~mask]
            new_row = pd.DataFrame([{
                "tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                "jumlah_pus": jumlah_pus, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            save_data("pus", pd.concat([df, new_row], ignore_index=True))
            st.success(f"✅ Tersimpan: {jumlah_pus} PUS")
    
    with tab2:
        st.markdown(f"**Peserta KB Total (Akumulasi)** — {BULAN_NAMA[bulan]} {tahun}")
        cols = st.columns(3)
        vals = {}
        for i, m in enumerate(METODE_KB):
            with cols[i % 3]:
                vals[m] = st.number_input(m, min_value=0, value=0, step=1, key=f"t_{m}")
        total = sum(vals.values())
        st.info(f"**Total Aktif: {total:,}**")
        if st.button("💾 Simpan KB Total", type="primary", key="sv_tot"):
            df = load_data("kb_total")
            mask = (df.get("tahun", pd.Series()) == tahun) & (df.get("bulan", pd.Series()) == bulan) & \
                   (df.get("kecamatan", pd.Series()) == kecamatan) & (df.get("desa", pd.Series()).fillna("") == desa)
            if not df.empty and mask.any():
                df = df[~mask]
            rows = [{"tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                     "metode": m, "jumlah": j, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    for m, j in vals.items()]
            save_data("kb_total", pd.concat([df, pd.DataFrame(rows)], ignore_index=True))
            st.success(f"✅ Tersimpan (Total: {total:,})")
    
    with tab3:
        st.markdown(f"**Peserta KB Baru** — {BULAN_NAMA[bulan]} {tahun}")
        cols = st.columns(3)
        vals = {}
        for i, m in enumerate(METODE_KB):
            with cols[i % 3]:
                vals[m] = st.number_input(m, min_value=0, value=0, step=1, key=f"b_{m}")
        total = sum(vals.values())
        st.info(f"**Total Baru: {total:,}**")
        if st.button("💾 Simpan KB Baru", type="primary", key="sv_baru"):
            df = load_data("kb_baru")
            mask = (df.get("tahun", pd.Series()) == tahun) & (df.get("bulan", pd.Series()) == bulan) & \
                   (df.get("kecamatan", pd.Series()) == kecamatan) & (df.get("desa", pd.Series()).fillna("") == desa)
            if not df.empty and mask.any():
                df = df[~mask]
            rows = [{"tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                     "metode": m, "jumlah": j, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    for m, j in vals.items()]
            save_data("kb_baru", pd.concat([df, pd.DataFrame(rows)], ignore_index=True))
            st.success(f"✅ Tersimpan (Total: {total:,})")
    
    with tab4:
        st.markdown(f"**Keluarga Pra KS** — {BULAN_NAMA[bulan]} {tahun}")
        jml = st.number_input("Jumlah Keluarga Pra KS", min_value=0, value=0, step=1, key="inp_pra")
        if st.button("💾 Simpan Pra KS", type="primary", key="sv_pra"):
            df = load_data("pra_ks")
            mask = (df.get("tahun", pd.Series()) == tahun) & (df.get("bulan", pd.Series()) == bulan) & \
                   (df.get("kecamatan", pd.Series()) == kecamatan) & (df.get("desa", pd.Series()).fillna("") == desa)
            if not df.empty and mask.any():
                df = df[~mask]
            new_row = pd.DataFrame([{
                "tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                "jumlah_pra_ks": jml, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            save_data("pra_ks", pd.concat([df, new_row], ignore_index=True))
            st.success(f"✅ Tersimpan: {jml}")
    
    with tab5:
        st.markdown(f"**PUS Bukan Peserta KB** — {BULAN_NAMA[bulan]} {tahun}")
        st.markdown("##### Status Hamil")
        h1, h2, h3 = st.columns(3)
        with h1: hs = st.number_input("Ingin Anak Segera", min_value=0, value=0, key="hs")
        with h2: hn = st.number_input("Ingin Hamil Nanti", min_value=0, value=0, key="hn")
        with h3: ht = st.number_input("Tidak Ingin Anak Lagi", min_value=0, value=0, key="ht")
        
        st.markdown("##### Status Tidak Hamil")
        t1, t2, t3 = st.columns(3)
        with t1: ts = st.number_input("Ingin Anak Segera ", min_value=0, value=0, key="ts")
        with t2: tn = st.number_input("Ingin Anak Nanti", min_value=0, value=0, key="tn")
        with t3: tt = st.number_input("Tidak Ingin Anak Lagi ", min_value=0, value=0, key="tt")
        
        total_b = hs + hn + ht + ts + tn + tt
        st.info(f"**Total PUS Bukan KB: {total_b:,}**")
        
        if st.button("💾 Simpan PUS Bukan KB", type="primary", key="sv_bukan"):
            df = load_data("pus_bukan_kb")
            mask = (df.get("tahun", pd.Series()) == tahun) & (df.get("bulan", pd.Series()) == bulan) & \
                   (df.get("kecamatan", pd.Series()) == kecamatan) & (df.get("desa", pd.Series()).fillna("") == desa)
            if not df.empty and mask.any():
                df = df[~mask]
            rows = [
                {"tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                 "status_hamil": "Hamil", "keinginan": "INGIN ANAK SEGERA", "jumlah": hs},
                {"tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                 "status_hamil": "Hamil", "keinginan": "INGIN HAMIL NANTI/KEMUDIAN", "jumlah": hn},
                {"tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                 "status_hamil": "Hamil", "keinginan": "TIDAK INGIN ANAK LAGI", "jumlah": ht},
                {"tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                 "status_hamil": "Tidak Hamil", "keinginan": "INGIN ANAK SEGERA", "jumlah": ts},
                {"tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                 "status_hamil": "Tidak Hamil", "keinginan": "INGIN ANAK NANTI/KEMUDIAN", "jumlah": tn},
                {"tahun": tahun, "bulan": bulan, "kecamatan": kecamatan, "desa": desa,
                 "status_hamil": "Tidak Hamil", "keinginan": "TIDAK INGIN ANAK LAGI", "jumlah": tt},
            ]
            for r in rows:
                r["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data("pus_bukan_kb", pd.concat([df, pd.DataFrame(rows)], ignore_index=True))
            st.success(f"✅ Tersimpan (Total: {total_b:,})")

# ==================== MENU: DASHBOARD ====================
elif menu == "📊 Dashboard":
    st.markdown("### 📊 Dashboard Monitoring KB & PUS")
    
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        filter_tahun = st.selectbox("Tahun", list(range(2020, 2031)),
                                    index=list(range(2020, 2031)).index(datetime.now().year), key="dt")
    with f2:
        periode_type = st.selectbox("Periode", ["Bulanan", "Triwulanan", "Semesteran", "Tahunan"])
    with f3:
        if periode_type == "Bulanan":
            fb = st.selectbox("Bulan", list(BULAN_NAMA.keys()), format_func=lambda x: BULAN_NAMA[x], key="db")
            filter_periode = [fb]
            periode_label = BULAN_NAMA[fb]
        elif periode_type == "Triwulanan":
            tw = st.selectbox("Triwulan", [1, 2, 3, 4], format_func=lambda x: f"TW {x}")
            filter_periode = list(range((tw-1)*3+1, tw*3+1))
            periode_label = f"Triwulan {tw}"
        elif periode_type == "Semesteran":
            sm = st.selectbox("Semester", [1, 2])
            filter_periode = list(range(1, 7)) if sm == 1 else list(range(7, 13))
            periode_label = f"Semester {sm}"
        else:
            filter_periode = list(range(1, 13))
            periode_label = "Tahunan"
    with f4:
        filter_kec = st.selectbox("Kecamatan", ["Semua"] + get_kecamatan_list(), key="dk")
    
    st.markdown(f"**📅 {periode_label} {filter_tahun}**" + (f" · {filter_kec}" if filter_kec != "Semua" else " · Semua Kecamatan"))
    
    df_pus = load_data("pus")
    df_kb_t = load_data("kb_total")
    df_kb_b = load_data("kb_baru")
    df_pra = load_data("pra_ks")
    df_bukan = load_data("pus_bukan_kb")
    
    is_multi = len(filter_periode) > 1
    if is_multi:
        pus_f = get_stock_df(df_pus, filter_tahun, filter_periode, filter_kec)
        kbt_f = get_stock_df(df_kb_t, filter_tahun, filter_periode, filter_kec)
        pra_f = get_stock_df(df_pra, filter_tahun, filter_periode, filter_kec)
        bukan_f = get_stock_df(df_bukan, filter_tahun, filter_periode, filter_kec)
        kbb_f = filter_df(df_kb_b, filter_tahun, filter_periode, filter_kec)
        st.caption("📌 Mode multi-bulan: data stok = posisi bulan terakhir · KB Baru = jumlah sepanjang periode")
    else:
        pus_f = filter_df(df_pus, filter_tahun, filter_periode, filter_kec)
        kbt_f = filter_df(df_kb_t, filter_tahun, filter_periode, filter_kec)
        kbb_f = filter_df(df_kb_b, filter_tahun, filter_periode, filter_kec)
        pra_f = filter_df(df_pra, filter_tahun, filter_periode, filter_kec)
        bukan_f = filter_df(df_bukan, filter_tahun, filter_periode, filter_kec)
    
    total_pus = int(pus_f["jumlah_pus"].sum()) if not pus_f.empty and "jumlah_pus" in pus_f.columns else 0
    total_kb = int(kbt_f["jumlah"].sum()) if not kbt_f.empty and "jumlah" in kbt_f.columns else 0
    total_baru = int(kbb_f["jumlah"].sum()) if not kbb_f.empty and "jumlah" in kbb_f.columns else 0
    total_pra = int(pra_f["jumlah_pra_ks"].sum()) if not pra_f.empty and "jumlah_pra_ks" in pra_f.columns else 0
    total_bukan = int(bukan_f["jumlah"].sum()) if not bukan_f.empty and "jumlah" in bukan_f.columns else 0
    coverage = (total_kb / total_pus * 100) if total_pus > 0 else 0
    non_kb = max(total_pus - total_kb, 0)
    
    total_unmet = 0
    if not bukan_f.empty and "keinginan" in bukan_f.columns and "jumlah" in bukan_f.columns:
        unmet_mask = bukan_f["keinginan"].astype(str).str.contains("NANTI|TIDAK INGIN", case=False, na=False, regex=True)
        total_unmet = int(bukan_f.loc[unmet_mask, "jumlah"].sum())
    unmet_pct = (total_unmet / total_pus * 100) if total_pus > 0 else 0
    
    # ===== BARIS METRIK ATAS =====
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Total PUS", f"{total_pus:,}")
    with c2:
        st.metric("KB Aktif", f"{total_kb:,}", delta=f"{coverage:.1f}% coverage")
    with c3:
        st.metric("KB Baru", f"{total_baru:,}")
    with c4:
        st.metric("Pra KS", f"{total_pra:,}")
    with c5:
        st.metric("PUS Bukan KB", f"{total_bukan:,}")
    with c6:
        st.metric("Unmet Need", f"{total_unmet:,}", delta=f"{unmet_pct:.1f}% PUS")
    
    st.markdown("---")
    
    # ===== LAYOUT 3 KOLOM: Donut | Ranking | Detail =====
    left, mid, right = st.columns([1.1, 1.2, 1.1])
    
    # --- KIRI: Donut charts ---
    with left:
        st.markdown("##### 👥 PUS")
        if total_pus > 0:
            fig_pus = go.Figure(data=[go.Pie(
                labels=["Peserta KB", "Non-KB"],
                values=[total_kb, non_kb],
                hole=0.55,
                marker_colors=["#22c55e", "#94a3b8"],
                textinfo="percent+label",
                textposition="outside"
            )])
            fig_pus.update_layout(
                height=220, margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False, annotations=[dict(text=f"{total_pus:,}", x=0.5, y=0.5, font_size=16, showarrow=False)]
            )
            st.plotly_chart(fig_pus, use_container_width=True)
        else:
            st.info("Belum ada data PUS")
        
        st.markdown("##### 🔬 Peserta KB")
        if not kbt_f.empty and total_kb > 0:
            msum = kbt_f.groupby("metode")["jumlah"].sum().reset_index()
            msum = msum[msum["jumlah"] > 0].sort_values("jumlah", ascending=False)
            fig_kb = go.Figure(data=[go.Pie(
                labels=msum["metode"], values=msum["jumlah"], hole=0.55,
                textinfo="percent", textposition="inside",
                marker_colors=px.colors.qualitative.Set2
            )])
            fig_kb.update_layout(
                height=240, margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", y=-0.15, font_size=10),
                annotations=[dict(text=f"{total_kb:,}", x=0.5, y=0.5, font_size=14, showarrow=False)]
            )
            st.plotly_chart(fig_kb, use_container_width=True)
        else:
            st.info("Belum ada data KB")
        
        st.markdown("##### 🚫 Bukan Peserta KB")
        if not bukan_f.empty and total_bukan > 0:
            if "status_hamil" in bukan_f.columns:
                st_sum = bukan_f.groupby("status_hamil")["jumlah"].sum().reset_index()
                fig_b = go.Figure(data=[go.Pie(
                    labels=st_sum["status_hamil"], values=st_sum["jumlah"], hole=0.55,
                    marker_colors=["#ef4444", "#3b82f6"],
                    textinfo="percent+label", textposition="outside"
                )])
                fig_b.update_layout(
                    height=220, margin=dict(t=10, b=10, l=10, r=10),
                    showlegend=False,
                    annotations=[dict(text=f"{total_bukan:,}", x=0.5, y=0.5, font_size=14, showarrow=False)]
                )
                st.plotly_chart(fig_b, use_container_width=True)
            else:
                st.info("Data tidak lengkap")
        else:
            st.info("Belum ada data")
    
    # --- TENGAH: Ranking + Unmet ---
    with mid:
        st.markdown("##### 🏆 Peringkat Kecamatan (Coverage KB)")
        
        # Build ranking
        if not pus_f.empty:
            kec_p = pus_f.groupby("kecamatan", as_index=False)["jumlah_pus"].sum() if "jumlah_pus" in pus_f.columns else pd.DataFrame(columns=["kecamatan","jumlah_pus"])
            kec_k = kbt_f.groupby("kecamatan", as_index=False)["jumlah"].sum().rename(columns={"jumlah":"kb_aktif"}) if (not kbt_f.empty and "jumlah" in kbt_f.columns) else pd.DataFrame(columns=["kecamatan","kb_aktif"])
            rank = kec_p.merge(kec_k, on="kecamatan", how="left").fillna(0)
            rank["coverage"] = rank.apply(lambda r: round(r["kb_aktif"]/r["jumlah_pus"]*100, 1) if r["jumlah_pus"]>0 else 0, axis=1)
            rank = rank.sort_values("coverage", ascending=False).reset_index(drop=True)
            rank["rank"] = rank.index + 1
            
            # Color bars for ranking
            for i, row in rank.head(12).iterrows():
                cov = row["coverage"]
                color = "#22c55e" if cov >= 70 else ("#eab308" if cov >= 50 else "#ef4444")
                st.markdown(
                    f"""<div style="display:flex;align-items:center;margin-bottom:6px;background:#f8fafc;border-radius:8px;padding:6px 10px;border-left:4px solid {color}">
                    <span style="width:28px;font-weight:700;color:#64748b">#{int(row['rank'])}</span>
                    <span style="flex:1;font-weight:600;font-size:0.9rem">{row['kecamatan']}</span>
                    <span style="font-weight:700;color:{color}">{cov:.1f}%</span>
                    </div>""",
                    unsafe_allow_html=True
                )
            if len(rank) > 12:
                st.caption(f"... dan {len(rank)-12} kecamatan lainnya (lihat tabel bawah)")
        else:
            st.info("Belum ada data untuk ranking")
        
        st.markdown("##### 📉 Unmet Need")
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#fef2f2,#fff7ed);border-radius:12px;padding:16px;text-align:center;border:1px solid #fecaca">
            <div style="font-size:2rem;font-weight:800;color:#dc2626">{total_unmet:,}</div>
            <div style="color:#991b1b;font-size:0.9rem">Unmet Need ({unmet_pct:.1f}% dari PUS)</div>
            <div style="color:#78716c;font-size:0.75rem;margin-top:4px">Ingin anak nanti + Tidak ingin anak lagi</div>
            </div>""",
            unsafe_allow_html=True
        )
    
    # --- KANAN: Detail chart + KB Baru ---
    with right:
        st.markdown("##### 🆕 KB Baru per Metode")
        if not kbb_f.empty and total_baru > 0:
            mbaru = kbb_f.groupby("metode")["jumlah"].sum().reset_index()
            mbaru = mbaru[mbaru["jumlah"] > 0].sort_values("jumlah", ascending=True)
            fig_baru = px.bar(mbaru, x="jumlah", y="metode", orientation="h",
                              color="jumlah", color_continuous_scale="Tealgrn")
            fig_baru.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10),
                                   showlegend=False, coloraxis_showscale=False,
                                   xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_baru, use_container_width=True)
        else:
            st.info("Belum ada data KB Baru")
        
        st.markdown("##### 📋 Detail Bukan KB")
        if not bukan_f.empty and "keinginan" in bukan_f.columns:
            det = bukan_f.groupby(["status_hamil", "keinginan"])["jumlah"].sum().reset_index()
            det = det.sort_values("jumlah", ascending=False)
            fig_det = px.bar(det, x="keinginan", y="jumlah", color="status_hamil", barmode="group",
                             color_discrete_map={"Hamil": "#ef4444", "Tidak Hamil": "#3b82f6"})
            fig_det.update_layout(height=280, margin=dict(t=10, b=40, l=10, r=10),
                                  xaxis_tickangle=-30, legend=dict(orientation="h", y=-0.35),
                                  xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_det, use_container_width=True)
        else:
            st.info("Belum ada detail")
    
    st.markdown("---")
    
    # ===== TABEL PER KECAMATAN =====
    if not pus_f.empty:
        st.markdown("##### 📍 Tabel Lengkap per Kecamatan")
        kec_p = pus_f.groupby("kecamatan", as_index=False)["jumlah_pus"].sum() if "jumlah_pus" in pus_f.columns else pd.DataFrame(columns=["kecamatan", "jumlah_pus"])
        kec_k = kbt_f.groupby("kecamatan", as_index=False)["jumlah"].sum().rename(columns={"jumlah": "kb_aktif"}) if (not kbt_f.empty and "jumlah" in kbt_f.columns) else pd.DataFrame(columns=["kecamatan", "kb_aktif"])
        kec_baru = kbb_f.groupby("kecamatan", as_index=False)["jumlah"].sum().rename(columns={"jumlah": "kb_baru"}) if (not kbb_f.empty and "jumlah" in kbb_f.columns) else pd.DataFrame(columns=["kecamatan", "kb_baru"])
        kec_pra = pra_f.groupby("kecamatan", as_index=False)["jumlah_pra_ks"].sum() if (not pra_f.empty and "jumlah_pra_ks" in pra_f.columns) else pd.DataFrame(columns=["kecamatan", "jumlah_pra_ks"])
        kec_bukan = bukan_f.groupby("kecamatan", as_index=False)["jumlah"].sum().rename(columns={"jumlah": "pus_bukan_kb"}) if (not bukan_f.empty and "jumlah" in bukan_f.columns) else pd.DataFrame(columns=["kecamatan", "pus_bukan_kb"])
        
        if not bukan_f.empty and "keinginan" in bukan_f.columns:
            unmet_df = bukan_f[bukan_f["keinginan"].astype(str).str.contains("NANTI|TIDAK INGIN", case=False, na=False, regex=True)]
            kec_unmet = unmet_df.groupby("kecamatan", as_index=False)["jumlah"].sum().rename(columns={"jumlah": "unmet_need"}) if not unmet_df.empty else pd.DataFrame(columns=["kecamatan", "unmet_need"])
        else:
            kec_unmet = pd.DataFrame(columns=["kecamatan", "unmet_need"])
        
        comp = kec_p.merge(kec_k, on="kecamatan", how="outer")
        comp = comp.merge(kec_baru, on="kecamatan", how="outer")
        comp = comp.merge(kec_pra, on="kecamatan", how="outer")
        comp = comp.merge(kec_bukan, on="kecamatan", how="outer")
        comp = comp.merge(kec_unmet, on="kecamatan", how="outer").fillna(0)
        
        for col in ["jumlah_pus", "kb_aktif", "kb_baru", "jumlah_pra_ks", "pus_bukan_kb", "unmet_need"]:
            if col in comp.columns:
                comp[col] = comp[col].astype(int)
        
        comp["coverage"] = comp.apply(lambda r: round(r["kb_aktif"] / r["jumlah_pus"] * 100, 1) if r["jumlah_pus"] > 0 else 0, axis=1)
        comp["unmet_pct"] = comp.apply(lambda r: round(r["unmet_need"] / r["jumlah_pus"] * 100, 1) if r["jumlah_pus"] > 0 else 0, axis=1)
        comp = comp.sort_values("coverage", ascending=False)
        
        show_df = comp.rename(columns={
            "kecamatan": "Kecamatan", "jumlah_pus": "PUS", "kb_aktif": "KB Aktif",
            "coverage": "Coverage (%)", "kb_baru": "KB Baru", "jumlah_pra_ks": "Pra KS",
            "pus_bukan_kb": "PUS Bukan KB", "unmet_need": "Unmet Need", "unmet_pct": "Unmet Need (%)"
        })
        st.dataframe(show_df, use_container_width=True, hide_index=True)
        
        csv_kec = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Tabel per Kecamatan (CSV)", data=csv_kec,
                           file_name=f"perbandingan_kecamatan_{filter_tahun}.csv", mime="text/csv")
    else:
        st.info("Belum ada data PUS. Silakan input atau import data terlebih dahulu.")

# ==================== MENU: PETA SPASIAL ====================
elif menu == "🗺️ Peta Spasial":
    st.subheader("🗺️ Visualisasi Spasial Monitoring KB")
    
    sf1, sf2, sf3 = st.columns(3)
    with sf1:
        map_tahun = st.selectbox("Tahun", list(range(2020, 2031)),
                                 index=list(range(2020, 2031)).index(datetime.now().year), key="mt")
    with sf2:
        map_periode = st.selectbox("Periode", ["Bulanan", "Triwulanan", "Semesteran", "Tahunan"], key="mp")
    with sf3:
        if map_periode == "Bulanan":
            mb = st.selectbox("Bulan", list(BULAN_NAMA.keys()), format_func=lambda x: BULAN_NAMA[x], key="mb")
            map_bulan = [mb]
            map_label = BULAN_NAMA[mb]
        elif map_periode == "Triwulanan":
            tw = st.selectbox("Triwulan", [1,2,3,4], key="mtw")
            map_bulan = list(range((tw-1)*3+1, tw*3+1))
            map_label = f"TW {tw}"
        elif map_periode == "Semesteran":
            sm = st.selectbox("Semester", [1,2], key="msm")
            map_bulan = list(range(1,7)) if sm==1 else list(range(7,13))
            map_label = f"Semester {sm}"
        else:
            map_bulan = list(range(1,13))
            map_label = "Tahunan"
    
    st.markdown(f"**Periode peta:** {map_label} {map_tahun}")
    
    df_pus = load_data("pus")
    df_kb = load_data("kb_total")
    
    # Multi-bulan: ambil posisi bulan terakhir (stok)
    if len(map_bulan) > 1:
        pus_map = get_stock_df(df_pus, map_tahun, map_bulan, "Semua")
        kb_map = get_stock_df(df_kb, map_tahun, map_bulan, "Semua")
    else:
        pus_map = filter_df(df_pus, map_tahun, map_bulan, "Semua")
        kb_map = filter_df(df_kb, map_tahun, map_bulan, "Semua")
    
    rows = []
    for kec, coord in KOORDINAT_KECAMATAN.items():
        p = int(pus_map[pus_map["kecamatan"]==kec]["jumlah_pus"].sum()) if not pus_map.empty else 0
        k = int(kb_map[kb_map["kecamatan"]==kec]["jumlah"].sum()) if not kb_map.empty else 0
        cov = (k / p * 100) if p > 0 else 0
        rows.append({
            "kecamatan": kec,
            "lat": coord["lat"],
            "lon": coord["lon"],
            "jumlah_pus": p,
            "kb_aktif": k,
            "coverage": round(cov, 1)
        })
    
    map_df = pd.DataFrame(rows)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total PUS (Peta)", f"{map_df['jumlah_pus'].sum():,}")
    c2.metric("Total KB Aktif", f"{map_df['kb_aktif'].sum():,}")
    avg_cov = map_df[map_df['jumlah_pus']>0]['coverage'].mean() if (map_df['jumlah_pus']>0).any() else 0
    c3.metric("Rata-rata Coverage", f"{avg_cov:.1f}%")
    
    st.markdown("---")
    
    map_metric = st.radio("Tampilkan di peta berdasarkan:", 
                          ["Jumlah PUS", "Peserta KB Aktif", "Coverage (%)"], horizontal=True)
    
    if map_metric == "Jumlah PUS":
        size_col, color_col, title = "jumlah_pus", "jumlah_pus", "Jumlah PUS per Kecamatan"
        color_scale = "Greens"
    elif map_metric == "Peserta KB Aktif":
        size_col, color_col, title = "kb_aktif", "kb_aktif", "Peserta KB Aktif per Kecamatan"
        color_scale = "Blues"
    else:
        size_col, color_col, title = "coverage", "coverage", "Coverage KB (%) per Kecamatan"
        color_scale = "RdYlGn"
    
    fig = px.scatter_map(
        map_df,
        lat="lat",
        lon="lon",
        size=size_col,
        color=color_col,
        hover_name="kecamatan",
        hover_data={
            "jumlah_pus": True,
            "kb_aktif": True,
            "coverage": True,
            "lat": False,
            "lon": False
        },
        color_continuous_scale=color_scale,
        size_max=45,
        zoom=9.5,
        title=title,
        map_style="open-street-map",
        height=520,
        center={"lat": -7.0, "lon": 109.85}
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title=map_metric)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📋 Data Tabel per Kecamatan", expanded=False):
        st.dataframe(
            map_df[["kecamatan", "jumlah_pus", "kb_aktif", "coverage"]]
            .rename(columns={
                "kecamatan": "Kecamatan",
                "jumlah_pus": "PUS",
                "kb_aktif": "KB Aktif",
                "coverage": "Coverage (%)"
            })
            .sort_values("PUS", ascending=False),
            use_container_width=True,
            hide_index=True
        )
    
    st.caption("💡 Ukuran lingkaran & warna mewakili nilai metrik yang dipilih. Hover untuk detail.")

# ==================== MENU: MANAJEMEN WILAYAH ====================
elif menu == "📍 Manajemen Wilayah":
    st.subheader("📍 Manajemen Wilayah")
    
    master = init_master_wilayah()
    kec_list = sorted(master["kecamatan"].unique().tolist())
    
    st.markdown("##### Daftar Kecamatan")
    st.write(" · ".join(kec_list))
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("##### ➕ Tambah Kecamatan")
        new_kec = st.text_input("Nama Kecamatan Baru")
        if st.button("Tambah Kecamatan"):
            if new_kec.strip() and new_kec.strip() not in kec_list:
                new_row = pd.DataFrame([{"kecamatan": new_kec.strip(), "desa": ""}])
                master = pd.concat([master, new_row], ignore_index=True)
                master.to_csv(FILES["master"], index=False)
                st.success(f"'{new_kec}' ditambahkan")
                st.rerun()
            elif new_kec.strip() in kec_list:
                st.warning("Kecamatan sudah ada")
    
    with c2:
        st.markdown("##### ➕ Tambah Desa")
        sel_kec = st.selectbox("Pilih Kecamatan", kec_list)
        new_desa = st.text_input("Nama Desa/Kelurahan")
        if st.button("Tambah Desa"):
            if new_desa.strip():
                add_desa(sel_kec, new_desa.strip())
                st.success(f"'{new_desa}' ditambahkan ke {sel_kec}")
                st.rerun()
    
    st.markdown("---")
    st.markdown("##### Daftar Desa per Kecamatan")
    for kec in kec_list:
        desa_k = master[(master["kecamatan"]==kec) & (master["desa"].notna()) & (master["desa"]!="")]["desa"].tolist()
        if desa_k:
            with st.expander(f"**{kec}** ({len(desa_k)} desa)"):
                st.write(", ".join(sorted(desa_k)))
        else:
            st.caption(f"{kec} — belum ada desa")

# ==================== MENU: DATA & EXPORT ====================
elif menu == "📁 Data & Export":
    st.subheader("📁 Data Tersimpan, Export & Import Excel")
    
    tab_view, tab_import = st.tabs(["📋 Lihat & Export Data", "📥 Import dari Excel"])
    
    with tab_view:
        choice = st.selectbox("Pilih Jenis Data", [
            "Jumlah PUS", "Peserta KB Total", "Peserta KB Baru",
            "Keluarga Pra KS", "PUS Bukan Peserta KB"
        ])
        
        key_map = {
            "Jumlah PUS": "pus",
            "Peserta KB Total": "kb_total",
            "Peserta KB Baru": "kb_baru",
            "Keluarga Pra KS": "pra_ks",
            "PUS Bukan Peserta KB": "pus_bukan_kb"
        }
        
        df = load_data(key_map[choice])
        
        if df.empty:
            st.warning("Belum ada data tersimpan.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                years = sorted(df["tahun"].unique().tolist()) if "tahun" in df.columns else []
                f_tahun = st.multiselect("Filter Tahun", years, default=years[-1:] if years else [])
            with c2:
                kecs = sorted(df["kecamatan"].unique().tolist()) if "kecamatan" in df.columns else []
                f_kec = st.multiselect("Filter Kecamatan", kecs)
            
            filtered = df.copy()
            if f_tahun:
                filtered = filtered[filtered["tahun"].isin(f_tahun)]
            if f_kec:
                filtered = filtered[filtered["kecamatan"].isin(f_kec)]
            
            st.dataframe(filtered, use_container_width=True, hide_index=True)
            
            csv = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download CSV",
                data=csv,
                file_name=f"{key_map[choice]}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            with st.expander("⚠️ Hapus Data"):
                st.warning("Tindakan ini tidak dapat dibatalkan.")
                if st.button("Hapus SEMUA data jenis ini"):
                    save_data(key_map[choice], pd.DataFrame())
                    st.success("Data dihapus.")
                    st.rerun()
    
    with tab_import:
        st.markdown("### 📥 Import Data dari Excel")
        st.info("Gunakan template resmi agar format kolom sesuai. Data dengan tahun+bulan+kecamatan yang sama akan **ditimpa**.")
        
        # Download template
        template_path = "Template_Import_Data_KB.xlsx"
        if os.path.exists(template_path):
            with open(template_path, "rb") as f:
                st.download_button(
                    "📄 Download Template Excel",
                    data=f.read(),
                    file_name="Template_Import_Data_KB.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
        else:
            st.warning("Template belum tersedia di server. Download dari file yang sudah disediakan.")
        
        st.markdown("---")
        st.markdown("##### Upload File Excel")
        
        uploaded = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx", "xls"])
        
        if uploaded is not None:
            try:
                xls = pd.ExcelFile(uploaded)
                sheet_names = xls.sheet_names
                st.success(f"File terbaca. Sheet tersedia: {', '.join(sheet_names)}")
                
                # Mapping sheet name to key
                sheet_map = {
                    "PUS": ("pus", ["tahun", "bulan", "kecamatan", "desa", "jumlah_pus"]),
                    "KB_TOTAL": ("kb_total", ["tahun", "bulan", "kecamatan", "desa", "metode", "jumlah"]),
                    "KB_BARU": ("kb_baru", ["tahun", "bulan", "kecamatan", "desa", "metode", "jumlah"]),
                    "PRA_KS": ("pra_ks", ["tahun", "bulan", "kecamatan", "desa", "jumlah_pra_ks"]),
                    "PUS_BUKAN_KB": ("pus_bukan_kb", ["tahun", "bulan", "kecamatan", "desa", "status_hamil", "keinginan", "jumlah"]),
                }
                
                available = [s for s in sheet_names if s.upper() in [k.upper() for k in sheet_map.keys()] or s in sheet_map]
                
                if not available:
                    # Try flexible matching
                    available = [s for s in sheet_names if s != "PETUNJUK"]
                
                selected_sheets = st.multiselect(
                    "Pilih sheet yang ingin diimport",
                    options=sheet_names,
                    default=[s for s in sheet_names if s != "PETUNJUK"]
                )
                
                if selected_sheets and st.button("🚀 Proses Import", type="primary"):
                    results = []
                    for sheet in selected_sheets:
                        df_sheet = pd.read_excel(uploaded, sheet_name=sheet)
                        
                        # Find matching key — exact match first, then longest contains
                        key = None
                        req_cols = None
                        sheet_upper = sheet.upper().replace(" ", "_")
                        
                        # 1) Exact match
                        for sk, (k, cols) in sheet_map.items():
                            if sk.upper() == sheet_upper:
                                key, req_cols = k, cols
                                break
                        
                        # 2) Longest partial match
                        if key is None:
                            candidates = sorted(sheet_map.items(), key=lambda x: -len(x[0]))
                            for sk, (k, cols) in candidates:
                                if sk.upper() in sheet_upper or sheet_upper in sk.upper():
                                    key, req_cols = k, cols
                                    break
                        
                        # 3) Heuristic by columns
                        if key is None:
                            cols_lower = [str(c).lower() for c in df_sheet.columns]
                            if "status_hamil" in cols_lower or "keinginan" in cols_lower:
                                key, req_cols = "pus_bukan_kb", ["tahun", "bulan", "kecamatan", "desa", "status_hamil", "keinginan", "jumlah"]
                            elif "jumlah_pra_ks" in cols_lower:
                                key, req_cols = "pra_ks", ["tahun", "bulan", "kecamatan", "desa", "jumlah_pra_ks"]
                            elif "jumlah_pus" in cols_lower:
                                key, req_cols = "pus", ["tahun", "bulan", "kecamatan", "desa", "jumlah_pus"]
                            elif "metode" in cols_lower:
                                if "baru" in sheet_upper:
                                    key, req_cols = "kb_baru", ["tahun", "bulan", "kecamatan", "desa", "metode", "jumlah"]
                                else:
                                    key, req_cols = "kb_total", ["tahun", "bulan", "kecamatan", "desa", "metode", "jumlah"]
                            else:
                                results.append(f"❌ Sheet **{sheet}**: format tidak dikenali")
                                continue
                        
                        count, msg = import_sheet_data(df_sheet, key, req_cols)
                        if msg == "Berhasil":
                            results.append(f"✅ Sheet **{sheet}** → {key}: {count} baris berhasil diimport")
                        else:
                            results.append(f"❌ Sheet **{sheet}**: {msg}")
                    
                    for r in results:
                        st.write(r)
                    
                    st.balloons()
                    st.success("Proses import selesai. Silakan cek di menu Dashboard / Data.")
                    
            except Exception as e:
                st.error(f"Gagal membaca file: {e}")

# Footer
st.markdown("""
<div class="footer">
    Sistem Monitoring KB & PUS · v2.1 · Import Excel + Peta Spasial · Siap Deploy
</div>
""", unsafe_allow_html=True)
