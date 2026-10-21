import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime
from io import BytesIO

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

# ==================== DATA PATHS ====================
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
    path = FILES[key]
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(key, df):
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
    st.caption("v2.1 • Import Excel + Spasial")
    st.caption("Data tersimpan lokal / cloud")

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
    st.subheader("📊 Dashboard Monitoring")
    
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
    
    st.markdown(f"#### 📅 {periode_label} {filter_tahun}" + (f" · {filter_kec}" if filter_kec != "Semua" else " · Semua Kecamatan"))
    
    df_pus = load_data("pus")
    df_kb_t = load_data("kb_total")
    df_kb_b = load_data("kb_baru")
    df_pra = load_data("pra_ks")
    df_bukan = load_data("pus_bukan_kb")
    
    pus_f = filter_df(df_pus, filter_tahun, filter_periode, filter_kec)
    kbt_f = filter_df(df_kb_t, filter_tahun, filter_periode, filter_kec)
    kbb_f = filter_df(df_kb_b, filter_tahun, filter_periode, filter_kec)
    pra_f = filter_df(df_pra, filter_tahun, filter_periode, filter_kec)
    bukan_f = filter_df(df_bukan, filter_tahun, filter_periode, filter_kec)
    
    total_pus = int(pus_f["jumlah_pus"].sum()) if not pus_f.empty else 0
    total_kb = int(kbt_f["jumlah"].sum()) if not kbt_f.empty else 0
    total_baru = int(kbb_f["jumlah"].sum()) if not kbb_f.empty else 0
    total_pra = int(pra_f["jumlah_pra_ks"].sum()) if not pra_f.empty else 0
    total_bukan = int(bukan_f["jumlah"].sum()) if not bukan_f.empty else 0
    coverage = (total_kb / total_pus * 100) if total_pus > 0 else 0
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total PUS", f"{total_pus:,}")
    m2.metric("KB Aktif", f"{total_kb:,}", delta=f"{coverage:.1f}% coverage" if total_pus else None)
    m3.metric("KB Baru", f"{total_baru:,}")
    m4.metric("Pra KS", f"{total_pra:,}")
    m5.metric("PUS Bukan KB", f"{total_bukan:,}")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🔬 Distribusi Metode KB (Aktif)")
        if not kbt_f.empty:
            msum = kbt_f.groupby("metode")["jumlah"].sum().reset_index()
            msum = msum[msum["jumlah"] > 0]
            if not msum.empty:
                fig = px.pie(msum, values="jumlah", names="metode", hole=0.45,
                             color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=380, margin=dict(t=20, b=20), showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada data")
        else:
            st.info("Belum ada data Peserta KB Total")
    
    with c2:
        st.markdown("##### 🆕 Metode KB Baru")
        if not kbb_f.empty:
            mbaru = kbb_f.groupby("metode")["jumlah"].sum().reset_index()
            mbaru = mbaru[mbaru["jumlah"] > 0]
            if not mbaru.empty:
                fig = px.bar(mbaru, x="metode", y="jumlah", color="metode",
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(height=380, showlegend=False, margin=dict(t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada data")
        else:
            st.info("Belum ada data Peserta KB Baru")
    
    st.markdown("##### 🚫 Detail PUS Bukan Peserta KB")
    if not bukan_f.empty:
        b1, b2 = st.columns(2)
        with b1:
            st_sum = bukan_f.groupby("status_hamil")["jumlah"].sum().reset_index()
            fig = px.pie(st_sum, values="jumlah", names="status_hamil", hole=0.35,
                         color_discrete_map={"Hamil": "#ef4444", "Tidak Hamil": "#3b82f6"})
            fig.update_layout(height=320, title="Status Kehamilan")
            st.plotly_chart(fig, use_container_width=True)
        with b2:
            det = bukan_f.groupby(["status_hamil", "keinginan"])["jumlah"].sum().reset_index()
            fig = px.bar(det, x="keinginan", y="jumlah", color="status_hamil", barmode="group",
                         color_discrete_map={"Hamil": "#ef4444", "Tidak Hamil": "#3b82f6"})
            fig.update_layout(height=320, title="Keinginan menurut Status", xaxis_tickangle=-25)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data PUS Bukan KB")
    
    if filter_kec == "Semua" and not pus_f.empty:
        st.markdown("##### 📍 Perbandingan antar Kecamatan")
        kec_p = pus_f.groupby("kecamatan")["jumlah_pus"].sum().reset_index()
        kec_k = kbt_f.groupby("kecamatan")["jumlah"].sum().reset_index() if not kbt_f.empty else pd.DataFrame(columns=["kecamatan", "jumlah"])
        kec_k = kec_k.rename(columns={"jumlah": "kb_aktif"})
        comp = kec_p.merge(kec_k, on="kecamatan", how="left").fillna(0)
        comp["coverage"] = (comp["kb_aktif"] / comp["jumlah_pus"] * 100).round(1)
        comp = comp.sort_values("jumlah_pus", ascending=False)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=comp["kecamatan"], y=comp["jumlah_pus"], name="PUS",
                             marker_color="#10b981"), secondary_y=False)
        fig.add_trace(go.Scatter(x=comp["kecamatan"], y=comp["coverage"], name="Coverage %",
                                 mode="lines+markers", marker_color="#ef4444", line=dict(width=3)), secondary_y=True)
        fig.update_layout(height=400, title="PUS vs Coverage KB")
        fig.update_yaxes(title_text="Jumlah PUS", secondary_y=False)
        fig.update_yaxes(title_text="Coverage (%)", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(comp.rename(columns={
            "kecamatan": "Kecamatan", "jumlah_pus": "Total PUS",
            "kb_aktif": "KB Aktif", "coverage": "Coverage (%)"
        }), use_container_width=True, hide_index=True)

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
                        
                        # Find matching key
                        key = None
                        req_cols = None
                        sheet_upper = sheet.upper().replace(" ", "_")
                        for sk, (k, cols) in sheet_map.items():
                            if sk.upper() == sheet_upper or sk.upper() in sheet_upper:
                                key = k
                                req_cols = cols
                                break
                        
                        if key is None:
                            # Heuristic
                            cols_lower = [c.lower() for c in df_sheet.columns]
                            if "jumlah_pus" in cols_lower:
                                key, req_cols = "pus", ["tahun", "bulan", "kecamatan", "desa", "jumlah_pus"]
                            elif "jumlah_pra_ks" in cols_lower:
                                key, req_cols = "pra_ks", ["tahun", "bulan", "kecamatan", "desa", "jumlah_pra_ks"]
                            elif "status_hamil" in cols_lower:
                                key, req_cols = "pus_bukan_kb", ["tahun", "bulan", "kecamatan", "desa", "status_hamil", "keinginan", "jumlah"]
                            elif "metode" in cols_lower:
                                # Could be total or baru - default total
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
