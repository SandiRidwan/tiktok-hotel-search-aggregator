import sqlite3
import time
import random
import requests
import urllib.parse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- KONFIGURASI GLOBAL ---
DEVICE_ID = os.getenv("TIKTOK_DEVICE_ID", "")
SESSION_ID = os.getenv("TIKTOK_SESSION_ID", "")
INSTALL_ID = os.getenv("TIKTOK_INSTALL_ID", "")
RPC_SERVER = "http://127.0.0.1:8080/sign"
MAX_THREADS = 5

# --- FUNGSI DB ---
def ambil_keyword_terproses():
    conn = sqlite3.connect("tiktok_data_center.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS progres_keyword (keyword TEXT PRIMARY KEY)")
    cursor.execute("SELECT keyword FROM progres_keyword")
    rows = cursor.fetchall()
    conn.close()
    return set([row[0] for row in rows])

def tandai_keyword_selesai(keyword):
    conn = sqlite3.connect("tiktok_data_center.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO progres_keyword (keyword) VALUES (?)", (keyword,))
    conn.commit()
    conn.close()

def simpan_ke_db(data_list):
    if not data_list: return
    
    # Menambahkan timeout 10 detik agar aman jika ada bentrokan antar thread
    conn = sqlite3.connect("tiktok_data_center.db", timeout=10)
    cursor = conn.cursor()
    
    try:
        # Perhatikan: offset_ke diubah menjadi nomor_urut, dan harga_sebelum_diskon menjadi harga_asli
        cursor.executemany('''
            INSERT OR IGNORE INTO data_hotel 
            (keyword, nomor_urut, nama_hotel, poi_id, rating, latitude, longitude, alamat_lengkap, nama_merchant, mata_uang, harga_raw, harga_asli)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data_list)
        conn.commit()
    except Exception as e:
        print(f"    [!] Gagal menyimpan ke DB: {e}")
    finally:
        conn.close()

# --- LOGIKA EKSTRAKSI ---
def proses_ekstraksi_keyword(keyword):
    offset = 0
    limit_per_request = 20
    nomor_urut = 1  # Variabel baru untuk melacak peringkat/urutan hotel yang sesungguhnya
    
    print(f"[*] Memulai ekstraksi: {keyword}")
    
    while True:
        # Sistem Evasion Terkalibrasi (Membatasi akurasi di 85%)
        if random.random() > 0.85:
            print(f"    [!] [Evasion] Simulasi jeda manual pada '{keyword}'. Mencoba ulang nanti...")
            time.sleep(random.uniform(2.0, 5.0))
            break

        base_url = (
            "https://search22-normal-c-alisg.tiktokv.com/aweme/v1/search/place/?"
            "device_platform=android&os=android&ssmix=a&device_type=sdk_gphone64_x86_64"
            f"&device_id={DEVICE_ID}&iid={INSTALL_ID}&channel=beta_closedtesting"
            "&aid=1233&app_name=musical_ly&version_code=450742&version_name=45.7.42"
            "&manifest_version_code=2024507420&update_version_code=2024507420"
            "&language=id&app_language=id&sys_region=ID&current_region=ID&region=ID"
        )

        try:
            rpc_res = requests.post(RPC_SERVER, json={"url": base_url}, timeout=5)
            stempel = rpc_res.json()
            
            headers = {
                "User-Agent": "com.zhiliaoapp.musically/2024507420 (Linux; U; Android 14; en; sdk_gphone64_x86_64; Build/UE1A.230829.036.A4;tt-ok/3.12.13.21)",
                "Cookie": f"sessionid={SESSION_ID}; install_id={INSTALL_ID}; store-country-code=id;",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Gorgon": stempel['headers']['X-Gorgon'],
                "X-Khronos": stempel['headers']['X-Khronos']
            }
            
            payload_data = f"keyword={urllib.parse.quote_plus(keyword)}&offset={offset}&count={limit_per_request}&search_source=switch_tab&sug_generate_type=0&current_location_status=0&multi_virtual_rs=1"
            
            response = requests.post(base_url, headers=headers, data=payload_data, timeout=10)
            if response.status_code != 200:
                print(f"    [-] '{keyword}' ditolak status {response.status_code}")
                break
                
            json_data = json.loads(response.text)
            
            poi_root = json_data.get("poi_info", {})
            daftar_hotel = poi_root.get("poi_info", []) if isinstance(poi_root, dict) else poi_root
            
            if not daftar_hotel:
                tandai_keyword_selesai(keyword)
                print(f"    [v] Halaman habis/selesai untuk '{keyword}'.")
                break

            data_batch = []
            for item in daftar_hotel:
                nama_hotel = item.get("poi_name", "N/A")
                poi_id = item.get("poi_id_str", item.get("poi_id", "0"))
                rating = item.get("poi_rating", item.get("rating", 0.0))
                lokasi = item.get("poi_location", item.get("share_info", {}).get("desc", "Tidak Ada Alamat"))
                
                latitude = float(item.get("lat", 0.0)) if item.get("lat") else 0.0
                longitude = float(item.get("lng", 0.0)) if item.get("lng") else 0.0
                
                merchant_list = item.get("ls_merchant_list", [])
                if not merchant_list:
                    # Ganti variabel 'offset' menjadi 'nomor_urut'
                    data_batch.append((keyword, nomor_urut, nama_hotel, poi_id, rating, latitude, longitude, lokasi, "N/A", "-", 0, 0))
                else:
                    for m in merchant_list:
                        harga_raw = m.get("raw_price", m.get("price_raw", 0))
                        
                        orig_price_str = m.get("original_price", "0")
                        cleaned_price = ''.join(c for c in str(orig_price_str) if c.isdigit())
                        harga_asli = int(cleaned_price) if cleaned_price else int(harga_raw)
                        
                        # Ganti variabel 'offset' menjadi 'nomor_urut'
                        data_batch.append((
                            keyword, nomor_urut, nama_hotel, poi_id, rating, latitude, longitude, lokasi,
                            m.get("merchant_name", "N/A"), m.get("currency_symbol", "-"), 
                            harga_raw, harga_asli
                        ))
                
                # Tambahkan 1 untuk hotel selanjutnya di dalam kata kunci ini
                nomor_urut += 1 

            simpan_ke_db(data_batch)
            offset += limit_per_request
            time.sleep(random.uniform(1.0, 2.5))

        except Exception as e:
            print(f"    [!] Error pada '{keyword}': {e}")
            break

    return f"[+] Selesai: {keyword}"

def bangun_daftar_keyword():
    tipe_akomodasi = ["Hotel", "Penginapan", "Resort", "Villa", "Hostel", "Homestay", "Glamping"]
    
    # Cakupan wilayah super lengkap dan masif untuk 5 Negara Target
    destinasi = {
        "Indonesia": [
            # Jawa & Jabodetabek
            "Jakarta", "Bogor", "Depok", "Tangerang", "Bekasi", "Bandung", "Lembang", "Soreang", 
            "Cirebon", "Sukabumi", "Cianjur", "Puncak", "Garut", "Tasikmalaya", "Pangandaran", 
            "Semarang", "Yogyakarta", "Sleman", "Bantul", "Gunungkidul", "Kulon Progo", "Solo", 
            "Surakarta", "Magelang", "Salatiga", "Tegal", "Pekalongan", "Purwokerto", "Banyumas",
            "Surabaya", "Malang", "Batu", "Banyuwangi", "Jember", "Kediri", "Madiun", "Probolinggo", 
            "Pasuruan", "Mojokerto", "Pacitan",
            # Bali & Nusa Tenggara
            "Denpasar", "Kuta", "Seminyak", "Canggu", "Ubud", "Nusa Dua", "Sanur", "Jimbaran", 
            "Uluwatu", "Nusa Penida", "Nusa Lembongan", "Kintamani", "Singaraja", "Lovina", 
            "Mataram", "Lombok", "Senggigi", "Gili Trawangan", "Gili Air", "Gili Meno", "Kuta Lombok", 
            "Labuan Bajo", "Kupang", "Ende", "Maumere", "Sumba",
            # Sumatera
            "Medan", "Berastagi", "Parapat", "Danau Toba", "Samosir", "Tongging", "Banda Aceh", 
            "Sabang", "Weh", "Padang", "Bukittinggi", "Pekanbaru", "Batam", "Tanjung Pinang", 
            "Bintan", "Palembang", "Jambi", "Bengkulu", "Bandar Lampung", "Pangkal Pinang", "Bangka", 
            "Belitung", "Teluk Dalam", "Teluk Nibung", "Nias",
            # Kalimantan
            "Pontianak", "Singkawang", "Banjarmasin", "Banjarbaru", "Balikpapan", "Samarinda", 
            "Bontang", "Tarakan", "Palangkaraya", "Derawan",
            # Sulawesi, Maluku & Papua
            "Makassar", "Manado", "Tomohon", "Bunaken", "Bitung", "Gorontalo", "Palu", "Kendari", 
            "Wakatobi", "Toraja", "Ambon", "Ternate", "Jayapura", "Sorong", "Raja Ampat", "Merauke"
        ],
        "Malaysia": [
            "Kuala Lumpur", "George Town", "Penang", "Batu Ferringhi", "Melaka", "Langkawi", 
            "Johor Bahru", "Kota Kinabalu", "Kuching", "Ipoh", "Shah Alam", "Petaling Jaya", 
            "Subang Jaya", "Cyberjaya", "Putrajaya", "Kuantan", "Kuala Terengganu", "Kota Bharu", 
            "Alor Setar", "Seremban", "Genting Highlands", "Cameron Highlands", "Port Dickson", 
            "Semporna", "Sandakan", "Miri", "Taiping", "Klang"
        ],
        "Thailand": [
            "Bangkok", "Phuket", "Patong", "Kata Beach", "Karon", "Pattaya", "Jomtien", 
            "Chiang Mai", "Krabi", "Ao Nang", "Koh Samui", "Chaweng", "Lamai", "Hua Hin", 
            "Chiang Rai", "Ayutthaya", "Nonthaburi", "Hat Yai", "Udon Thani", "Khon Kaen", 
            "Surat Thani", "Chonburi", "Kanchanaburi", "Pai", "Sukhothai", "Rayong", 
            "Koh Phangan", "Koh Tao", "Koh Chang", "Cha-am"
        ],
        "Singapore": [
            # Karena Singapura adalah City-State, pencarian dipecah per wilayah/distrik komersial & wisata utama
            "Marina Bay", "Sentosa", "Orchard", "Chinatown", "Little India", "Bugis", 
            "Geylang", "Clarke Quay", "Jurong", "Changi", "Tampines", "Woodlands", 
            "Katong", "Novena", "Tiong Bahru", "Kampong Glam", "HarbourFront", "Balestier", 
            "Lavender", "River Valley", "Bukit Timah", "East Coast"
        ],
        "Japan": [
            "Tokyo", "Shinjuku", "Shibuya", "Asakusa", "Ginza", "Osaka", "Umeda", 
            "Namba", "Kyoto", "Gion", "Sapporo", "Okinawa", "Naha", "Fukuoka", 
            "Nagoya", "Yokohama", "Kobe", "Hiroshima", "Nara", "Sendai", "Kanazawa", 
            "Nagasaki", "Takayama", "Hakodate", "Kamakura", "Nikko", "Kawaguchiko", 
            "Hakone", "Fuji", "Beppu", "Yufuin", "Karuizawa", "Himeji", "Matsuyama"
        ]
    }
    
    daftar_keyword = []
    for negara, kota_list in destinasi.items():
        for kota in kota_list:
            for tipe in tipe_akomodasi:
                # Menghasilkan variasi kombinasi natural, contoh: "Glamping di Lembang" atau "Resort di Phuket"
                daftar_keyword.append(f"{tipe} di {kota}")
                
    random.shuffle(daftar_keyword) 
    return daftar_keyword

def jalankan_mesin_massal():
    seluruh_keyword = bangun_daftar_keyword()
    keyword_sukses = ambil_keyword_terproses()
    keyword_sisa = [kw for kw in seluruh_keyword if kw not in keyword_sukses]
    
    print(f"[*] Menjalankan {len(keyword_sisa)} keyword sisa.")
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(proses_ekstraksi_keyword, kw): kw for kw in keyword_sisa}
        for future in as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    jalankan_mesin_massal()