import os
import MetaTrader5 as mt5
from dotenv import load_dotenv

load_dotenv()

def connect_mt5():
    if not mt5.initialize():
        print(f"Gagal inisialisasi MT5, error: {mt5.last_error()}")
        return False

    akun = int(os.getenv("MT5_ACCOUNT"))
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER")

    authorized = mt5.login(akun, password=password, server=server)
    
    if authorized:
        # print("Berhasil login ke MT5!")
        return True
    else:
        print(f"Gagal login ke akun MT5, error: {mt5.last_error()}")
        return False

def get_account_info():
    connect_mt5() 
    
    account = mt5.account_info()
    if account is not None:
        return f" 📊 **Info Akun Trading**\nSaldo: {account.balance} {account.currency}\nEquity: {account.equity}\nMargin: {account.margin}"
    
    error_code = mt5.last_error()
    return f"Gagal mendapatkan info akun. Kode Error MT5: {error_code}"

def open_trade(symbol, order_type, lot, sl=0.0, tp=0.0):
    connect_mt5()

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return f"Symbol {symbol} tidak ditemukan."

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            return f"Gagal memunculkan {symbol} di Market Watch."

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return f"Gagal mendapatkan harga untuk {symbol}."

    if order_type.lower() == 'buy':
        tipe_order = mt5.ORDER_TYPE_BUY
        price = tick.ask
    elif order_type.lower() == 'sell':
        tipe_order = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        return "Tipe order tidak valid."

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot),
        "type": tipe_order,
        "price": price,
        "sl": float(sl), 
        "tp": float(tp),
        "deviation": 20,
        "magic": 234000,
        "comment": "Order via Telegram Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return f"Order gagal! Kode error: {result.retcode} - {result.comment}"
    
    pesan = f"📊 **Order {order_type.upper()} Berhasil!**\nSymbol: {symbol}\nLot: {lot}\nHarga: {price}"
    if float(sl) > 0: pesan += f"\nSL: {sl}"
    if float(tp) > 0: pesan += f"\nTP: {tp}"
    
    return pesan

def get_open_positions():
    connect_mt5()
    
    positions = mt5.positions_get()
    
    if positions is None or len(positions) == 0:
        return "Belum ada posisi trading yg terbuka saat ini"
        
    result = "📊 **Daftar Posisi Aktif:**\n\n"
    
    for pos in positions:
        tipe = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
        profit = pos.profit
        
        icon = "🟢" if profit > 0 else "🔴"
        
        result += f"{icon} **{pos.symbol}** | {tipe} {pos.volume} Lot\n"
        result += f"   Tiket: `{pos.ticket}`\n"
        result += f"   Harga Buka: {pos.price_open}\n"
        result += f"   Harga Saat Ini: {pos.price_current}\n"
        result += f"   Profit: $ {profit}\n\n"
        
    return result

def close_trade(ticket):
    connect_mt5()
    
    try:
        tiket_int = int(ticket)
    except ValueError:
        return "Nomor tiket harus berupa angka"

    position = mt5.positions_get(ticket=tiket_int)
    
    if position is None or len(position) == 0:
        return f"Posisi dengan tiket {ticket} tidak ditemukan atau sudah ditutup."
        
    pos = position[0]
    symbol = pos.symbol
    lot = pos.volume
    tipe_awal = pos.type
    
    tick = mt5.symbol_info_tick(symbol)
    if tipe_awal == mt5.ORDER_TYPE_BUY:
        tipe_tutup = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        tipe_tutup = mt5.ORDER_TYPE_BUY
        price = tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": tipe_tutup,
        "position": pos.ticket,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Close via Telegram Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return f"Gagal menutup posisi! Kode error: {result.retcode} - {result.comment}"
        
    return f"📊 **Posisi DITUTUP!**\nTiket: {ticket}\nSymbol: {symbol}\nProfit/Loss Akhir: $ {pos.profit}"