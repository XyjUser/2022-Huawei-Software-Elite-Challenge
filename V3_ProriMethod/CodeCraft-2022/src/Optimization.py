#!/usr/bin/env python
# -*- coding:utf-8 -*-
# from baseline import BaseLine
from new_start import BaseLine


class Opt(BaseLine):
    def __init__(self):
        super(Opt, self).__init__()
        self.center_score_time = [0 for _ in range(self.time_num)]
        self.site_total_vol = [[0 for _ in range(self.time_num)] for _ in self.site_keys]
        self.site_vol_index = [[i for i in range(self.time_num)] for _ in self.site_keys]
        self.center_score_index = []

    def opt_init(self):
        for site in self.site_keys:
            for time_index in range(self.time_num):
                self.site_total_vol[site][time_index] = self.site_used_vol_list[time_index][site] + \
                                                        int(self.site_cache_list[time_index][site])
            self.site_vol_index[site] = sorted(range(self.time_num), key=lambda k: self.site_total_vol[site][k])

        self.init_center_score()
        self.center_cost_pos = self.center_score_index[self.object_position]

    def init_center_score(self):
        for site in self.site_keys:
            for time_index in range(self.time_num):
                self.center_score_time[time_index] += sum(self.each_site_max_stream[time_index][site])
        self.center_score_index = sorted(range(self.time_num), key=lambda k: self.center_score_time[k])

    def update_stream_cache(self, site, time_index):
        """
        更新一个流后，更新对节点的缓存有影响的时刻
        """
        t = time_index + 1
        while t < self.time_num:
            last_use_vol = self.site_used_vol_list[t - 1][site] + self.site_cache_list[t - 1][site]
            last_cache = self.site_cache_list[t][site]
            new_cache = int(last_use_vol * 0.05)
            err = last_cache - new_cache
            if err == 0:
                break
            self.site_cache_list[t][site] = new_cache
            self.site_total_vol[site][t] -= err
            t += 1

    def is_add_legal(self, vol, site, time_index):
        """
        当前节点增加流是否合法
        """
        if self.site_total_vol[site][time_index] + vol > self.site_bandwidth[site]:
            return False
        t = time_index + 1
        cache = int((self.site_total_vol[site][time_index] + vol) * 0.05)
        while t < self.time_num:
            if cache == self.site_cache_list[t][site]:
                return True
            elif cache + self.site_used_vol_list[t][site] > self.site_bandwidth[site]:
                return False
            else:
                cache = int((cache + self.site_used_vol_list[t][site]) * 0.05)
                t += 1
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

        self.site_used_vol_list[time_index][from_site] -= stream_vol
        self.site_total_vol[from_site][time_index] -= stream_vol

        self.site_used_vol_list[time_index][to_site] += stream_vol
        self.site_total_vol[to_site][time_index] += stream_vol

        self.update_stream_cache(from_site, time_index)
        self.update_stream_cache(to_site, time_index)

        if self.each_site_max_stream[time_index][from_site][st.stream] == stream_vol:
            s_vol, nd_vol = self.find_max_2nd_stream(time_index, from_site, st.stream)
            self.each_site_max_stream[time_index][from_site][st.stream] = s_vol
            self.each_site_2nd_stream[time_index][from_site][st.stream] = nd_vol
            self.center_score_time[time_index] -= stream_vol - s_vol

        if self.each_site_max_stream[time_index][to_site][st.stream] < stream_vol:
            self.center_score_time[time_index] += stream_vol - self.each_site_max_stream[time_index][to_site][st.stream]
            self.each_site_2nd_stream[time_index][to_site][st.stream] = self.each_site_max_stream[time_index][to_site][
                st.stream]
            self.each_site_max_stream[time_index][to_site][st.stream] = stream_vol

        self.sort_site_index(to_site)
        self.sort_site_index(from_site)
        self.sort_center_index()

    def sort_site_index(self, site):
        self.site_vol_index[site] = sorted(range(self.time_num), key=lambda k: self.site_total_vol[site][k])

    def sort_center_index(self):
        self.center_score_index = sorted(range(self.time_num), key=lambda k: self.center_score_time[k])
        self.center_cost_pos = self.center_score_index[self.object_position]

    def get_available_site(self, st, time_index):
        sites = self.get_leisure_site(st.client)
        for site in sites:
            if st.site == site:
                continue
            site_vol = self.site_total_vol[site][time_index]
            thre_vol = self.site_total_vol[site][self.site_vol_index[site][self.object_position]]
            if not self.is_add_legal(st.vol, site, time_index):
                continue
            if site_vol > thre_vol:
                change_vol = self.center_change_vol(st.site, site, st, time_index) * self.center_cost
                if change_vol >= 0:
                    return True, site, change_vol
            else:
                change_vol_center = self.center_change_vol(st.site, site, st, time_index) * self.center_cost
                change_vol_site = self.site_change_vol(st.site, site, st, time_index)
                change_vol = change_vol_center + change_vol_site
                if change_vol > 0:
                    return True, site, change_vol
        return False, None, 0

    def site_change_vol(self, site_from, site_to, st, time_index):
        new_vol = self.cal_score(site_from, self.site_total_vol[site_from][time_index] - st.vol)
        last_vol = self.cal_score(site_from, self.site_total_vol[site_from][time_index])
        below_index = self.site_vol_index[site_from][self.object_position - 1]
        below_vol = self.cal_score(site_from, self.site_total_vol[site_from][below_index])
        change_vol_from = last_vol - max(new_vol, below_vol)

        new_vol = self.cal_score(site_from, self.site_total_vol[site_to][time_index] + st.vol)
        last_vol = self.cal_score(site_from, self.site_total_vol[site_to][time_index])
        obj_time = self.site_vol_index[site_to][self.object_position]

        beyond_time = self.site_vol_index[site_to][self.object_position + 1]
        beyond_vol = self.cal_score(site_from, self.site_total_vol[site_to][beyond_time])
        if obj_time == time_index:
            change_vol_to = last_vol - min(beyond_vol, new_vol)
        else:
            obj_vol = self.cal_score(site_from, self.site_total_vol[site_to][obj_time])
            if obj_vol >= new_vol:
                change_vol_to = 0
            else:
                change_vol_to = last_vol - min(beyond_vol, new_vol)
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
        vol1 = self.center_score_time[time_index] + change_vol
        vol2 = self.center_score_time[self.center_cost_pos]
        if vol1 > vol2:
            return vol2 - vol1
        if self.center_cost_pos == time_index:
            return vol2 - vol1
        return 0



    def opt_site_cost(self):
        for site in self.site_keys:
            for i in range(100):
                self.opt_site_cost_once(site)
        # self.get_score()

    def opt_center_cost(self):
        time_index = self.center_cost_pos
        for st in self.client_demands[time_index]:
            flag, to_site, change_vol = self.get_available_site(st, time_index)
            if flag:
                self.move_stream(st, st.site, to_site, time_index)

    def opt_site_cost_once(self, site):
        change_vol = 0
        time_index = self.site_vol_index[site][self.object_position]
        # print(time_index)
        for st in self.client_demands[time_index]:
            if st.site != site:
                continue
            flag, to_site, change_vol = self.get_available_site(st, time_index)
            if flag:
                self.move_stream(st, site, to_site, time_index)
        return change_vol

    def cal_score(self, site, vol):
        if vol == 0:
            if max(self.site_total_vol[site]) == 0:
                return 0
        if vol <= self.base_cost:
            return self.base_cost
        return (vol - self.base_cost) ** 2 / self.site_bandwidth[site] + vol

    def get_score(self):
        site_score = 0
        center_score = self.center_score_time[self.center_cost_pos] * self.center_cost
        for site in self.site_keys:
            t = self.site_vol_index[site][self.object_position]
            site_score += self.cal_score(site, self.site_total_vol[site][t])
        print(
            f"边缘节点得分 : {round(site_score, 2)} 中心节点得分 : {round(center_score, 2)} 总得分 : {int(site_score + center_score)}")

    def run(self):
        self.handle_demand()
        self.precent95_distribution()
        self.opt_init()
        self.get_score()
        self.opt_site_cost()


        self.write_to_txt()

    def new_judge(self):
        for site in self.site_keys:
            for time_index in range(self.time_num):
                vol1 = self.site_used_vol_list[time_index][site] + int(self.site_cache_list[time_index][site])
                vol2 = self.site_total_vol[site][time_index]
                if vol1 != vol2:
                    print(vol1, vol2)


if __name__ == '__main__':
    method = Opt()
    method.run()
    method.get_run_time()
    from judgement_tools.judgement import JudgeMent

    judge = JudgeMent('solution.txt')
    judge.run_judge()
