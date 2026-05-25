import MetaTrader5 as mt5

def connect_mt5():
    if not mt5.initialize():
        print(f"Gagal inisialisasi MT5, error: {mt5.last_error()}")
        return False

    akun = 107472181 
    password = "Q-Bz4uHf" 
    server = "MetaQuotes-Demo"

    authorized = mt5.login(akun, password=password, server=server)
    
    if authorized:
        print("Berhasil login ke MT5!")
        return True
    else:
        print(f"Gagal login ke akun MT5, error: {mt5.last_error()}")
        return False

def get_account_info():
    connect_mt5() 
    
    account = mt5.account_info()
    if account is not None:
        return f"**Info Akun Trading**\nSaldo: {account.balance} {account.currency}\nEquity: {account.equity}\nMargin: {account.margin}"
    
    error_code = mt5.last_error()
    return f"Gagal mendapatkan info akun. Kode Error MT5: {error_code}"

def open_trade(symbol, order_type, lot):
    # Pastikan koneksi fresh
    connect_mt5()

    # Cek apakah symbol (mata uang) tersedia
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return f"❌ Symbol {symbol} tidak ditemukan."

    # Pastikan mata uang terlihat di Market Watch
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            return f"❌ Gagal memunculkan {symbol} di Market Watch."

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return f"❌ Gagal mendapatkan harga untuk {symbol}."

    if order_type.lower() == 'buy':
        tipe_order = mt5.ORDER_TYPE_BUY
        price = tick.ask
    elif order_type.lower() == 'sell':
        tipe_order = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        return "❌ Tipe order tidak valid."

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot),
        "type": tipe_order,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Order via Telegram Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return f"❌ Order gagal! Kode error: {result.retcode} - {result.comment}"
    
    return f"✅ **Order {order_type.upper()} Berhasil!**\nSymbol: {symbol}\nLot: {lot}\nHarga: {price}"