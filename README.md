# Sistem Monitoring KB & PUS v2.0

Aplikasi monitoring Keluarga Berencana (KB) dan Pasangan Usia Subur (PUS) dengan dashboard analitik dan visualisasi spasial.

## Fitur

- Input data PUS, Peserta KB (Total & Baru), Pra KS, PUS Bukan KB
- Dashboard multi-periode (Bulanan / Triwulanan / Semesteran / Tahunan)
- **Peta Spasial** interaktif per Kecamatan
- Manajemen wilayah (Kecamatan & Desa)
- Export data ke CSV

## Cara Menjalankan Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Community Cloud (Gratis)

1. Buat akun di [share.streamlit.io](https://share.streamlit.io)
2. Push folder ini ke GitHub repository
3. Di Streamlit Cloud → New app → pilih repository & file `app.py`
4. Klik Deploy

Aplikasi akan dapat diakses dari mana saja melalui link publik.
