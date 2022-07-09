# import random
#
#
# import time
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

import heapq

m = [34, 94, 35, 78, 45, 67, 23, 90, 1, 0]
# 求一个list中最大的2个数，并排序（使用了堆排序算法）
max_number = heapq.nlargest(2, m)
# 最大的2个数对应的，如果用nsmallest则是求最小的数及其索引
max_index = map(m.index, heapq.nlargest(2, m))
print(list(max_index))
