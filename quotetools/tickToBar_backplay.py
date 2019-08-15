#encoding:utf-8
import datetime
from function import generate_ohlc_key
import queue
from datetime import datetime
import time
import decimal
from vtObject import VtTickData

from myfunction import stringToDate


q_bar = queue.Queue()
q_depth_market_data = queue.Queue()

nest = dict()
int_instruments = ['rb', 'hc', 'ru', 'ni', 'cu']

def tickToBar(tick, granularity = 180):
    #tick data to bar
    # global bars
    instrument_id = tick.InstrumentID
    action_day = tick.ActionDay
    update_time = tick.UpdateTime.replace(':', '')
    # update_time = tick.UpdateTime
    # last_price = int(float(tick.LastPrice)) if instrument_id[0:2] in int_instruments else float(tick.LastPrice)
    last_price = float(tick.LastPrice) if instrument_id[0:2] in int_instruments else float(tick.LastPrice)
    # volume = int(float(tick.Volume))

    # if volume == 0:
    #     continue

    if update_time.find('.') != -1:
        dt = datetime.strptime(' '.join([action_day, update_time]), "%Y-%m-%d %H%M%S.%f")
        # dt = datetime.strptime(' '.join([action_day, update_time]), "%Y%m%d %H%M%S.%f")
        timestamp = time.mktime(dt.timetuple()) + (dt.microsecond / 1e6)

    else:
        timestamp = int(time.mktime(time.strptime(' '.join([action_day, update_time]), "%Y%m%d %H%M%S")))

    date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    ohlc_key = generate_ohlc_key(instrument_id=instrument_id, granularity=granularity, timestamp=timestamp)

    if ohlc_key not in nest:
        nest[ohlc_key] = {
            'date_time': date_time,
            'last_timestamp': timestamp,
            'high': last_price,
            'low': last_price,
            'close': last_price,
            'open': last_price
        }

    nest[ohlc_key]['last_timestamp'] = timestamp
    nest[ohlc_key]['date_time'] = date_time

    nest[ohlc_key]['close'] = last_price

    if last_price > nest[ohlc_key]['high']:
        nest[ohlc_key]['high'] = last_price

    elif last_price < nest[ohlc_key]['low']:
        nest[ohlc_key]['low'] = last_price

    if nest.__len__() > 1:
        for k, v in nest.items():
            if k == ohlc_key:
                continue
            q_bar.put(nest[k])
            del nest[k]

    print nest


bars = dict()

def tickDataReplay(tickfile):
    # tickfile 为tqsdk 下载的tick 文件格式

    with open(tickfile) as f:
        for i, line in enumerate(f):

            # 忽略 csv 头
            if i == 0:
                continue

            # date_time, tlastPrice, tbidPrice1, taskPrice1, tvolume, topenInt ,t1,t2, t3,t4,t5,t6,t7= line.split(',')

            row = line.split(',')
            if row[1] == 'nan':
                continue

            date_time = row[0]

            dt = stringToDate(date_time.split(' ')[1].split('.')[0]).time()

            # dt = stringToDate(row[0].split(' ')[1]).time()

            ddate = row[0].split()[0]
            dtime = row[0].split()[1][0:12]
            # dtime = row[0].split()[1][0:9]
            tick = VtTickData()

            tick.InstrumentID = 'rb1910'
            tick.ActionDay = ddate
            tick.UpdateTime = dtime
            tick.LastPrice = float(row[1])
            tick.Volume = int(float(row[6]))

            # print(tick)
            q_depth_market_data.put(tick)

            # if q_depth_market_data.qsize() > 1000:
            #     time.sleep(5)


if __name__ == "__main__":

    tickfile = '/home/tianhm/ctplrn/quotetools/data/rb2005_tickcleaned.csv'
    granularity = 300
    # tickDataReplay(tickfile)


    import threading
    play = threading.Thread(target=tickDataReplay, args=(tickfile,))
    play.start()

    # dingdang = threading.Thread(target=dingdangNo6())
    # dingdang.start()

    while True:

        if not q_depth_market_data.empty():
            tick = q_depth_market_data.get()

            tickToBar(tick, granularity)