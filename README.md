# Ufeek Alert Bot

Bot Telegram untuk alert harga crypto (BTC, ETH, dll) berbasis Python, dengan fitur analisa AI Gemini.

## Fitur

- Kirim alert otomatis ke Telegram jika harga crypto melewati batas tertentu (atas/bawah)
- Tambah/hapus alert harga dengan perintah Telegram
- Analisa harga crypto dengan AI Gemini langsung dari chat
- Log alert ke file

## Instalasi

1. **Clone repo & masuk folder**
   ```bash
   git clone <repo-anda>
   cd ufeekalertbot
   ```
2. **Install dependensi**
   ```bash
   pip install -r requirements.txt
   ```
   Jika belum ada, buat file `requirements.txt` dengan isi:
   ```
   python-telegram-bot
   requests
   google-generativeai
   ```
3. **Buat file `.env` (opsional, untuk keamanan API key)**
   Simpan token dan API key di file `.env` (atau langsung edit di `alertbot.py`):
   ```env
   TELEGRAM_TOKEN=isi_token_dari_botfather
   GEMINI_API_KEY=isi_api_key_gemini
   CHAT_ID=isi_chat_id_anda
   ```

## Konfigurasi Manual

Edit variabel berikut di `alertbot.py` jika tidak pakai `.env`:

- `TELEGRAM_TOKEN` → Token dari BotFather
- `GEMINI_API_KEY` → API key Gemini
- `CHAT_ID` → Chat ID Telegram Anda

## Menjalankan Bot

```bash
python alertbot.py
```

## Cara Pakai di Telegram

- `/start` — Info bantuan
- `/alert SYMBOL HARGA` — Tambah alert (contoh: `/alert BTCUSDT 120000`)
- `/removealert SYMBOL HARGA` — Hapus alert (contoh: `/removealert BTCUSDT 120000`)
- `/analisa pertanyaan` — Analisa AI Gemini (contoh: `/analisa coin yang bagus minggu ini`)

## Catatan

- Data alert tersimpan di `alert_data.json`
- Log alert ada di `alert_log.txt`
- Bot akan cek harga tiap 10 detik (bisa diubah di variabel `CHECK_INTERVAL`)

## Lisensi

MIT
