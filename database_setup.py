import sqlite3

def buat_database():
    conn = sqlite3.connect("tiktok_data_center.db")
    cursor = conn.cursor()
    
    # Mengaktifkan mode WAL agar aman dibaca-tulis oleh banyak thread
    conn.execute("PRAGMA journal_mode=WAL;")
    
    # Aturan Anti-Duplikasi: Jika POI ID dan Merchant yang sama sudah ada, langsung TOLAK/ABAIKAN
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_hotel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            nomor_urut INTEGER,
            nama_hotel TEXT,
            poi_id TEXT,
            rating REAL,
            latitude REAL,
            longitude REAL,
            alamat_lengkap TEXT,
            nama_merchant TEXT,
            mata_uang TEXT,
            harga_raw INTEGER,
            harga_asli INTEGER,
            waktu_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(poi_id, nama_merchant) ON CONFLICT IGNORE
        )
    ''')
    
    # Tabel Checkpoint: Mencatat keyword mana saja yang sudah selesai di-scrape habis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progres_keyword (
            keyword TEXT PRIMARY KEY,
            waktu_selesai TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[v] Database & Sistem Checkpoint Berhasil Diperbarui.")

if __name__ == "__main__":
    buat_database()