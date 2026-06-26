import sqlite3
import os
import time
import sys

def monitor_live():
    nama_db = "tiktok_data_center.db"
    
    if not os.path.exists(nama_db):
        print("[-] Database belum ditemukan.")
        return

    try:
        while True:
            # Membersihkan terminal agar terlihat seperti dashboard live
            os.system('cls' if os.name == 'nt' else 'clear')
            
            conn = sqlite3.connect(nama_db)
            cursor = conn.cursor()

            # Mengambil statistik
            cursor.execute("SELECT COUNT(*) FROM data_hotel")
            total_hotel = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM progres_keyword")
            total_keyword = cursor.fetchone()[0]

            print("="*60)
            print("          LIVE MONITORING TIKTOK DATA CENTER          ")
            print("="*60)
            print(f"[*] Total Data Terkumpul : {total_hotel:,} baris")
            print(f"[*] Keyword Selesai      : {total_keyword:,}")
            print(f"[*] Status               : MENGAMBIL DATA...")
            print("="*60)

            # Tampilkan 10 data terbaru
            cursor.execute('''
                SELECT keyword, nama_hotel, nama_merchant, harga_asli, waktu_scraped 
                FROM data_hotel 
                ORDER BY id DESC LIMIT 10
            ''')
            rows = cursor.fetchall()
            
            print(f"{'KEYWORD':<20} | {'HOTEL':<15} | {'MERCHANT':<10} | {'HARGA ASLI'}")
            print("-" * 60)
            for row in rows:
                print(f"{row[0][:18]:<20} | {row[1][:15]:<15} | {row[2][:10]:<10} | {row[3]:,}")

            conn.close()
            
            # Jeda 3 detik sebelum refresh
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n[!] Monitoring dihentikan.")
        sys.exit()

if __name__ == "__main__":
    monitor_live()