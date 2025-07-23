import requests
import json
import asyncio
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


# === Tambahan Gemini ===
from google import genai


# API Key Gemini (amanin nanti ke .env ya)
GEMINI_API_KEY = "API KEY DARI GEMINI"
client = genai.Client(api_key=GEMINI_API_KEY)


# Konfigurasi
TELEGRAM_TOKEN = 'TOKEN DARI BOTFATHER'
CHAT_ID = CHATIDDARIAPITELEGRAM
CHECK_INTERVAL = 10  # detik
DATA_FILE = "alert_data.json"

# Inisialisasi data
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        SYMBOLS = json.load(f)
except FileNotFoundError:
    SYMBOLS = {
        "BTCUSDT": [119000],
        "ETHUSDT": [3400]
    }

ALERT_STATE = {}
for symbol, prices in SYMBOLS.items():
    ALERT_STATE[symbol] = {str(p): {"above": False, "below": False} for p in prices}
    
# Save data ke file
def save_symbols():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(SYMBOLS, f, indent=2)

# Log ke file dan terminal
def log_alert(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("alert_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")
    print(message)

# Ambil harga Binance
def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        res = requests.get(url, timeout=10)
        return float(res.json()['price'])
    except Exception as e:
        log_alert(f"Error fetching {symbol}: {e}")
        return None

# Cek harga & kirim alert
async def price_loop(bot):
    global ALERT_STATE
    while True:
        for symbol, thresholds in SYMBOLS.items():
            price = get_price(symbol)
            if price:
                for threshold in thresholds:
                    t = str(threshold)
                    log_alert(f"{symbol} = ${price} (cek threshold: ${threshold})")

                    # Naik
                    if price >= threshold and not ALERT_STATE[symbol][t]["above"]:
                        try:
                            await bot.send_message(chat_id=CHAT_ID, text=f"🚀 {symbol} naik di ${threshold}! Sekarang: ${price}")
                        except Exception as e:
                            log_alert(f"❌ Gagal kirim alert untuk {symbol} ${threshold}: {e}")
                        ALERT_STATE[symbol][t]["above"] = True
                        ALERT_STATE[symbol][t]["below"] = False

                    # Turun
                    elif price < threshold and not ALERT_STATE[symbol][t]["below"]:
                        try:
                            await bot.send_message(chat_id=CHAT_ID, text=f"🔻 {symbol} turun di bawah ${threshold}. Sekarang: ${price}")
                        except Exception as e:
                            log_alert(f"❌ Gagal kirim alert untuk {symbol} ${threshold}: {e}")
                        ALERT_STATE[symbol][t]["below"] = True
                        ALERT_STATE[symbol][t]["above"] = False

        await asyncio.sleep(CHECK_INTERVAL)

# ===== Handler Telegram Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Selamat datang! Gunakan /alert SYMBOL PRICE untuk mengatur alert.\nContoh: /alert BTCUSDT 120000\nAtau coba: /analisa coin yang bagus buat bulan ini")

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Format salah. Gunakan: /alert SYMBOL PRICE")
        return

    symbol = context.args[0].upper()
    try:
        price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Harga tidak valid.")
        return

    # Tambahkan ke list, bukan overwrite
    if symbol not in SYMBOLS:
        SYMBOLS[symbol] = []
        ALERT_STATE[symbol] = {}

    if price not in SYMBOLS[symbol]:
        SYMBOLS[symbol].append(price)
        ALERT_STATE[symbol][str(price)] = {"above": False, "below": False}
        save_symbols()
        await update.message.reply_text(f"✅ Alert untuk {symbol} ditambahkan di ${price}")
    else:
        await update.message.reply_text(f"⚠️ Alert untuk {symbol} di ${price} sudah ada.")

async def removealert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Format salah. Gunakan: /removealert SYMBOL PRICE")
        return

    symbol = context.args[0].upper()
    try:
        price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Harga tidak valid.")
        return

    if symbol in SYMBOLS and price in SYMBOLS[symbol]:
        SYMBOLS[symbol].remove(price)
        if str(price) in ALERT_STATE[symbol]:
            del ALERT_STATE[symbol][str(price)]
        # Jika list kosong, hapus symbol dari dict
        if not SYMBOLS[symbol]:
            del SYMBOLS[symbol]
            del ALERT_STATE[symbol]
        save_symbols()
        await update.message.reply_text(f"✅ Alert untuk {symbol} di ${price} berhasil dihapus.")
    else:
        await update.message.reply_text(f"⚠️ Alert untuk {symbol} di ${price} tidak ditemukan.")


# ===== Prompt Builder agar output Gemini tidak pakai format markdown lebay dan lebih tajam =====
def build_prompt(user_input: str, price: float = None) -> str:
    system_instruction = (
        "Berikan analisa harga crypto yang tajam, singkat, dan aktual. "
        "Sertakan prediksi arah harga berikutnya, level support dan resistance terkini, "
        "harga entry potensial (agresif & konservatif), take profit dan stop loss. "
        "Gunakan gaya bahasa seperti analis profesional Telegram."
    )

    today = datetime.now().strftime("%d %B %Y")
    price_info = f"Harga ETHUSDT saat ini adalah sekitar ${price:.2f}." if price else ""

    return (
        f"{system_instruction}\n\n"
        f"Tanggal hari ini: {today}\n"
        f"{price_info}\n"
        f"Pertanyaan pengguna: {user_input}"
    )



# ===== Analisa pakai Gemini =====
async def analisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🧠 Ketik pertanyaan setelah /analisa\nContoh: /analisa coin yang bagus minggu ini")
        return

    user_query = " ".join(context.args)
    final_prompt = build_prompt(user_query)
    await update.message.reply_text("⏳ Sedang menganalisis dengan Gemini...")

    max_retries = 3
    model_name = "gemini-2.5-pro"
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=final_prompt
            )
            await update.message.reply_text(response.text)
            return
        except Exception as e:
            err_msg = str(e)
            if ("503" in err_msg or "overload" in err_msg or "UNAVAILABLE" in err_msg) and attempt < max_retries:
                if model_name == "gemini-2.5-pro":
                    model_name = "gemini-2.5-flash"
                    await update.message.reply_text(f"⚠️ Model Gemini-2.5-Pro sedang sibuk, mencoba dengan Gemini-2.5-Flash...")
                else:
                    await update.message.reply_text(f"⚠️ Model Gemini-2.5-Flash juga sibuk (percobaan {attempt}/{max_retries}), mencoba lagi...")
                await asyncio.sleep(2 * attempt)
                continue
            await update.message.reply_text(f"⚠️ Gagal mendapatkan respon dari Gemini: {e}")
            return


# ===== Main Bot Init =====
# Callback setelah Application selesai inisialisasi
async def _post_init(app):
    # Mulai task price_loop di event loop yang sama
    app.create_task(price_loop(app.bot))


def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .post_init(_post_init)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("analisa", analisa))
    app.add_handler(CommandHandler("removealert", removealert))

    # Jalankan polling (sinkron, mengatur event loop-nya sendiri)
    app.run_polling()

if __name__ == "__main__":
    main()