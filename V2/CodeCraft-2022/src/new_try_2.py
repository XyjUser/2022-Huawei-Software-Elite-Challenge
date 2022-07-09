#!/usr/bin/env python
# -*- coding:utf-8 -*-
import math
from settings import Settings
import heapq


def load_time_client_stream_map(client_demands, time_num, client_names, stream_names_list):
    time_client_stream_map = [
        [[None for _ in range(len(stream_names_list[time_index]))] for _ in range(len(client_names))]
        for time_index in range(time_num)]
    for time_index in range(time_num):
        for st in client_demands[time_index]:
            time_client_stream_map[time_index][st.client][st.stream] = st
    return time_client_stream_map


class BaseLine(Settings):
    def __init__(self):
        super(BaseLine, self).__init__()
        self.time_index_tuple = [i for i in range(self.time_num)]
        self.site_used_vol_list = [[0 for _ in self.site_keys] for _ in self.time_index_tuple]
        self.max_pre_handle_num = int(0.05 * self.time_num) - 25
        self.object_position = int(math.ceil(0.95 * self.time_num)) - 1
        self.each_site_max_stream = [[[0 for _ in range(len(self.stream_names_list[time_index]))]
                                      for _ in self.site_keys] for time_index in self.time_index_tuple]
        self.time_client_stream_map = load_time_client_stream_map(self.client_demands, self.time_num,
                                                                  self.client_names, self.stream_names_list)
        self.time_max_fill_sites = [{} for _ in self.time_index_tuple]
        self.time_middle_fill_sites = [{} for _ in self.time_index_tuple]

    def update_output(self, st, site, time_index):
        st.site = site
        self.site_used_vol_list[time_index][site] += st.vol
        if self.each_site_max_stream[time_index][site][st.stream] < st.vol:
            self.each_site_max_stream[time_index][site][st.stream] = st.vol

    def handle_demand(self):
        """
        按照客户点数排序
        """
        tmp = [(site, len(self.get_leisure_client(site)), self.site_bandwidth[site]) for site in self.site_keys
               if len(self.get_leisure_client(site)) > 0]
        sites = sorted(tmp, key=lambda k: (k[1], k[2]), reverse=True)
        for site in sites:
            time_list = self.choose_time_index(site[0])
            self.handle_sites(site[0], time_list)

    def handle_sites(self, site, time_list):
        clients = self.get_leisure_client(site)
        site_bandwidth = self.site_bandwidth[site]
        c_05, c_01 = int(self.site_bandwidth[site] * 0.05), int(site_bandwidth * 0.01)
        for i, time_index in enumerate(time_list):
            self.time_max_fill_sites[time_index][site] = None
            site_bandwidth = self.site_bandwidth[site]
            if time_index == 0:
                bandwidth = self.site_bandwidth[site]
            else:
                last_time = time_index - 1
                if last_time == time_list[i - 1]:
                    bandwidth = site_bandwidth - c_05
                else:
                    bandwidth = site_bandwidth - c_01
            labeled_streams = self.statistics_available_streams_infos(clients, bandwidth, time_index)
            self.handle_streams(labeled_streams, site, time_index, clients)

    def handle_streams(self, labeled_streams, site, time_index, clients):
        client_used_map = {client: 0 for client in clients}
        for st in labeled_streams:
            self.update_output(st, site, time_index)
            client_used_map[st.client] += st.vol
        for client in client_used_map:
            self.remove_demand(client, client_used_map[client], time_index)

    def statistics_available_streams_infos(self, clients, bandwidth, time_index):
        if bandwidth <= 0:
            return []
        streams_infos = [[0, 0, []] for _ in range(len(self.stream_names_list[time_index]))]
        streams = []
        labeled_streams = []
        for client in clients:
            for stream in range(len(self.stream_names_list[time_index])):
                st = self.time_client_stream_map[time_index][client][stream]
                if st is not None and st.site == -1:
                    streams.append(st)
        streams_list = sorted(streams, key=lambda k: k.vol, reverse=True)
        for st in streams_list:
            if streams_infos[st.stream][0] + st.vol <= bandwidth:
                streams_infos[st.stream][0] += st.vol
                streams_infos[st.stream][1] += 1
                streams_infos[st.stream][2].append(st)
            else:
                streams_infos[st.stream][0] = bandwidth
        streams_infos = sorted(streams_infos, key=lambda k: (k[0], -k[1]), reverse=True)
        for streams_info in streams_infos:
            for st in streams_info[2]:
                if st.vol <= bandwidth:
                    labeled_streams.append(st)
                    bandwidth -= st.vol
                    if bandwidth == 0:
                        break
        return labeled_streams

    def choose_time_index(self, site):
        time_list = heapq.nlargest(self.max_pre_handle_num, self.time_index_tuple,
                                   key=lambda x: self.site_sum_list[site][x])
        time_max_set = {}
        time_middle_set = {}
        num = 0
        for time_index in time_list:
            if time_index in time_max_set:
                continue
            if time_index in time_middle_set:
                del time_middle_set[time_index]
                time_max_set[time_index] = None
            else:
                time_max_set[time_index] = None
                num += 1
                if num == self.max_pre_handle_num:
                    break
                if time_index + 1 < self.time_num:
                    if time_index + 1 in time_max_set:
                        continue
                    time_middle_set[time_index + 1] = None
                    num += 1
                    if num == self.max_pre_handle_num:
                        break
        time_max_list = list(time_max_set.keys())
        time_middle_list = list(time_middle_set.keys())
        time_list = []
        for time_index in time_max_list:
            time_list.append(time_index)
        for time_index in time_middle_list:
            self.time_middle_fill_sites[time_index][site] = None
        time_list.sort()
        return time_list

    def add_cache_to_use(self, time_index):
        if time_index == 0:
            return
        for site in self.site_keys:
            self.site_used_vol_list[time_index][site] += int(self.site_used_vol_list[time_index - 1][site] * 0.05)

    def match_once(self, time_index):
        sties_95_map = self.time_max_fill_sites[time_index]
        sites_20v_map = self.time_middle_fill_sites[time_index]
        streams = [st for st in self.client_demands[time_index] if st.site == -1]
        streams.sort(key=lambda k: k.vol, reverse=True)
        for st in streams:
            site = self.get_suitable_site(time_index, st, sties_95_map, sites_20v_map)
            self.update_output(st, site, time_index)

    def get_site_cost(self, used_vol, site):
        return used_vol ** 2 / self.site_bandwidth[site]

    def get_suitable_site(self, time_index, st, sties_95_map, sites_20v_map):
        sites = self.get_leisure_site(st.client)
        target_site = None
        target_score = float('inf')
        min_cost = float('inf')
        under_threshold_site = []
        above_threshold_site = []
        v20 = 20 * self.base_cost
        for site in sites:
            used_vol = self.site_used_vol_list[time_index][site] + st.vol

            if used_vol > self.site_bandwidth[site]:
                continue
            if site in sites_20v_map and used_vol > v20:
                continue
            if used_vol <= self.base_cost:
                under_threshold_site.append((site, used_vol))
            else:
                above_threshold_site.append((site, used_vol))
        if under_threshold_site:
            for site, vol in under_threshold_site:
                cost = st.vol * self.center_cost if st.vol > self.each_site_max_stream[time_index][site][
                    st.stream] else 0
                score = self.get_site_cost(vol, site) if site not in sties_95_map else 0
                if cost == min_cost:
                    if score < target_score:
                        target_score = score
                        target_site = site
                elif cost < min_cost:
                    target_site = site
                    target_score = score
                    min_cost = cost
            return target_site

        for site, vol in above_threshold_site:
            center_score = st.vol * self.center_cost if st.vol > self.each_site_max_stream[time_index][site][
                st.stream] else 0
            site_cost = self.get_site_cost(vol, site) if site not in sties_95_map else 0
            cost = site_cost + center_score
            if cost == min_cost:
                if self.site_bandwidth[site] > self.site_bandwidth[target_site]:
                    target_site = site
            elif cost < min_cost:
                min_cost = cost
                target_site = site
        return target_site

    def percent95_distribution(self):
        for time_index in range(0, self.time_num):
            self.add_cache_to_use(time_index)
            self.match_once(time_index)

    def run(self):
        self.handle_demand()
        self.percent95_distribution()
        self.write_to_txt()

    def test_run(self):
        self.handle_demand()
        self.percent95_distribution()
        self.check_middle()
        self.write_to_txt()

        return True

    def check_middle(self):
        for time_index in self.time_index_tuple:
            sites = self.time_middle_fill_sites[time_index]
            for site in sites:
                if self.site_used_vol_list[time_index][site] > 20 * self.base_cost:
                    print(time_index, site, self.site_used_vol_list[time_index][site])

    def judge(self):
        self.site_judge_vol_list = [[0 for _ in self.site_keys] for _ in self.time_index_tuple]
        for time_index in self.time_index_tuple:
            for site in self.site_keys:
                self.site_judge_vol_list[time_index][site] = self.site_used_vol_list[time_index][site]
                if self.site_bandwidth[site] < self.site_judge_vol_list[time_index][site]:
                    print(f'时刻 {time_index} 边缘节点 {site} 超限 '
                          f'{self.site_judge_vol_list[time_index][site]}/{self.site_bandwidth[site]}')
                    return False
        sum_score = 0
        for site in self.site_keys:
            arr = []
            for time_index in self.time_index_tuple:
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
        center_score_time = [0 for _ in self.time_index_tuple]

        self.site_vol_list = [[0 for _ in self.time_index_tuple] for _ in self.site_keys]
        for site in self.site_keys:
            for time_index in self.time_index_tuple:
                self.site_vol_list[site][time_index] = self.site_judge_vol_list[time_index][site]
                center_score_time[time_index] += sum(self.each_site_max_stream[time_index][site])
            site_score_time[site] = sorted(self.time_index_tuple, key=lambda k: self.site_vol_list[site][k])[
                self.object_position]
        center_record_time = sorted(self.time_index_tuple, key=lambda k: center_score_time[k])[self.object_position]
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
