import MetaTrader5 as mt5

def connect_mt5():
    if not mt5.initialize():
        print(f"Gagal inisialisasi MT5, error: {mt5.last_error()}")
        return False
    return True

def get_account_info():
    account = mt5.account_info()
    if account is not None:
        return f"📊 **Info Akun Trading**\nSaldo: {account.balance} {account.currency}\nEquity: {account.equity}\nMargin: {account.margin}"
    return "❌ Gagal mendapatkan info akun. Pastikan MT5 sedang login."