import sqlite3
conn = sqlite3.connect("tiktok_data_center.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM progres_keyword")
conn.commit()
conn.close()
print("[*] Progres berhasil di-reset. Silakan jalankan scraper kembali.")