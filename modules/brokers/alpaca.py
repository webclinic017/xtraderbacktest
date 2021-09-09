import datetime
import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))

import requests
import modules.other.sys_conf_loader as sys_conf_loader
import json
import logging 
import pandas as pd
import dateutil
import alpaca_trade_api as alpaca_trade_api
import threading
import time
import threading
import asyncio



sys_conf = sys_conf_loader.get_sys_conf()
alpaca_conf = sys_conf["live_conf"]["alpaca"]
KEY_ID = alpaca_conf["APCA-API-KEY-ID"]
KEY_SECRET = alpaca_conf["APCA-API-SECRET-KEY"]
BASE_URL = alpaca_conf["URL"]
DATA_URL = alpaca_conf["DATA_URL"]

HEADERS  = {
    "APCA-API-KEY-ID":KEY_ID,
    "APCA-API-SECRET-KEY":KEY_SECRET
}


stream = alpaca_trade_api.stream.Stream(KEY_ID,KEY_SECRET,base_url=BASE_URL,data_feed='sip', raw_data=True)

def account():
    result = None
    url = BASE_URL + '/v2/account' 
    params = {
    }
    response = requests.get(url, data = json.dumps(params), headers = HEADERS)
    if response.status_code == 200:
        result = response.json()
    else:
        logging.error("Error at " + url + " params " + json.dumps(params) + " headers " + json.dumps(HEADERS))
        logging.error(response.status_code)
        logging.error(response.text)
    return result

def _timeframe_convert(timeframe):
    if 'm' in  timeframe:
        if int(timeframe.split('m')[0]) < 60:
            return timeframe.split('m')[0] + "Min"
        elif timeframe.split('m')[0] == '60':
            return "1Hour"
    if 'd' in  timeframe:
        return timeframe.split('d')[0] + "Day"

def stocks_bars(symbol,timeframe,start,end):
    result = None
    url = DATA_URL + '/v2/stocks/'+symbol+'/bars' 
    start_iso = datetime.datetime.strptime(start,"%Y-%m-%d %H:%M:%S").astimezone(dateutil.tz.gettz('US/Eastern')).isoformat()
    end_iso = datetime.datetime.strptime(end,"%Y-%m-%d %H:%M:%S").astimezone(dateutil.tz.gettz('US/Eastern')).isoformat()
    params = {
        "start":start_iso,
        "end":end_iso,
        "limit":10000,
        "timeframe":_timeframe_convert(timeframe),
        'adjustment':'raw',
        'page_token':None
    }
    response = requests.get(url, params = params, headers = HEADERS)
    if response.status_code == 200:
        result = response.json()['bars']
        result = pd.DataFrame(result)
        result = result.rename(columns={"t": "date","o": "open", "h": "high", "l": "low", "c": "close", "v": "volume","vw":"vwap",'n':"unknown_n"})
        result = result.drop(columns=["vwap","unknown_n"])
        result["date"] = pd.to_datetime(result["date"],utc=True).dt.tz_convert('US/Eastern')
        result["date"] = pd.to_datetime(result["date"].dt.strftime('%Y-%m-%d %H:%M:%S'))
        result["open_interest"] = 0
        final_result =  pd.DataFrame()
        final_result["date"] = result["date"]
        final_result["open"] = result["open"]
        final_result["high"] = result["high"]
        final_result["low"] = result["low"]
        final_result["close"] = result["close"]
        final_result["symbol"] =  symbol
        final_result["volume"] = result["volume"]
        final_result["open_interest"] = result["open_interest"]
        final_result = final_result.set_index("date")
        result = final_result.copy(deep = True)
    else:
        logging.error("Error at " + url + " params " + json.dumps(params) + " headers " + json.dumps(HEADERS))
        logging.error(response.status_code)
        logging.error(response.text)
    return result



def _stream_thread():
    try:
        # make sure we have an event loop, if not create a new one
        loop = asyncio.get_event_loop()
        loop.set_debug(True)
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    print("Stream thread start")
    stream.run()
threading.Thread(target=_stream_thread).start()

def subscribe(symbols,quote_call_back,trade_call_back,trade_update_call_back):
    for symbol in symbols:
        stream.subscribe_quotes(quote_call_back, symbol)
        stream.subscribe_trades(trade_call_back, symbol)
    stream.subscribe_trade_updates(trade_update_call_back)
    
    # stream_thread = threading.Thread(target = stream.run)
    # stream_thread.start()
    print("Finish Subscribes.")

def get_orders(symbols=None):
    result = None
    url = BASE_URL + '/v2/orders' 
    params = {
        "status":'open',
        'limit':'500',
    }
    if symbols is not None:
        symbols_params = ''
        for symbol in symbols:
            symbols_params = symbols_params + symbol + ','
        symbols_params = symbols_params[0:-1]
        params.update({'symbols':symbols_params})
    response = requests.get(url, params = params, headers = HEADERS)
    if response.status_code == 200:
        result = response.json()
    else:
        logging.error("Error at " + url + " params " + json.dumps(params) + " headers " + json.dumps(HEADERS))
        logging.error(response.status_code)
        logging.error(response.text)
    return result

def _convert_direction_to_side(direction):
    if direction == "long":
        return "buy"
    elif direction == "short":
        return "sell"
'''
order = {
    "order_ref":order_ref,
    "symbol":symbol,
    "order_type":order_type,                            # "market","limit","stop"
    "volume":volume,
    "filled":0,
    "direction":direction,
    "limit_price":limit_price,
    "tp":tp,
    "sl":sl,
    "mutiple_exits":mutiple_exits,
    "trailing_sl":trailing_sl,
    "extra":extra,
    "create_date":self.current_time,
    "open_date":None,
    "close_date":None,
    "expiration":expiration,
    "status":"pending_open",                            # "pending_open","sending_open","opening","open_filled","sending_close","closing","close_filled","delete"
    "open_price":0,
    "open_filled_price":0,
    "close_price":0,
    "close_filled_price":0,
    "commission":0,
    "margin":0,
    "profit":0,
    "swap":0
}
'''
def new_order(order,limit_price):
    result = None
    url = BASE_URL + '/v2/orders' 
    params = {
        "symbol":order["symbol"],
        "qty":order["volume"],
        "side":_convert_direction_to_side(order["direction"]),
        "type":"limit",
        "time_in_force":"day",
        "extended_hours":True,
        "client_order_id":order["order_ref"],
        "order_class":"simple",
        "limit_price":limit_price,
        "take_profit":{
           "limit_price": float(order["tp"])
        },
        "stop_loss": {
            "stop_price": float(order["sl"]), "limit_price": float(order["tp"])
        }
        
    }
    response = requests.post(url, json = params, headers = HEADERS)
    if response.status_code == 200:
        result = response.json()
    else:
        logging.error("Error at " + url + " params " + json.dumps(params) + " headers " + json.dumps(HEADERS))
        logging.error(response.status_code)
        logging.error(response.text)
    return result

if __name__ == "__main__":
    print("Start testing.")
    #print(account()) # pass
    #print(stocks_bars("AAPL","1m","2021-09-08 09:30:00","2021-09-08 10:00:00"))
    print("Testing subscribe.")
    async def quote_call_back(q):
        print('quote', q,flush=True)
        symbol = q["S"]
        ask_exchange_code = q["ax"]
        ask_price = q["ap"]
        ask_size = q["as"]
        bid_exchange_code = q["bx"]
        bid_price = q["bp"]
        bid_size = q["bs"]
        date = q["t"].to_datetime().astimezone(dateutil.tz.gettz('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S") 
       
        print(date, flush=True)
        pass
    async def trade_call_back(q):
        # print('trade', q,flush=True)
        pass
    async def trade_update_call_back(q):
        print('trade_update', q,flush=True)
        pass
    #subscribe(["AAPL"],quote_call_back,trade_call_back,trade_update_call_back) # pass
    
    #time.sleep(10)
    #print("Testing open order.")
    order = {
        "order_ref":"test_order",
        "symbol":"AAPL",
        "volume":1,
        "direction":"long",
        "tp":180,
        "sl":120
    }
    print(new_order(order,154))

    print("Testing get orders.")
    print(get_orders(["AAPL","IBM"]))
    pass