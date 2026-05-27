import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from datetime import datetime
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from mt5_connector import connect_mt5, get_account_info, open_trade, get_open_positions, close_trade, run_auto_strategy, geser_sl_saat_profit

# Buka brankas .env
load_dotenv()

# Tarik Chat ID dari .env
MY_CHAT_ID = os.getenv("MY_CHAT_ID")

async def check_access(update: Update):
    if str(update.effective_chat.id) != MY_CHAT_ID:
        await update.message.reply_text("❌ Akses ditolak! Anda bukan pemilik bot.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_access(update):
        await update.message.reply_text('Halo Boss! Bot sudah online dan siap melayani.')

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_access(update):
        info = get_account_info()
        await update.message.reply_text(info)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Format salah, Boss! Gunakan: /buy SYMBOL LOT [SL] [TP]\nContoh: /buy EURUSD 0.10 1.15000 1.18000")
        return
        
    symbol = context.args[0].upper()
    lot = context.args[1]
    sl = context.args[2] if len(context.args) > 2 else 0.0
    tp = context.args[3] if len(context.args) > 3 else 0.0
    
    pesan_proses = f"⏳ Memproses BUY {symbol} | Lot: {lot}"
    if float(sl) > 0: pesan_proses += f" | SL: {sl}"
    if float(tp) > 0: pesan_proses += f" | TP: {tp}"
    await update.message.reply_text(pesan_proses)
    
    hasil = open_trade(symbol, 'buy', lot, sl, tp)
    await update.message.reply_text(hasil)

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Format salah, Boss! Gunakan: /sell SYMBOL LOT [SL] [TP]\nContoh: /sell EURUSD 0.10 1.18000 1.15000")
        return
        
    symbol = context.args[0].upper()
    lot = context.args[1]
    sl = context.args[2] if len(context.args) > 2 else 0.0
    tp = context.args[3] if len(context.args) > 3 else 0.0
    
    pesan_proses = f"⏳ Memproses SELL {symbol} | Lot: {lot}"
    if float(sl) > 0: pesan_proses += f" | SL: {sl}"
    if float(tp) > 0: pesan_proses += f" | TP: {tp}"
    await update.message.reply_text(pesan_proses)
    
    hasil = open_trade(symbol, 'sell', lot, sl, tp)
    await update.message.reply_text(hasil)

async def posisi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    
    await update.message.reply_text("⏳ Memindai radar pasar...")
    hasil = get_open_positions()
    await update.message.reply_text(hasil)

async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Format salah, Boss! Gunakan: /close NOMOR_TIKET\nContoh: /close 8775145889")
        return
        
    ticket = context.args[0]
    await update.message.reply_text(f"⏳ Memproses penutupan tiket {ticket}...")
    
    hasil = close_trade(ticket)
    await update.message.reply_text(hasil)

# --- MESIN AUTO-TRADE DITAMBAHKAN DI SINI ---
async def auto_trading_loop(app):
    print("🧠 Otak analisa & Pengaman Profit mulai memantau pasar...")
    symbol = "XAUUSD.vxc"  
    lot = "0.01" # <--- Lot diubah menjadi 0.01
    
    while True:
        try:
            # 1. Cek apakah ada posisi yang perlu digeser SL-nya (Trailing Stop)
            hasil_geser = geser_sl_saat_profit(symbol)
            if hasil_geser is not None:
                await app.bot.send_message(chat_id=MY_CHAT_ID, text=hasil_geser)
                print(f"\n{hasil_geser}\n")

            # 2. Cek apakah ada sinyal baru untuk eksekusi
            hasil_auto = run_auto_strategy(symbol, lot)
            if hasil_auto is not None:
                await app.bot.send_message(chat_id=MY_CHAT_ID, text=hasil_auto)
                print(f"\n[EKSEKUSI] {hasil_auto}\n")
            else:
                waktu = datetime.now().strftime("%H:%M:%S")
                print(f"[{waktu}] Radar {symbol} M1 aktif... Menunggu candle berikutnya tutup.")
                
        except Exception as e:
            print(f"Error pada mesin auto-trade: {e}")
            
        await asyncio.sleep(60)

async def post_init(application):
    asyncio.create_task(auto_trading_loop(application))

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    # PERHATIKAN BARIS INI: parameter .post_init(post_init) mengikat loop ke jalannya bot
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("sell", sell_command))
    app.add_handler(CommandHandler("posisi", posisi_command))
    app.add_handler(CommandHandler("close", close_command))
    
    print("Bot sedang berjalan...")
    app.run_polling()