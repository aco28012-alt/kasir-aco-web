import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta

# Fungsi Waktu WITA (UTC+8)
def waktu_sekarang():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")

# --- PENGATURAN DASAR ---
PASSWORD_RAHASIA = st.secrets["PASSWORD_RAHASIA"] 
URL_KASIR = st.secrets["URL_KASIR"]
ID_SHEET = st.secrets["ID_SHEET"]

# URL GID milik Aco
URL_BACA_KASIR = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_BACA_PENGELUARAN = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=2102782816"
URL_BACA_ARUSKAS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1780397324"
URL_BACA_JURNAL = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1597087749"

st.set_page_config(page_title="Cultur Coffee - Management", layout="wide")

# --- DATA MENU ---
menu = {
    'HOT COFFEE': {'AMERICANO': 10000, 'ESPRESSO': 8000, 'AMERICANO SPECIAL': 12000, 'COFFE MILK': 10000},
    'COLD COFFEE': {'ICED AMERICANO': 12000, 'LATTE': 15000, 'CAPPUCINO': 15000, 'MOCHA': 16000, 'COFFEE MILK (reguler)': 13000, 'COFFE MILK (small)': 10000},
    'TEA & NON-COFFEE': {'GREAN TEA': 13000, 'THAI TEA': 13000, 'HOT MILK': 10000,'BROWN SUGAR MILK': 14000, 'ICED CHOCOLATE': 13000, 'HOT CHOCOLATE': 12000, 'ICED MILK': 12000, 'EKSTRA JOSS SUSU': 7000},
    'SPECIALITY DRINKS': {'PANDAN LATTE': 15000, 'HAZELNUT LATTE': 15000, 'BUTTERSCOTCH LATTE': 15000, 'SPAINISH LATTE': 16000},
    'SIGNATURE': {'KOPI KULT': 15000, 'KOPI ARENITA': 15000, 'ICED AMERICANO SPECIAL': 15000},
    'MANUAL BREW': {'V60': 20000, 'VIETNAM DRIP': 13000},
    'MOCKTAIL': {'MANGOSQUASH': 14000, 'BLUEOCEAN': 14000, 'REDBLISS': 14000}
}

semua_harga = {}
for kategori in menu: semua_harga.update(menu[kategori])

if 'keranjang' not in st.session_state: st.session_state.keranjang = {}

def tambah_ke_keranjang(nama_item):
    st.session_state.keranjang[nama_item] = st.session_state.keranjang.get(nama_item, 0) + 1

def reset_keranjang(): st.session_state.keranjang = {}

# --- LOGIN ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    st.title("🔐 Akses Terkunci - Cultur Coffee")
    input_pass = st.text_input("Masukkan Password", type="password")
    if st.button("Masuk"):
        if input_pass == PASSWORD_RAHASIA:
            st.session_state["authenticated"] = True
            st.rerun()
else:
    with st.sidebar:
        st.title("🚀 Navigasi")
        pilihan = st.radio("Menu Utama:", ["🛒 Kasir Pro", "💸 Pengeluaran", "📋 Laporan Keuangan"])
        if st.button("🚪 Keluar"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- HALAMAN KASIR ---
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
                            if st.button(f"**{item}**\n\nRp {harga:,}", key=f"btn_{item}", use_container_width=True):
                                tambah_ke_keranjang(item)
                                st.toast(f"{item} ditambahkan!")
        with col_p:
            st.subheader("🛒 Keranjang")
            if not st.session_state.keranjang: st.info("Pilih menu")
            else:
                total_bayar = sum(semua_harga[item] * qty for item, qty in st.session_state.keranjang.items())
                for item, qty in st.session_state.keranjang.items():
                    st.write(f"**{item}** x{qty}")
                st.divider()
                st.write(f"### Total: Rp {total_bayar:,}")
                nama_plg = st.text_input("Nama Pelanggan").strip().upper()
                
                if st.button("KONFIRMASI PEMBAYARAN", type="primary", use_container_width=True):
                    if nama_plg:
                        pesanan_final = st.session_state.keranjang.copy()
                        st.session_state.keranjang = {}
                        with st.spinner("Mencatat..."):
                            jam_trx = waktu_sekarang()
                            for item, qty in pesanan_final.items():
                                payload = {"action": "save", "type": "kasir", "waktu": jam_trx, "pelanggan": nama_plg, "produk": item, "qty": qty, "harga": semua_harga[item], "total": semua_harga[item]*qty}
                                requests.post(URL_KASIR, data=json.dumps(payload))
                            
                            requests.post(URL_KASIR, data=json.dumps({"action": "save", "type": "aruskas", "waktu": jam_trx, "kategori": "Penjualan", "keterangan": f"Order {nama_plg}", "masuk": total_bayar, "keluar": 0}))
                            requests.post(URL_KASIR, data=json.dumps({"action": "save", "type": "jurnal", "waktu": jam_trx, "ket": f"Penjualan {nama_plg}", "debit_akun": "Kas", "kredit_akun": "Pendapatan", "nilai": total_bayar}))
                            st.cache_data.clear(); st.success("Tersimpan!"); st.rerun()
                    else: st.warning("Isi nama pelanggan!")
                if st.button("Reset Keranjang"): reset_keranjang(); st.rerun()

    # --- HALAMAN PENGELUARAN ---
    elif pilihan == "💸 Pengeluaran":
        st.title("💸 Catat Pengeluaran")
        kat = st.selectbox("Kategori", ["Bahan Baku", "Operasional", "Gaji", "Lain-lain"])
        ket = st.text_input("Keterangan Pengeluaran")
        nom = st.number_input("Nominal (Rp)", min_value=0, step=1000)
        
        if st.button("Simpan Pengeluaran", use_container_width=True):
            if ket and nom > 0:
                jam_trx = waktu_sekarang()
                requests.post(URL_KASIR, data=json.dumps({"action": "save", "type": "pengeluaran", "waktu": jam_trx, "kategori": kat, "keterangan": ket, "nominal": nom}))
                requests.post(URL_KASIR, data=json.dumps({"action": "save", "type": "aruskas", "waktu": jam_trx, "kategori": kat, "keterangan": ket, "masuk": 0, "keluar": nom}))
                requests.post(URL_KASIR, data=json.dumps({"action": "save", "type": "jurnal", "waktu": jam_trx, "ket": ket, "debit_akun": f"Beban {kat}", "kredit_akun": "Kas", "nilai": nom}))
                st.cache_data.clear(); st.success("Pengeluaran Tercatat!")
            else: st.warning("Lengkapi data!")

    # --- HALAMAN LAPORAN ---
    elif pilihan == "📋 Laporan Keuangan":
        st.title("📊 Dashboard Cultur Coffee")
        try:
            ts = datetime.now().timestamp()
            df_k = pd.read_csv(f"{URL_BACA_KASIR}&t={ts}")
            df_p = pd.read_csv(f"{URL_BACA_PENGELUARAN}&t={ts}")
            df_ak = pd.read_csv(f"{URL_BACA_ARUSKAS}&t={ts}")
            df_j = pd.read_csv(f"{URL_BACA_JURNAL}&t={ts}")
            
            # Pre-processing waktu
            for d in [df_k, df_p, df_ak, df_j]:
                d['waktu'] = pd.to_datetime(d['waktu'])

            tab1, tab2, tab3, tab4 = st.tabs(["💰 Penjualan", "💸 Pengeluaran", "📈 Arus Kas", "📖 Jurnal Umum"])
            
            # --- TAB PENJUALAN ---
            with tab1:
                st.subheader("Filter Penjualan")
                m1 = st.radio("Tampilan Penjualan:", ["Harian", "Bulanan"], horizontal=True, key="m1")
                if m1 == "Harian":
                    t1 = st.date_input("Pilih Tanggal", datetime.now() + timedelta(hours=8), key="t1")
                    df_res = df_k[df_k['waktu'].dt.date == t1]
                else:
                    b1 = st.selectbox("Pilih Bulan", df_k['waktu'].dt.to_period('M').unique(), key="b1")
                    df_res = df_k[df_k['waktu'].dt.to_period('M') == b1]
                
                st.metric("Total Omzet", f"Rp {df_res['total'].sum():,}")
                st.dataframe(df_res, use_container_width=True)
                with st.expander("🗑️ Hapus Transaksi Terakhir"):
                    for i, row in df_k.tail(5).iterrows():
                        c_t, c_b = st.columns([4, 1])
                        c_t.write(f"{row['waktu']} | {row['pelanggan']} | Rp {row['total']:,}")
                        if c_b.button("Hapus", key=f"del_{i}"):
                            requests.post(URL_KASIR, data=json.dumps({"action": "delete", "row_index": int(i)}))
                            st.cache_data.clear(); st.rerun()

            # --- TAB PENGELUARAN ---
            with tab2:
                st.subheader("Filter Pengeluaran")
                m2 = st.radio("Tampilan Pengeluaran:", ["Harian", "Bulanan"], horizontal=True, key="m2")
                if m2 == "Harian":
                    t2 = st.date_input("Pilih Tanggal", datetime.now() + timedelta(hours=8), key="t2")
                    df_res_p = df_p[df_p['waktu'].dt.date == t2]
                else:
                    b2 = st.selectbox("Pilih Bulan", df_p['waktu'].dt.to_period('M').unique(), key="b2")
                    df_res_p = df_p[df_p['waktu'].dt.to_period('M') == b2]
                
                st.metric("Total Pengeluaran", f"Rp {df_res_p['nominal'].sum():,}")
                st.dataframe(df_res_p, use_container_width=True)

            # --- TAB ARUS KAS ---
            with tab3:
                st.subheader("Filter Arus Kas")
                m3 = st.radio("Tampilan Arus Kas:", ["Harian", "Bulanan"], horizontal=True, key="m3")
                if m3 == "Harian":
                    t3 = st.date_input("Pilih Tanggal", datetime.now() + timedelta(hours=8), key="t3")
                    df_res_ak = df_ak[df_ak['waktu'].dt.date == t3]
                else:
                    b3 = st.selectbox("Pilih Bulan", df_ak['waktu'].dt.to_period('M').unique(), key="b3")
                    df_res_ak = df_ak[df_ak['waktu'].dt.to_period('M') == b3]
                
                if not df_res_ak.empty:
                    df_res_ak['Saldo'] = df_res_ak['masuk'].cumsum() - df_res_ak['keluar'].cumsum()
                    st.dataframe(df_res_ak, use_container_width=True)
                    st.line_chart(df_res_ak.set_index('waktu')['Saldo'])

            # --- TAB JURNAL ---
            with tab4:
                st.subheader("Filter Jurnal Umum")
                m4 = st.radio("Tampilan Jurnal:", ["Harian", "Bulanan"], horizontal=True, key="m4")
                if m4 == "Harian":
                    t4 = st.date_input("Pilih Tanggal", datetime.now() + timedelta(hours=8), key="t4")
                    df_res_j = df_j[df_j['waktu'].dt.date == t4]
                else:
                    b4 = st.selectbox("Pilih Bulan", df_j['waktu'].dt.to_period('M').unique(), key="b4")
                    df_res_j = df_j[df_j['waktu'].dt.to_period('M') == b4]
                
                st.dataframe(df_res_j, use_container_width=True)
                deb, kre = df_res_j['debit'].sum(), df_res_j['kredit'].sum()
                st.write(f"**Debit:** Rp {deb:,} | **Kredit:** Rp {kre:,}")
                if deb == kre: st.success("Balance ✅")
                else: st.error("Unbalanced ❌")

        except Exception as e:
            st.error(f"Error: {e}")
