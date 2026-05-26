import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from mt5_connector import connect_mt5, get_account_info, open_trade, get_open_positions, close_trade

load_dotenv()

MY_CHAT_ID = os.getenv("MY_CHAT_ID")

async def check_access(update: Update):
    if str(update.effective_chat.id) != MY_CHAT_ID:
        await update.message.reply_text("Akses ditolak! Anda bukan pemilik bot.")
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
        await update.message.reply_text("⚠️ Format salah \nGunakan: /buy SYMBOL LOT [SL] [TP]\nContoh: /buy EURUSD 0.10 1.16000 1.17000")
        return
        
    symbol = context.args[0].upper()
    lot = context.args[1]
    
    sl = context.args[2] if len(context.args) > 2 else 0.0
    tp = context.args[3] if len(context.args) > 3 else 0.0
    
    pesan_proses = f"Memproses BUY {symbol} | Lot: {lot}"
    if float(sl) > 0: pesan_proses += f" | SL: {sl}"
    if float(tp) > 0: pesan_proses += f" | TP: {tp}"
    await update.message.reply_text(pesan_proses)
    
    hasil = open_trade(symbol, 'buy', lot, sl, tp)
    await update.message.reply_text(hasil)

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    
    if len(context.args) < 2:
        await update.message.reply_text("Format salah \nGunakan: /sell SYMBOL LOT [SL] [TP]\nContoh: /sell EURUSD 0.10 1.17000 1.16000")
        return
        
    symbol = context.args[0].upper()
    lot = context.args[1]
    
    sl = context.args[2] if len(context.args) > 2 else 0.0
    tp = context.args[3] if len(context.args) > 3 else 0.0
    
    pesan_proses = f"Memproses SELL {symbol} | Lot: {lot}"
    if float(sl) > 0: pesan_proses += f" | SL: {sl}"
    if float(tp) > 0: pesan_proses += f" | TP: {tp}"
    await update.message.reply_text(pesan_proses)
    
    hasil = open_trade(symbol, 'sell', lot, sl, tp)
    await update.message.reply_text(hasil)
    if not await check_access(update): return
    
    if len(context.args) < 2:
        await update.message.reply_text("Format salah, Gunakan: /sell SYMBOL LOT\nContoh: /sell EURUSD 0.01")
        return
        
    symbol = context.args[0].upper()
    lot = context.args[1]
    
    await update.message.reply_text(f"Memproses perintah SELL {symbol} dengan lot {lot}...")
    
    hasil = open_trade(symbol, 'sell', lot)
    await update.message.reply_text(hasil)

async def posisi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    
    await update.message.reply_text("Memindai market...")
    hasil = get_open_positions()
    await update.message.reply_text(hasil)

async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    
    if len(context.args) < 1:
        await update.message.reply_text("Format salah, Gunakan: /close NOMOR_TIKET\nContoh: /close 8775145889")
        return
        
    ticket = context.args[0]
    await update.message.reply_text(f"Memproses penutupan tiket {ticket}...")
    
    hasil = close_trade(ticket)
    await update.message.reply_text(hasil)

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("sell", sell_command))
    app.add_handler(CommandHandler("posisi", posisi_command))
    app.add_handler(CommandHandler("close", close_command))
    
    print("Bot sedang berjalan...")
    app.run_polling()