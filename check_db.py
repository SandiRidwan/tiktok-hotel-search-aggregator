import sqlite3

def cek_database():
    try:
        conn = sqlite3.connect("tiktok_data_center.db")
        cursor = conn.cursor()
        
        # 1. Cek tabel apa saja yang ada
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"[*] Tabel yang ditemukan di database: {tables}")
        
        if 'data_hotel' not in tables:
            print("[!] ERROR: Tabel 'data_hotel' tidak ditemukan!")
            return

        # 2. Cek jumlah data
        cursor.execute("SELECT COUNT(*) FROM data_hotel")
        count = cursor.fetchone()[0]
        print(f"[*] Jumlah total record di 'data_hotel': {count}")
        
        # 3. Ambil contoh 1 data (jika ada)
        if count > 0:
            cursor.execute("SELECT * FROM data_hotel LIMIT 1")
            row = cursor.fetchone()
            print(f"[*] Contoh data terbaru: {row}")
        else:
            print("[!] Tabel ada, tapi kosong. Scraper Anda belum berhasil menyimpan data.")
            
    except Exception as e:
        print(f"[!] Terjadi error saat membaca DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    cek_database()