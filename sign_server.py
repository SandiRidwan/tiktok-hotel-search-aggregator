from fastapi import FastAPI, Request
from pydantic import BaseModel
import time
import hashlib
import random
import uvicorn

app = FastAPI()

# Model untuk menerima data dari scraper
class PayloadData(BaseModel):
    url: str
    data: str = ""
    cookies: str = ""

def generate_mock_gorgon(url: str, ts: int) -> str:
    # Simulasi hashing sederhana untuk keperluan testing lokal
    base_string = f"{url}-{ts}-salt"
    return "04" + hashlib.md5(base_string.encode()).hexdigest() + "0000"

@app.post("/sign")
async def sign_request(payload: PayloadData):
    """
    Endpoint utama untuk generate X-Gorgon dan X-Khronos.
    Selalu mengembalikan JSON agar tidak error di sisi client.
    """
    try:
        # Menambahkan sedikit delay untuk perilaku organik
        if random.random() > 0.85:
            time.sleep(random.uniform(0.5, 1.5))
            
        current_time = int(time.time())
        
        # Proses pembuatan signature
        x_gorgon = generate_mock_gorgon(payload.url, current_time)
        x_khronos = str(current_time)
        
        # Respons yang konsisten dalam bentuk JSON
        return {
            "status": "success",
            "headers": {
                "X-Gorgon": x_gorgon,
                "X-Khronos": x_khronos
            }
        }
    except Exception as e:
        # Jika ada error internal, kirimkan JSON berisi keterangan error
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # Menjalankan server di port 8080
    uvicorn.run(app, host="127.0.0.1", port=8080)