from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from mt5_connector import connect_mt5, get_account_info
from mt5_connector import connect_mt5, get_account_info, open_trade

MY_CHAT_ID = '6998238268'

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
    
    # Cek apakah boss mengetik format dengan benar
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Format salah, Boss! Gunakan: /buy SYMBOL LOT\nContoh: /buy EURUSD 0.01")
        return
        
    symbol = context.args[0].upper()
    lot = context.args[1]
    
    await update.message.reply_text(f"⏳ Memproses perintah BUY {symbol} dengan lot {lot}...")
    
    # Panggil MT5
    hasil = open_trade(symbol, 'buy', lot)
    await update.message.reply_text(hasil)

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Format salah, Boss! Gunakan: /sell SYMBOL LOT\nContoh: /sell EURUSD 0.01")
        return
        
    symbol = context.args[0].upper()
    lot = context.args[1]
    
    await update.message.reply_text(f"⏳ Memproses perintah SELL {symbol} dengan lot {lot}...")
    
    # Panggil MT5
    hasil = open_trade(symbol, 'sell', lot)
    await update.message.reply_text(hasil)

if __name__ == '__main__':
    TOKEN = '8271622388:AAFmlE0Di_kcvVmlpzm_UPlRoVjcH9alH54'
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saldo", saldo))

    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("sell", sell_command))
    
    print("Bot sedang berjalan...")
    app.run_polling()