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

def run_auto_strategy(symbol, lot):
    connect_mt5()
    
    # 1. GEMBOK PENGAMAN POSISI AKTIF DIMATIKAN!
    # pos = mt5.positions_get(symbol=symbol)
    # if pos is not None and len(pos) > 0:
    #     return None
        
    # 2. Ambil data 2 candle terakhir saja
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 2)
    if rates is None or len(rates) < 2: 
        print(f"❌ [DEBUG] Gagal ambil data candle! Simbol '{symbol}' mungkin salah atau tidak aktif.")
        return None
        
    import pandas as pd
    df = pd.DataFrame(rates)
    
    # Ambil Candle terakhir yang baru saja ditutup
    c2 = df.iloc[-2] 
    
    c2_hijau = c2['close'] > c2['open']
    c2_merah = c2['close'] < c2['open']

    info = mt5.symbol_info(symbol)
    if info is None: return None
    jarak_sl = 300 * info.point
    jarak_tp = 600 * info.point
    
    tick = mt5.symbol_info_tick(symbol)
    
    # --- 3. EKSEKUSI MODE BRUTAL: 3 POSISI SEKALIGUS ---
    if c2_hijau:
        sl = tick.ask - jarak_sl
        tp = tick.ask + jarak_tp
        
        laporan = []
        for i in range(3):
            hasil = open_trade(symbol, "buy", lot, sl, tp)
            laporan.append(f"Peluru {i+1}: {hasil}")
            
        pesan_gabungan = "\n\n".join(laporan)
        return f"🚀 **[MODE BRUTAL] Candle Hijau -> BUY {symbol} 3X SEKALIGUS!**\n{pesan_gabungan}"
        
    elif c2_merah:
        sl = tick.bid + jarak_sl
        tp = tick.bid - jarak_tp
        
        laporan = []
        for i in range(3):
            hasil = open_trade(symbol, "sell", lot, sl, tp)
            laporan.append(f"Peluru {i+1}: {hasil}")
            
        pesan_gabungan = "\n\n".join(laporan)
        return f"📉 **[MODE BRUTAL] Candle Merah -> SELL {symbol} 3X SEKALIGUS!**\n{pesan_gabungan}"
            
    return None

# --- FUNGSI BARU: TRAILING STOP / BREAK EVEN ---
def geser_sl_saat_profit(symbol):
    """
    Fungsi ini akan mengecek: jika profit sudah mencapai 30 pips (setengah dari SL),
    maka SL akan digeser ke harga Open + 10 pips (Break Even), agar terhindar dari kerugian.
    """
    connect_mt5()
    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        return None
        
    info = mt5.symbol_info(symbol)
    target_profit_pips = 300 * info.point  # 30 Pips
    kunci_profit = 100 * info.point        # 10 Pip untuk diamankan
    
    pesan_notif = []
    
    for pos in positions:
        tick = mt5.symbol_info_tick(symbol)
        
        # Logika untuk posisi BUY
        if pos.type == mt5.POSITION_TYPE_BUY:
            if (tick.bid - pos.price_open) >= target_profit_pips:
                sl_baru = pos.price_open + kunci_profit
                if pos.sl < sl_baru:  # Hanya geser jika SL belum diamankan
                    request = {"action": mt5.TRADE_ACTION_SLTP, "position": pos.ticket, "sl": sl_baru, "tp": pos.tp}
                    if mt5.order_send(request).retcode == mt5.TRADE_RETCODE_DONE:
                        pesan_notif.append(f"🛡️ **[KEAMANAN]** SL Buy #{pos.ticket} digeser ke profit (Break Even)!")
                        
        # Logika untuk posisi SELL
        elif pos.type == mt5.POSITION_TYPE_SELL:
            if (pos.price_open - tick.ask) >= target_profit_pips:
                sl_baru = pos.price_open - kunci_profit
                if pos.sl > sl_baru or pos.sl == 0.0: # Hanya geser jika SL belum diamankan
                    request = {"action": mt5.TRADE_ACTION_SLTP, "position": pos.ticket, "sl": sl_baru, "tp": pos.tp}
                    if mt5.order_send(request).retcode == mt5.TRADE_RETCODE_DONE:
                        pesan_notif.append(f"🛡️ **[KEAMANAN]** SL Sell #{pos.ticket} digeser ke profit (Break Even)!")
                        
    return "\n".join(pesan_notif) if pesan_notif else None