class Heap:
    def __init__(self):
        self.arr = [0]
        self.heap_size = 0

    def put(self, val):
        self.arr.append(val)
        self.heap_size += 1
        now = self.heap_size
        while now > 1:
            parent = now >> 1
            if self.arr[now] < self.arr[parent]:
                break
            self.arr[now], self.arr[parent] = self.arr[parent], self.arr[now]
            now = parent

    def get(self):
        res = self.arr[1]
        self.arr[1] = self.arr[self.heap_size]
        self.arr = self.arr[:-1]
        self.heap_size -= 1
        pa = 1
        while 2 * pa <= self.heap_size:
            son = pa * 2
            if son < self.heap_size and self.arr[son] < self.arr[son + 1]:
                son += 1
            if self.arr[pa] >= self.arr[son]:
                break
            self.arr[pa], self.arr[son] = self.arr[son], self.arr[pa]
            pa = son
        return res

    def is_empty(self):
        return self.heap_size == 0

    def clear(self):
        self.arr = [0]
        self.heap_size = 0

if __name__ == '__main__':
    h = Heap()
    arr = [1,5,4,8,6,9,7,5]
    for i in arr:
        h.put(i)
    print(h.arr)
    h.get()
    print(h.arr)
    h.get()
    print(h.arr)