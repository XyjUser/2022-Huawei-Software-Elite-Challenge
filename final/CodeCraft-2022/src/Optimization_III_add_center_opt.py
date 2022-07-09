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
            # print(f"({self.site_total_vol[time_index][site]} + {vol}) / {self.site_bandwidth[site]}")
            if self.site_total_vol[time_index][site] + vol > self.site_bandwidth[site]:
                # print(f"({self.site_total_vol[time_index][site]} + {vol}) / {self.site_bandwidth[site]}")
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
        # print(f"move site_from:{from_site}  site_to{to_site}  move stream:{st}")
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
            # site_vol = self.site_total_vol[time_index][site]
            # thre_vol = self.site_total_vol[self.site_vol_index[site][self.object_position]][site]
            # if site_vol > thre_vol:
            #     change_vol = self.center_change_vol(st.site, site, st, time_index) * self.center_cost
            #     if change_vol <= 0:
            #         # print(f'center_change_vol :{change_vol}')
            #         return True, site, change_vol
            # else:
            change_vol_center = self.center_change_vol(st.site, site, st, time_index) * self.center_cost
            # change_vol_center = 0
            # change_vol_site = 0
            change_vol_site = self.site_change_vol(st.site, site, st, time_index)
            change_vol = change_vol_center + change_vol_site

            if change_vol <= 0:
                # print(f"{time_index} st.vol: {st.vol} change_vol_center:{int(change_vol_center)}  change_vol_site : {int(change_vol_site)} change_vol:{int(change_vol)}")
                return True, site, change_vol
        return False, None, 0

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
            # change_vol_from -= self.calc_cache(site_to, st.vol, time_index, time95)

        return change_vol_from + change_vol_to

    def calc_cache(self, site, change_vol, start_time, end_time):
        time_index = start_time
        while time_index < end_time and change_vol != 0:
            last_cache = int(self.site_total_vol[time_index][site] * 0.05)
            new_cache = int((self.site_total_vol[time_index][site] + change_vol) * 0.05)
            change_vol = new_cache - last_cache
            time_index += 1

        return change_vol

    def center_change_vol(self, site_from, site_to, st, time_index):
        """
        移动该流对中心成本的变化，降低了多少分
        """
        change_vol = 0
        if st.vol == self.each_site_max_stream[time_index][site_from][st.stream]:
            change_vol += self.each_site_2nd_stream[time_index][site_from][st.stream] - st.vol
            # print('each_site_2nd_stream', self.each_site_2nd_stream[time_index][site_from][st.stream])
        if st.vol > self.each_site_max_stream[time_index][site_to][st.stream]:
            change_vol += st.vol - self.each_site_max_stream[time_index][site_to][st.stream]
        vol_new = self.center_score_time[time_index] + change_vol
        vol_95 = self.center_score_time[self.center_cost_pos]
        vol_94 = self.center_score_time[self.center_score_index[self.object_position - 1]]
        vol_96 = self.center_score_time[self.center_score_index[self.object_position + 1]]

        # print(f"time_95: {self.center_cost_pos} vol_95: {vol_95}  time_96: {self.center_score_index[self.object_position + 1]} vol_96: {vol_96}")

        if self.center_score_time[time_index] > self.center_score_time[self.center_cost_pos]:
            if vol_new < vol_95:
                return max(vol_new, vol_94) - vol_95
            return 0
        elif self.center_score_time[time_index] == self.center_score_time[self.center_cost_pos]:
            # print('in', change_vol, st.vol)
            # print(self.each_site_max_stream[time_index][site_from][st.stream])
            if change_vol < 0:
                return max(vol_new, vol_94) - vol_95
            else:
                # print(min(vol_new, vol_96) - vol_95)
                return min(vol_new, vol_96) - vol_95
        else:
            if vol_new <= vol_95:
                return 0
            else:
                return min(vol_new, vol_96) - vol_95

    def opt_site_cost(self):
        # last_site_score, last_center_score, last_score = self.get_score()
        for i in range(150):
            change_vol = 0
            # sites = sorted(self.site_keys,
            #                key=lambda k: self.site_total_vol[self.site_vol_index[k][self.object_position]][k], reverse=True)
            for site in self.site_keys:
                change_vol += self.opt_site_cost_once(site)
            # site_score, center_score, new_score = self.get_score()
            # print('='*30, f'N0.{i + 1} last_score: {last_score} now_score: {new_score}', '='*30)
            # print(f'theory_change_score: {int(-change_vol)} real_change_score: {last_score - new_score}')
            # print(f'last_site_score:{last_site_score} last_center_score: {last_center_score}')
            # print(f'new_site_score:{site_score} new_center_score: {center_score}')
            # last_score = new_score
            # last_site_score = site_score
            # last_center_score = center_score

    def opt_center_cost(self):
        time_index = self.center_cost_pos
        for st in self.client_demands[time_index]:
            flag, to_site, change_vol = self.get_available_site(st, time_index)
            if flag:
                self.move_stream(st, st.site, to_site, time_index)
                print(change_vol)
                return

    def opt_site_cost_once(self, site):
        time_index = self.site_vol_index[site][self.object_position]
        for st in self.client_demands[time_index]:
            if st.site != site:
                continue
            flag, to_site, change_vol = self.get_available_site(st, time_index)
            if flag:
                self.move_stream(st, site, to_site, time_index)
                return change_vol
        return 0

    def opt_site_cost_once_max(self, site):
        max_change_vol = 0
        max_to_site = None
        max_st = None
        time_index = self.site_vol_index[site][self.object_position]
        for st in self.client_demands[time_index]:
            if st.site != site:
                continue
            flag, to_site, change_vol = self.get_available_site(st, time_index)
            if flag and max_change_vol > change_vol:
                max_change_vol = change_vol
                max_to_site = to_site
                max_st = st
        if max_to_site:
            self.move_stream(max_st, site, max_to_site, time_index)

            return max_change_vol

    def cal_score(self, site, vol):
        if vol == 0:
            if self.site_total_vol[self.site_vol_index[site][-1]][site] == 0:
                return 0
        if vol <= self.base_cost:
            return self.base_cost
        return (vol - self.base_cost) ** 2 / self.site_bandwidth[site] + vol

    def get_score(self):
        site_score = 0
        center_score = self.center_score_time[self.center_cost_pos] * self.center_cost
        for site in self.site_keys:
            t = self.site_vol_index[site][self.object_position]
            site_score += self.cal_score(site, self.site_total_vol[t][site])
        # print(
        #     f"边缘节点得分 : {round(site_score, 2)} 中心节点得分 : {round(center_score, 2)} 总得分 : {int(site_score + center_score)}")
        return round(site_score), round(center_score), int(site_score + center_score)



    def run(self):
        self.handle_demand()
        self.percent95_distribution()
        self.opt_init()
        # self.get_score()
        # for _ in range(1000):
        #     self.opt_center_cost()
        self.opt_site_cost()
        self.judge()

        self.write_to_txt()


if __name__ == '__main__':
    method = Opt()
    method.run()
    method.get_run_time()
    from judgement_tools.judgement import JudgeMent

    judge = JudgeMent('solution.txt')
    judge.run_judge()
