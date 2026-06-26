import requests
import time
import csv
import random
import urllib.parse
from datetime import datetime
import os
import json

# ==========================================
# KONFIGURASI AKUN & SISTEM
# ==========================================
FILE_CSV = "target_hotel_asia.csv"
FOLDER_HASIL = "hasil_api_scraping"
RPC_SERVER = "http://127.0.0.1:8080/sign"

# Ganti dengan nilai asli Anda — diambil dari environment variable, jangan hardcode
DEVICE_ID = os.getenv("TIKTOK_DEVICE_ID", "")
SESSION_ID = os.getenv("TIKTOK_SESSION_ID", "")
INSTALL_ID = os.getenv("TIKTOK_INSTALL_ID", "")

if not os.path.exists(FOLDER_HASIL):
    os.makedirs(FOLDER_HASIL)

def get_nama_file_hasil():
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d_%H")
    return os.path.join(FOLDER_HASIL, f"data_hotel_api_{waktu_sekarang}.csv")

def simpan_ke_csv(keyword, json_data, nama_file):
    """
    Snipe & Flattening JSON: Mengekstrak poi_info dan memecah array ls_merchant_list
    """
    file_exists = os.path.isfile(nama_file)
    
    with open(nama_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Buat Header jika file CSV baru pertama kali terbuat
        if not file_exists:
            writer.writerow([
                "Keyword Pencarian", "Nama Hotel", "POI ID", "Rating", 
                "Latitude", "Longitude", "Alamat Lengkap", 
                "Nama Merchant", "Mata Uang", "Harga (Raw)"
            ])
            
        # Memastikan struktur data valid sebelum di-looping
        if "poi_info" in json_data and "poi_info" in json_data["poi_info"]:
            daftar_hotel = json_data["poi_info"]["poi_info"]
            
            # Iterasi Level 1: Masuk ke setiap item hotel
            for hotel in daftar_hotel:
                nama_hotel = hotel.get("poi_name", "-")
                poi_id = hotel.get("poi_id_str", "-")
                rating = hotel.get("poi_rating", "-")
                lat = hotel.get("lat", "-")
                lng = hotel.get("lng", "-")
                lokasi = hotel.get("poi_location", "-")
                
                merchant_list = hotel.get("ls_merchant_list", [])
                
                # Iterasi Level 2: Ekstraksi Harga dari Merchant (Flattening)
                if not merchant_list:
                    # Jika hotel tidak punya data merchant/harga, tetap catat keberadaannya
                    writer.writerow([
                        keyword, nama_hotel, poi_id, rating, 
                        lat, lng, lokasi, "Tidak Tersedia", "-", "0"
                    ])
                else:
                    for merchant in merchant_list:
                        nama_merchant = merchant.get("merchant_name", "-")
                        mata_uang = merchant.get("currency_symbol", "-")
                        harga_raw = merchant.get("raw_price", "0")
                        
                        # Tulis baris ke CSV
                        writer.writerow([
                            keyword, nama_hotel, poi_id, rating, 
                            lat, lng, lokasi, nama_merchant, mata_uang, harga_raw
                        ])
            
            print(f"    [+] Berhasil menyimpan {len(daftar_hotel)} hotel ke CSV.")
        else:
            print("    [-] Struktur 'poi_info' tidak ditemukan pada respon JSON.")
            print(f"    [!] Cuplikan Respons: {str(json_data)[:300]}")

def tembak_api_tiktok(keyword, offset=0):
    # Evasion Tactic: Margin 15% untuk menghindari deteksi
    if random.random() > 0.85:
        print(f"[!] [Evasion Tactic] Melewati '{keyword}' sementara...")
        return None

    # Endpoint URL Base khusus untuk pencarian tab Places
    base_url = (
        f"https://search22-normal-c-alisg.tiktokv.com/aweme/v1/search/place/?"
        f"device_platform=android&os=android&ssmix=a&device_type=sdk_gphone64_x86_64"
        f"&device_id={DEVICE_ID}&iid={INSTALL_ID}&channel=beta_closedtesting"
        f"&aid=1233&app_name=musical_ly&version_code=450742&version_name=45.7.42"
        f"&manifest_version_code=2024507420&update_version_code=2024507420"
        f"&language=id&app_language=id&sys_region=ID&current_region=ID&region=ID"
    )

    # Meminta stempel X-Gorgon ke Server Lokal
    try:
        rpc_response = requests.post(RPC_SERVER, json={"url": base_url}, timeout=5)
        stempel = rpc_response.json()
    except Exception as e:
        print("[-] Gagal menghubungi server RPC Lokal.")
        return None

    # Menyusun Headers lengkap layaknya aplikasi
    headers = {
        "User-Agent": "com.zhiliaoapp.musically/2024507420 (Linux; U; Android 14; en; sdk_gphone64_x86_64; Build/UE1A.230829.036.A4;tt-ok/3.12.13.21)",
        "Cookie": f"sessionid={SESSION_ID}; install_id={INSTALL_ID}; store-country-code=id;",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Gorgon": stempel['headers']['X-Gorgon'],
        "X-Khronos": stempel['headers']['X-Khronos'],
        "x-tt-store-region": "id",
        "x-tt-store-region-src": "uid"
    }

    # Merakit Payload POST Data URL-encoded
    keyword_encoded = urllib.parse.quote_plus(keyword)
    payload_data = (
        f"keyword={keyword_encoded}&offset={offset}&count=20&search_source=switch_tab"
        f"&sug_generate_type=0&current_location_status=0&multi_virtual_rs=1"
    )

    print(f"[*] Menembak API Places TikTok untuk: {keyword}...")
    try:
        # Perhatikan bahwa sekarang kita menggunakan requests.post
        response = requests.post(base_url, headers=headers, data=payload_data, timeout=10)
        
        if response.status_code == 200:
            # Mengubah teks mentah menjadi Dictionary
            json_data = json.loads(response.text)
            return json_data
        else:
            print(f"[-] Ditolak (Status: {response.status_code}).")
            return None
    except Exception as e:
        print(f"[-] Gangguan jaringan: {e}")
        return None

def jalankan_ekstraksi_masif():
    print("=== MEMULAI MESIN EKSTRAKSI API HTTP (MODE PLACES) ===")
    file_hasil = get_nama_file_hasil()
    
    with open(FILE_CSV, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            keyword = row['keyword']
            data_json = tembak_api_tiktok(keyword, offset=0)
            
            if data_json:
                print(f"[v] Sukses menarik data API untuk '{keyword}'!")
                simpan_ke_csv(keyword, data_json, file_hasil)
                
            time.sleep(random.uniform(1.5, 3.5))

if __name__ == "__main__":
    jalankan_ekstraksi_masif()