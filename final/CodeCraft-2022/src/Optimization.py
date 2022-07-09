#!/usr/bin/env python
# -*- coding:utf-8 -*-
from baseline import BaseLine

class Opt(BaseLine):
    def __init__(self):
        super(Opt, self).__init__()
        self.center_score_time = [0 for _ in range(self.time_num)]
        self.site_total_vol = self.site_used_vol_list
        self.site_vol_index = [[i for i in range(self.time_num)] for _ in self.site_keys]
        self.center_score_index = []

    def opt_init(self):
        for site in self.site_keys:
            self.site_vol_index[site] = sorted(range(self.time_num), key=lambda k: self.site_total_vol[k][site])
        self.init_center_score()
        self.center_cost_pos = self.center_score_index[self.object_position]

    def init_center_score(self):
        for site in self.site_keys:
            for time_index in range(self.time_num):
                self.center_score_time[time_index] += sum(self.each_site_max_stream[time_index][site])
        self.center_score_index = sorted(range(self.time_num), key=lambda k: self.center_score_time[k])

    def update_stream_cache(self, site, time_index, last_vol):
        """
        更新一个流后，更新对节点的缓存有影响的时刻
        """
        new_vol = self.site_used_vol_list[time_index][site]
        add_cache = int(new_vol * 0.05) - int(last_vol * 0.05)
        time_index += 1
        while time_index < self.time_num and add_cache != 0:
            last_vol = self.site_used_vol_list[time_index][site]
            self.site_used_vol_list[time_index][site] += add_cache
            add_cache = int(self.site_used_vol_list[time_index][site] * 0.05) - int(last_vol * 0.05)
            time_index += 1

    def is_add_legal(self, vol, site, time_index):
        """
        当前节点增加流是否合法
        """
        while time_index < self.time_num and vol > 0:
            if self.site_total_vol[time_index][site] + vol > self.site_bandwidth[site]:
                return False
            last_cache = int(self.site_total_vol[time_index][site] * 0.05)
            new_cache = int((self.site_total_vol[time_index][site] + vol) * 0.05)

            vol = new_cache - last_cache
            time_index += 1
        return True

    def find_max_2nd_stream(self, time_index, site, stream):
        max_stream = 0
        second_stream = 0
        for st in self.client_demands[time_index]:
            if st.site == site and st.stream == stream:
                if st.vol > max_stream:
                    second_stream = max_stream
                    max_stream = st.vol
        return max_stream, second_stream

    def move_stream(self, st, from_site, to_site, time_index):

        st.site = to_site
        stream_vol = st.vol

        last_vol = self.site_used_vol_list[time_index][from_site]
        self.site_used_vol_list[time_index][from_site] -= stream_vol
        self.update_stream_cache(from_site, time_index, last_vol)

        last_vol = self.site_used_vol_list[time_index][to_site]
        self.site_used_vol_list[time_index][to_site] += stream_vol
        self.update_stream_cache(to_site, time_index, last_vol)

        if self.each_site_max_stream[time_index][from_site][st.stream] == stream_vol:
            s_vol, nd_vol = self.find_max_2nd_stream(time_index, from_site, st.stream)
            self.each_site_max_stream[time_index][from_site][st.stream] = s_vol
            self.each_site_2nd_stream[time_index][from_site][st.stream] = nd_vol
            self.center_score_time[time_index] -= stream_vol - s_vol
        else:
            if self.each_site_2nd_stream[time_index][from_site][st.stream] == stream_vol:
                s_vol, nd_vol = self.find_max_2nd_stream(time_index, from_site, st.stream)
                self.each_site_max_stream[time_index][from_site][st.stream] = s_vol
                self.each_site_2nd_stream[time_index][from_site][st.stream] = nd_vol

        if self.each_site_max_stream[time_index][to_site][st.stream] <= stream_vol:
            self.center_score_time[time_index] += stream_vol - self.each_site_max_stream[time_index][to_site][st.stream]
            self.each_site_2nd_stream[time_index][to_site][st.stream] = self.each_site_max_stream[time_index][to_site][
                st.stream]
            self.each_site_max_stream[time_index][to_site][st.stream] = stream_vol
        else:
            if self.each_site_2nd_stream[time_index][to_site][st.stream] < st.vol:
                self.each_site_2nd_stream[time_index][to_site][st.stream] = st.vol

        self.sort_site_index(to_site)
        self.sort_site_index(from_site)
        self.sort_center_index()

    def sort_site_index(self, site):
        self.site_vol_index[site] = sorted(range(self.time_num), key=lambda k: self.site_total_vol[k][site])

    def sort_center_index(self):
        self.center_score_index = sorted(range(self.time_num), key=lambda k: self.center_score_time[k])
        self.center_cost_pos = self.center_score_index[self.object_position]

    def get_available_site(self, st, time_index):
        sites = self.get_leisure_site(st.client)
        for site in sites:
            if st.site == site:
                continue
            if not self.is_add_legal(st.vol, site, time_index):
                continue
            change_vol_center = self.center_change_vol(st.site, site, st, time_index) * self.center_cost
            change_vol_site = self.site_change_vol(st.site, site, st, time_index)
            change_vol = change_vol_center + change_vol_site
            if change_vol <= 0:
                return True, site
        return False, None

    def site_change_vol(self, site_from, site_to, st, time_index):
        change_vol_from = 0
        last_vol = self.cal_score(site_from, self.site_total_vol[time_index][site_from])
        site_from_time_95 = self.site_vol_index[site_from][self.object_position]
        site_from_vol_95 = self.cal_score(site_from, self.site_total_vol[site_from_time_95][site_from])
        if time_index < site_from_time_95:
            change_vol_from = - int(st.vol * (0.05 ** (site_from_time_95 - time_index)))
        if last_vol >= site_from_vol_95:
            new_vol = self.cal_score(site_from, self.site_total_vol[time_index][site_from] - st.vol)
            if new_vol < site_from_vol_95:
                time94 = self.site_vol_index[site_from][self.object_position - 1]
                vol_94 = self.cal_score(site_from, self.site_total_vol[time94][site_from])
                change_vol_from += max(new_vol, vol_94) - last_vol
        new_vol = self.cal_score(site_to, self.site_total_vol[time_index][site_to] + st.vol)
        last_vol = self.cal_score(site_to, self.site_total_vol[time_index][site_to])
        time95 = self.site_vol_index[site_to][self.object_position]
        time96 = self.site_vol_index[site_to][self.object_position + 1]
        vol_96 = self.cal_score(site_to, self.site_total_vol[time96][site_to])
        if time95 == time_index:
            change_vol_to = min(vol_96, new_vol) - last_vol
        else:
            vol_95 = self.cal_score(site_to, self.site_total_vol[time95][site_to])
            if vol_95 >= new_vol:
                change_vol_to = 0
            else:
                change_vol_to = min(vol_96, new_vol) - last_vol
        if time95 > time_index:
            change_vol_to += int(st.vol * (0.05 ** (time95 - time_index)))
        return change_vol_from + change_vol_to

    def center_change_vol(self, site_from, site_to, st, time_index):
        """
        移动该流对中心成本的变化，降低了多少分
        """
        change_vol = 0
        if st.vol == self.each_site_max_stream[time_index][site_from][st.stream]:
            change_vol += self.each_site_2nd_stream[time_index][site_from][st.stream] - st.vol
        if st.vol > self.each_site_max_stream[time_index][site_to][st.stream]:
            change_vol += st.vol - self.each_site_max_stream[time_index][site_to][st.stream]
        vol_new = self.center_score_time[time_index] + change_vol
        vol_95 = self.center_score_time[self.center_cost_pos]
        vol_94 = self.center_score_time[self.center_score_index[self.object_position - 1]]
        vol_96 = self.center_score_time[self.center_score_index[self.object_position + 1]]
        if self.center_score_time[time_index] > vol_95:
            if vol_new < vol_95:
                return max(vol_new, vol_94) - vol_95
            return 0
        elif self.center_score_time[time_index] == vol_95:
            if change_vol < 0:
                return max(vol_new, vol_94) - vol_95
            else:
                return min(vol_new, vol_96) - vol_95
        else:
            if vol_new <= vol_95:
                return 0
            else:
                return min(vol_new, vol_96) - vol_95

    def opt_site_cost(self, counts=1500, deadline=250):
        for i in range(counts):
            for site in self.site_keys:
                self.opt_site_cost_once(site)
            if self.get_run_time() >= deadline:
                break

    def opt_center_cost(self):
        time_index = self.center_cost_pos
        for st in self.client_demands[time_index]:
            flag, to_site = self.get_available_site(st, time_index)
            if flag:
                self.move_stream(st, st.site, to_site, time_index)
                return
        return

    def opt_site_cost_once(self, site):
        time_index = self.site_vol_index[site][self.object_position]
        for st in self.client_demands[time_index]:
            if st.site != site:
                continue
            flag, to_site = self.get_available_site(st, time_index)
            if flag:
                self.move_stream(st, st.site, to_site, time_index)
                return
        return 0

    def cal_score(self, site, vol):
        if vol == 0:
            if self.site_total_vol[self.site_vol_index[site][-1]][site] == 0:
                return 0
        if vol <= self.base_cost:
            return self.base_cost
        return (vol - self.base_cost) ** 2 / self.site_bandwidth[site] + vol

    def run(self, counts=1500, deadline=250):
        self.handle_demand()
        self.percent95_distribution()
        self.opt_init()
        # change_vol = 0
        # for _ in range(20):
        #     self.opt_center_cost()
        self.opt_site_cost(counts, deadline)
        self.judge()
        self.analyze()
        self.write_to_txt(self.time_choose_sites)

if __name__ == '__main__':
    method = Opt()
    method.run()
    print(method.get_run_time())
