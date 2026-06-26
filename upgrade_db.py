import sqlite3

def upgrade_database():
    conn = sqlite3.connect("tiktok_data_center.db")
    cursor = conn.cursor()
    try:
        # Menambahkan kolom baru ke tabel yang sudah ada
        cursor.execute("ALTER TABLE data_hotel ADD COLUMN harga_sebelum_diskon INTEGER DEFAULT 0;")
        print("[+] Sukses: Kolom 'harga_sebelum_diskon' berhasil ditambahkan ke database!")
    except sqlite3.OperationalError as e:
        print(f"[*] Info: {e} (Kolom kemungkinan sudah ada).")
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    upgrade_database()