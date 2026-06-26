import sqlite3
import csv
from datetime import datetime

def cek_dan_export_csv():
    nama_db = "tiktok_data_center.db"
    waktu_ekspor = datetime.now().strftime("%Y%m%d_%H%M%S")
    nama_csv = f"Data_Hotel_TikTok_{waktu_ekspor}.csv"

    try:
        # 1. Buka Koneksi ke Database
        conn = sqlite3.connect(nama_db)
        cursor = conn.cursor()

        # 2. Ekstrak Header/Nama Kolom
        cursor.execute("SELECT * FROM data_hotel")
        nama_kolom = [description[0] for description in cursor.description]

        # 3. Ambil Seluruh Data
        semua_data = cursor.fetchall()
        total_baris = len(semua_data)

        if total_baris == 0:
            print("[-] Database masih kosong. Tidak ada data yang bisa diekspor.")
            return

        # 4. Tampilkan Preview 5 Data Teratas ke Terminal
        print("=== PREVIEW 5 DATA TERATAS ===")
        for i, baris in enumerate(semua_data[:5]):
            # Indeks: 2 = nama_hotel, 8 = nama_merchant, 9 = mata_uang, 10 = harga_raw
            print(f"{i+1}. {baris[2]} | Merchant: {baris[8]} | Harga: {baris[9]} {baris[10]}")
        print("==============================\n")

        # 5. Tulis ke File CSV
        print(f"[*] Sedang mengekspor {total_baris} baris data ke format CSV...")
        with open(nama_csv, mode='w', newline='', encoding='utf-8') as file_csv:
            writer = csv.writer(file_csv)
            writer.writerow(nama_kolom)  # Tulis Baris Header
            writer.writerows(semua_data) # Tulis Semua Data

        print(f"[+] Selesai! File CSV berhasil dibuat dengan nama: {nama_csv}")

    except Exception as e:
        print(f"[!] Terjadi kesalahan: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    cek_dan_export_csv()