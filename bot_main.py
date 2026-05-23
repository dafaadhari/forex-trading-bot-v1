from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from mt5_connector import connect_mt5, get_account_info

# Inisialisasi MT5
if connect_mt5():
    print("Berhasil terkoneksi ke MT5")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Halo Boss! Bot sudah online dan siap melayani.')

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = get_account_info()
    await update.message.reply_text(info)

if __name__ == '__main__':
    TOKEN = '8271622388:AAFmlE0Di_kcvVmlpzm_UPlRoVjcH9alH54'
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saldo", saldo)) # Perintah baru
    
    print("Bot sedang berjalan...")
    app.run_polling()