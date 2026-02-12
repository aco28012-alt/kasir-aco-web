import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# --- PENGATURAN DASAR ---
PASSWORD_RAHASIA = "aco123" 
URL_KASIR = "https://script.google.com/macros/s/AKfycbwqWChTAom4eWXCW_vLIggjId4Xilp7XnmC458mARcQqZs5NREsCCR_jg25hIQom3Ou/exec"

# ID Sheet Aco
ID_SHEET = "1OmbEd5JtTdW82udZ28jpFWXjd4mexGO6_EB06_-8GPQ"

# Link CSV otomatis
URL_BACA_KASIR = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_BACA_PENGELUARAN = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=2102782816"

st.set_page_config(page_title="Kasir Pro Cafe Aco", layout="wide")

# --- DATA MENU (TERBARU) ---
menu = {
    'HOT COFFEE': {'AMERICANO': 10000, 'ESPRESSO': 8000},
    'COLD COFFEE': {'AMERICANO': 12000, 'LATTE': 15000, 'CAPPUCINO': 15000, 'MOCHA': 16000, 'COFFEE MILK (reguler)': 13000, 'COFFE MILK (small)': 10000},
    'TEA & NON-COFFEE': {'GREAN TEA': 13000, 'THAI TEA': 13000, 'HOT MILK': 10000,'BROWN SUGAR MILK': 14000, 'ICED CHOCOLATE': 13000, 'HOT CHOCOLATE': 12000, 'ICED MILK': 12000, 'EKSTRA JOSS SUSU': 7000},
    'SPECIALITY DRINKS': {'PANDAN LATTE': 15000, 'HAZELNUT LATTE': 15000, 'BUTTERSCOTCH LATTE': 15000, 'SPAINISH LATTE': 16000},
    'SIGNATURE': {'KOPI KULT': 15000, 'KOPI ARENITA': 15000, 'AMERICANO SPESIAL': 15000},
    'MANUAL BREW': {'V60': 20000, 'VIETNAM DRIP': 13000},
    'MOCKTAIL': {'MANGOSQUASH': 14000, 'BLUEOCEAN': 14000, 'REDBLISS': 14000}
}

semua_harga = {}
for kategori in menu: semua_harga.update(menu[kategori])

# --- SESSION STATE ---
if 'keranjang' not in st.session_state: st.session_state.keranjang = {}
def tambah_ke_keranjang(nama_item):
    st.session_state.keranjang[nama_item] = st.session_state.keranjang.get(nama_item, 0) + 1
def reset_keranjang(): st.session_state.keranjang = {}

# --- LOGIN ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    st.title("🔐 Akses Terkunci - Cafe Aco")
    input_pass = st.text_input("Masukkan Password", type="password")
    if st.button("Masuk"):
        if input_pass == PASSWORD_RAHASIA:
            st.session_state["authenticated"] = True
            st.rerun()
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🚀 Navigasi")
        pilihan = st.radio("Pilih Halaman:", ["🛒 Kasir Pro", "💸 Pengeluaran", "📋 Riwayat"])
        if st.button("🚪 Keluar"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- HALAMAN 1: KASIR ---
    if pilihan == "🛒 Kasir Pro":
        st.title("☕ Kasir Visual")
        col_m, col_p = st.columns([2, 1])
        with col_m:
            tabs = st.tabs(list(menu.keys()))
            for i, kategori in enumerate(menu.keys()):
                with tabs[i]:
                    cols = st.columns(2) 
                    for j, (item, harga) in enumerate(menu[kategori].items()):
                        with cols[j % 2]:
                            # INI PERUBAHANNYA: Membuat kunci unik agar tidak error
                            key_unik = f"btn_{kategori}_{item}".replace(" ", "_")
                            
                            if st.button(f"**{item}**\n\nRp {harga:,}", key=key_unik, use_container_width=True):
                                tambah_ke_keranjang(item)
                                st.toast(f"{item} masuk ke keranjang!")
        with col_p:
            st.subheader("🛒 Keranjang")
            if not st.session_state.keranjang: st.info("Pilih menu di samping")
            else:
                total_bayar = sum(semua_harga[item] * qty for item, qty in st.session_state.keranjang.items())
                for item, qty in st.session_state.keranjang.items():
                    st.write(f"**{item}** x{qty}")
                st.divider()
                st.write(f"### Total: Rp {total_bayar:,}")
                nama_plg = st.text_input("Nama Pelanggan", placeholder="Contoh: Aco")
                if st.button("KONFIRMASI", type="primary", use_container_width=True):
                    if nama_plg:
                        with st.spinner("Menyimpan..."):
                            for item, qty in st.session_state.keranjang.items():
                                payload = {
                                    "action": "save", 
                                    "type": "kasir", 
                                    "waktu": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                    "pelanggan": nama_plg.upper(), 
                                    "produk": item, 
                                    "qty": qty, 
                                    "harga": semua_harga[item], 
                                    "total": semua_harga[item]*qty
                                }
                                requests.post(URL_KASIR, data=json.dumps(payload))
                            st.cache_data.clear() # Agar data langsung terupdate di Riwayat
                            reset_keranjang()
                            st.rerun()
                    else: st.warning("Isi nama pelanggan!")
                if st.button("Reset Keranjang"): reset_keranjang(); st.rerun()

    # --- HALAMAN 2: PENGELUARAN ---
    elif pilihan == "💸 Pengeluaran":
        st.title("💸 Catat Pengeluaran")
        kat = st.selectbox("Kategori", ["Bahan Baku", "Operasional", "Gaji", "Lain-lain"])
        ket = st.text_input("Keterangan")
        nom = st.number_input("Nominal (Rp)", min_value=0, step=1000)
        if st.button("Simpan Pengeluaran", use_container_width=True):
            payload = {"action": "save", "type": "pengeluaran", "waktu": datetime.now().strftime("%Y-%m-%d %H:%M"), "kategori": kat, "keterangan": ket, "nominal": nom}
            requests.post(URL_KASIR, data=json.dumps(payload))
            st.cache_data.clear()
            st.success("Tercatat!")

    # --- HALAMAN 3: RIWAYAT & DASHBOARD ---
    elif pilihan == "📋 Riwayat":
        st.title("📋 Dashboard Keuangan")
        try:
            tanda_waktu = datetime.now().timestamp()
            df_k = pd.read_csv(f"{URL_BACA_KASIR}&t={tanda_waktu}")
            df_p = pd.read_csv(f"{URL_BACA_PENGELUARAN}&t={tanda_waktu}")
            
            df_k['waktu'] = pd.to_datetime(df_k['waktu'], errors='coerce')
            df_p['waktu'] = pd.to_datetime(df_p['waktu'], errors='coerce')
            
            mode = st.radio("Laporan:", ["Harian", "Bulanan"], horizontal=True)

            if mode == "Harian":
                tgl_pilih = st.date_input("Tanggal", datetime.now())
                df_k_f = df_k[df_k['waktu'].dt.date == tgl_pilih]
                df_p_f = df_p[df_p['waktu'].dt.date == tgl_pilih]
            else:
                bulan_list = df_k['waktu'].dt.to_period('M').unique().tolist()
                bln_pilih = st.selectbox("Bulan", bulan_list, format_func=lambda x: x.strftime('%B %Y'))
                df_k_f = df_k[df_k['waktu'].dt.to_period('M') == bln_pilih]
                df_p_f = df_p[df_p['waktu'].dt.to_period('M') == bln_pilih]

            # --- METRIK ---
            masuk = df_k_f['total'].sum() if not df_k_f.empty else 0
            keluar = df_p_f['nominal'].sum() if not df_p_f.empty else 0
            c1, c2, c3 = st.columns(3)
            c1.metric("Pemasukan", f"Rp {masuk:,}")
            c2.metric("Pengeluaran", f"Rp {keluar:,}")
            c3.metric("Saldo", f"Rp {masuk-keluar:,}")
            
            st.divider()

            tab_jual, tab_keluar = st.tabs(["💰 Penjualan", "💸 Pengeluaran"])
            
            with tab_jual:
                if not df_k_f.empty:
                    st.dataframe(df_k_f, use_container_width=True)
                    with st.expander("🗑️ Zona Hapus (Hapus jika salah input)"):
                        df_hapus = df_k.tail(5) 
                        for i, row in df_hapus.iterrows():
                            c_txt, c_btn = st.columns([4, 1])
                            c_txt.write(f"🕒 {row['waktu'].strftime('%H:%M')} | {row['pelanggan']} | {row['produk']}")
                            if c_btn.button("Hapus", key=f"del_{i}"):
                                payload = {"action": "delete", "row_index": int(i)}
                                requests.post(URL_KASIR, data=json.dumps(payload))
                                st.cache_data.clear()
                                st.rerun()
                else: st.info("Belum ada penjualan.")

            with tab_keluar:
                st.dataframe(df_p_f, use_container_width=True)
                    
        except: st.warning("Sedang memproses data dari Google Sheets...")
