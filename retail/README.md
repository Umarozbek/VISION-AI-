# Retail Analytics Platform

Haqiqiy IP kameralar bilan ishlaydigan retail analytics tizimi.

## Imkoniyatlar

- **RTSP kamera** — IP, login, parol orqali ulanish (Hikvision, Dahua, Uniview)
- **YOLOv8n** — bepul person detection va tracking
- **Kirish/chiqish sanash** — kirish eshigi kamerasida chiziq kesish
- **Yosh va jins** — OpenCV DNN modellari (bepul)
- **Xodim aniqlash** — uniforma rangi bo'yicha (ko'k forma)
- **Dwell time** — qaysi zonada qancha vaqt turgani
- **Yo'nalish tahlili** — qaysi tomonga ko'proq harakat
- **Heatmap** — real-time zona trafik xaritasi

## Ishga tushirish

```bash
docker compose up --build
```

| Xizmat | Manzil |
|--------|--------|
| Dashboard | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |

**Login:** `admin` / `admin123`

## Kamera qo'shish

1. Dashboard → **Cameras** → **Kamera qo'shish**
2. Maydonlarni to'ldiring:
   - **IP manzil** — masalan `192.168.1.64`
   - **Login / Parol** — kamera admin ma'lumotlari
   - **Kamera turi** — Hikvision, Dahua yoki Boshqa
3. **Ulanishni tekshirish** tugmasini bosing
4. **Saqlash** — AI service 10 soniya ichida avtomatik ulanadi

### RTSP yo'llari (standart)

| Brend | Stream yo'li |
|-------|-------------|
| Hikvision | `Streaming/Channels/101` |
| Dahua | `cam/realmonitor?channel=1&subtype=0` |
| Uniview | `media/video1` |

### Kirish eshigi kamerasi

"Kirish eshigi" switchini yoqing — AI kirgan/chiqgan odamlarni sanaydi va yosh/jins/staff aniqlaydi.

## AI modellari (bepul)

| Model | Vazifa |
|-------|--------|
| YOLOv8n | Odamlarni aniqlash va tracking |
| OpenCV Age/Gender Net | Yosh va jins tahlili |
| ByteTrack (Ultralytics) | Track ID saqlash |

## Muhim eslatmalar

- Kamera va server **bir xil tarmoqda** bo'lishi kerak
- Docker ichidan kameraga ulanish uchun kamera IP to'g'ri bo'lishi kerak
- Birinchi ishga tushirishda YOLO modeli yuklanadi (~6 MB)
- AI service holati kameralar kartasida ko'rinadi: `processing`, `connecting`, `error`

## Arxitektura

```
IP Camera (RTSP)
      │
      ▼
AI Service (YOLOv8 + tracking)
      │ POST /analytics/events
      ▼
FastAPI Backend → PostgreSQL
      │ WebSocket
      ▼
React Dashboard (MUI + Redux)
```
