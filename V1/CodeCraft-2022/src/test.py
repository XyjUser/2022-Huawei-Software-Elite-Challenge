import random
import time


class stream:
    def __init__(self, client_id, stream_name, vol, timeindex):
        self.client_id, self.stream_name, self.vol, self.timeindex = client_id, stream_name, vol, timeindex


def sort_stream(demand):
    streams = [None for _ in range(len(demand) * len(demand[0]))]
    index = 0
    for client in range(len(demand)):
        sts = demand[client]
        for st in range(len(sts)):
            if sts[st] > 0:
                streams[index]= stream(client, st, sts[st], 1)
                index += 1
    streams = sorted(streams[:index], key=lambda k: k.vol, reverse=True)
    for s in streams:
        client = s.client_id
        stream_name = s.stream_name
        vol = s.vol


def merge_streams(demand):
    """
    将一个时刻所有的stream整合到一起，每一个stream名字变为 client_stream
    Args:
        demand: 一个时刻的所有流信息
    Returns:
        streams_names:流的名字
        streams : 整合好的流
    """
    streams = {}
    for client in range(len(demand)):
        sts = demand[client]
        for st in range(len(sts)):
            if sts[st] > 0:
                streams[client * 100 + st] = sts[st]
    streams_names = sorted(list(streams.keys()), key=lambda k: streams[k], reverse=True)
    for stream_name in streams_names:
        client = stream_name // 100
        stream = stream_name - client * 100
    # return streams_names, streams
def tuple_list(demand):
    index = 0
    streams = [None for _ in range(len(demand) * len(demand[0]))]
    for client in range(len(demand)):
        sts = demand[client]
        for st in range(len(sts)):
            if sts[st] > 0:
                streams[index] = (client, st, sts[st])
                index += 1

    streams = sorted(streams[:index], key=lambda k: k[2], reverse=True)
    for s in streams:
        client = s[0]
        stream = s[1]

demand = [[1000 for _ in range(35)] for _ in range(100)]
start = time.time()
tuple_list(demand)
time1 = time.time()
sort_stream(demand)
time2 = time.time()
merge_streams(demand)
time3 = time.time()
print(f"tuple用时:{time1 - start}  class用时:{time2 - time1} num用时:{time3 - time2}")