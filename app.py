import streamlit as st
import pandas as pd
from datetime import datetime

# --- SETTING HALAMAN ---
st.set_page_config(page_title="Kasir Cafe Aco", layout="wide")

# --- DATA MENU (Sama dengan kode lamamu) ---
daftar_menu = {
    'AMERICANO': 10000, 'AMERICANO SPESIAL': 15000, 'ESPRESSO': 8000, 'COFFE MILK': 10000,
    'ICED AMERICANO': 12000, 'ICED AMERICANO SPESIAL': 15000, 'ICED LATTE': 15000,
    'ICED CAPPUCINO': 15000, 'ICED MOCHA': 16000, 'ICED COFFE MILK (REGULER)': 13000,
    'ICED COFFE MILK (SMALL)': 10000, 'GREAN TEA': 13000, 'THAI TEA': 13000,
    'HOT MILK': 10000, 'BROWN SUGAR MILK': 14000, 'ICED CHOCOLATE': 13000,
    'HOT CHOCOLATE': 12000, 'EKSTRAJOSS SUSU': 7000, 'PANDAN LATTE': 15000,
    'HAZELNUT LATTE': 15000, 'BUTTERSCOTCH LATTE': 15000, 'SPAINISH LATTE': 16000,
    'KOPI KULT': 15000, 'KOPI ARENITA': 15000, 'V60': 20000, 'VIETNAM DRIP': 13000,
    'MANGOSQUASH': 14000, 'BLUEOCEAN': 20000, 'REDBLISS': 15000
}

# Inisialisasi data sementara di memori browser
if 'data_penjualan' not in st.session_state:
    st.session_state.data_penjualan = pd.DataFrame(columns=['Waktu', 'Pelanggan', 'Produk', 'Qty', 'Harga', 'Total'])

# --- TAMPILAN WEB ---
st.title("☕ Kasir Cafe Aco Online")

with st.sidebar:
    st.header("Input Pesanan")
    # Nama Pelanggan (Ingat logika kita: Pakai nama terakhir kalau kosong)
    if 'nama_terakhir' not in st.session_state:
        st.session_state.nama_terakhir = "ANONIM"
    
    nama_input = st.text_input("Nama Pelanggan", value=st.session_state.nama_terakhir)
    
    # Pilih Produk (Pakai dropdown biar cepat)
    produk_pilihan = st.selectbox("Pilih Produk", list(daftar_menu.keys()))
    
    # Jumlah
    qty = st.number_input("Jumlah (Qty)", min_value=1, value=1)
    
    if st.button("Catat Pesanan"):
        st.session_state.nama_terakhir = nama_input.upper()
        harga = daftar_menu[produk_pilihan]
        total = harga * qty
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Simpan ke tabel sementara
        new_row = {
            'Waktu': waktu, 
            'Pelanggan': nama_input.upper(), 
            'Produk': produk_pilihan, 
            'Qty': qty, 
            'Harga': harga,
            'Total': total
        }
        st.session_state.data_penjualan = pd.concat([st.session_state.data_penjualan, pd.DataFrame([new_row])], ignore_index=True)
        st.success(f"✅ Dicatat: {produk_pilihan} x{qty}")

# --- BAGIAN UTAMA (LAPORAN) ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Transaksi Saat Ini")
    st.dataframe(st.session_state.data_penjualan, use_container_width=True)

with col2:
    st.subheader("💰 Total Pendapatan")
    grand_total = st.session_state.data_penjualan['Total'].sum()
    st.metric(label="Total RP", value=f"Rp {grand_total:,.0f}".replace(",", "."))
    
    if st.button("🗑️ Hapus Terakhir"):
        if not st.session_state.data_penjualan.empty:
            st.session_state.data_penjualan = st.session_state.data_penjualan.iloc[:-1]
            st.rerun()

    # Tombol download CSV hasil jualan
    if not st.session_state.data_penjualan.empty:
        csv = st.session_state.data_penjualan.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Penjualan (CSV)",
            data=csv,
            file_name=f"penjualan_{datetime.now().strftime('%Y_%m_%d')}.csv",
            mime='text/csv',
        )
