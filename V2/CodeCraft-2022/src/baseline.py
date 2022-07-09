#!/usr/bin/env python
# -*- coding:utf-8 -*-
import math
from settings import Settings


class BaseLine(Settings):
    def __init__(self):
        super(BaseLine, self).__init__()
        self.site_used_vol_list = [[0 for _ in self.site_keys] for _ in range(self.time_num)]
        self.max_pre_handle_num = int(0.05 * self.time_num - 20)
        self.object_position = int(math.ceil(0.95 * self.time_num) - 1)
        self.each_site_max_stream = [[[0 for _ in range(len(self.stream_names_list[time_index]))]
                                      for _ in self.site_keys] for time_index in range(self.time_num)]

    def update_output(self, st, site, time_index):
        st.site = site
        self.site_used_vol_list[time_index][site] += st.vol
        if self.each_site_max_stream[time_index][site][st.stream] < st.vol:
            self.each_site_max_stream[time_index][site][st.stream] = st.vol


    def get_one_site_score(self, use_vol, site):
        """
        获取某个节点的得分
        """
        return use_vol ** 2 / self.site_bandwidth[site]

    def handle_demand(self):
        """
        按照客户点数排序
        """
        tmp = [(site, len(self.get_leisure_client(site)), self.site_bandwidth[site]) for site in self.site_keys
               if len(self.get_leisure_client(site)) > 0]
        sites = sorted(tmp, key=lambda k: (k[1], k[2]), reverse=True)
        for site in sites:
            self.handle_demand_one_site(site[0])

    def handle_demand_one_site(self, site):
        priority_time_list = self.get_priority_time_list_of_site(site)
        if len(priority_time_list) == 0:
            return
        limit_vol = int(self.site_bandwidth[site] * 0.05)
        clients = self.get_leisure_client(site)
        client_stream_map = {client: None for client in clients}
        for time_index in priority_time_list:
            streams = []
            for st in self.client_demands[time_index]:
                if st.site == -1 and st.client in client_stream_map:
                    streams.append(st)

            streams = sorted(streams, key=lambda k: k.vol, reverse=True)

            for st in streams:
                stream_vol = st.vol
                site_vol = self.site_bandwidth[site] - self.site_used_vol_list[time_index][site]
                if site_vol - limit_vol < stream_vol:
                    continue
                self.update_output(st, site, time_index)
                self.remove_demand(st.client, stream_vol, time_index)
                self.client_all_demand[time_index][st.client] -= stream_vol

    def get_priority_time_list_of_site(self, site):
        priority_time_list = sorted(range(len(self.site_sum_list[site])),
                                    key=lambda x: self.site_sum_list[site][x], reverse=True)[:self.max_pre_handle_num]

        return priority_time_list

    def match_once(self, time_index):
        """
        对一个时刻进行分配
        """
        streams = [st for st in self.client_demands[time_index] if st.site == -1]

        streams = sorted(streams, key=lambda k: k.vol, reverse=True)

        for st in streams:
            suitable_site = self.get_suitable_site(st, time_index)
            self.update_output(st, suitable_site, time_index)

    def get_suitable_site(self, st, time_index):
        stream_vol = st.vol
        client = st.client
        stream_name = st.stream
        sites = self.get_leisure_site(client)
        min_cost = float('inf')
        target_site = None
        for site in sites:

            use_vol = self.site_used_vol_list[time_index][site] + stream_vol
            if use_vol <= self.site_bandwidth[site]:
                center_cost = 0 if self.each_site_max_stream[time_index][site][
                                       stream_name] >= stream_vol else stream_vol
                weight_cost = self.get_one_site_score(use_vol, site)

                total_cost = weight_cost + center_cost * self.center_cost
                # total_cost = center_cost * self.center_cost
                if min_cost > total_cost:
                    target_site = site
                    min_cost = total_cost
        return target_site

    def add_cache_to_use(self, time_index):
        if time_index == 0:
            return
        for site in self.site_keys:
            self.site_used_vol_list[time_index][site] += int(self.site_used_vol_list[time_index - 1][site] * 0.05)

    def precent95_distribution(self):
        for time_index in range(0, self.time_num):
            self.add_cache_to_use(time_index)
            self.match_once(time_index)

    def run(self):
        self.handle_demand()
        self.precent95_distribution()
        self.write_to_txt()

    def test_run(self):
        self.handle_demand()
        self.precent95_distribution()
        if not self.judge():
            print("95分配不合法")
            return False
        self.analyze()
        self.write_to_txt()

        return True

    def judge(self):
        self.site_judge_vol_list = [[0 for _ in self.site_keys] for _ in range(self.time_num)]
        for time_index in range(self.time_num):
            for site in self.site_keys:
                self.site_judge_vol_list[time_index][site] = self.site_used_vol_list[time_index][site]
                if self.site_bandwidth[site] < self.site_judge_vol_list[time_index][site]:
                    print(f'时刻 {time_index} 边缘节点 {site} 超限 '
                          f'{self.site_judge_vol_list[time_index][site]}/{self.site_bandwidth[site]}')
                    return False
        sum_score = 0
        for site in self.site_keys:
            arr = []
            for time_index in range(self.time_num):
                arr.append(self.site_judge_vol_list[time_index][site])
            arr.sort()
            vol = arr[self.object_position]
            if vol == 0:
                if max(arr) == 0:
                    continue
            sum_score += self.base_cost if vol <= self.base_cost else (vol - self.base_cost) ** 2 / self.site_bandwidth[
                site] + vol
        print(f"边缘节点得分为 : {round(sum_score, 2)}")
        return True

    def analyze(self):
        site_score_time = [-1 for _ in self.site_keys]
        center_score_time = [0 for _ in range(self.time_num)]

        self.site_vol_list = [[0 for _ in range(self.time_num)] for _ in self.site_keys]
        for site in self.site_keys:
            for time_index in range(self.time_num):
                self.site_vol_list[site][time_index] = self.site_judge_vol_list[time_index][site]
                center_score_time[time_index] += sum(self.each_site_max_stream[time_index][site])
            site_score_time[site] = sorted(range(self.time_num), key=lambda k: self.site_vol_list[site][k])[
                self.object_position]
        center_record_time = sorted(range(self.time_num), key=lambda k: center_score_time[k])[self.object_position]
        print(
            f'中心节点的得分计算时刻为: {center_record_time} 得分为: {round(center_score_time[center_record_time] * self.center_cost, 2)}')
        record_sites = []
        record_score = []
        for site in self.site_keys:
            if self.site_vol_list[site][center_record_time] > self.site_vol_list[site][site_score_time[site]]:
                record_sites.append(site)
                record_score.append(sum(self.each_site_max_stream[center_record_time][site]))
        print(f"中心节点记录得分的时刻，以下节点处于后5%: {record_sites} 对应的总分数为 {sum(record_score)}")


if __name__ == '__main__':
    method = BaseLine()
    flag = method.test_run()
    method.get_run_time()
    if flag:
        from judgement_tools.judgement import JudgeMent

        judge = JudgeMent('solution.txt')
        judge.run_judge()
