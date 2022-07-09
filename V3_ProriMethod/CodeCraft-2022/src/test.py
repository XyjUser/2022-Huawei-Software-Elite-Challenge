# import random
#
#
import time
# #
# #
# class Stream:
#     def __init__(self, client_id, stream_name, vol, timeindex):
#         self.client_id, self.stream_name, self.vol, self.timeindex = client_id, stream_name, vol, timeindex
#
#     def __str__(self):
#         return self.stream_name, self.vol
#
#
#
# client_num = 35
# stream_num = 100
#
# arr = []
# for i in range(client_num):
#     for j in range(stream_num):
#         arr.append(Stream(random.randint(0, 34), random.randint(0, 99), random.randint(0, 99), 0))
# start = time.time()
# for i in range(0,9000):
#     arr = [a for a in arr if a.stream_name > -1]
#     arr = sorted(arr, key=lambda k: (k.stream_name, k.vol), reverse=True)
#     arr = sorted(arr, key=lambda k: k.client_id)
#
# print(time.time() - start )
