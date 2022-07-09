#!/usr/bin/env python
# -*- coding:utf-8 -*-
import math

from settings import Settings


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
    return streams_names, streams


class BaseLine(Settings):
    def __init__(self):
        super(BaseLine, self).__init__()
        self.output = [{client: {} for client in self.client_names} for _ in range(self.time_num)]
        self.site_used_vol_list = [[0 for _ in self.site_keys] for _ in range(self.time_num)]
        self.site_cache_list = [[0 for _ in self.site_keys] for _ in range(self.time_num)]

        self.max_prehandle_num = int(0.05 * self.time_num - 20)
        self.object_position = int(math.ceil(0.95 * self.time_num) - 1)

    def update_output(self, client, stream_id, vol, site, time_index):
        stream = self.stream_names_list[time_index][stream_id]
        site_name = self.site_names[site]
        client_name = self.client_names[client]
        try:
            self.output[time_index][client_name][site_name].append(stream)
        except:
            self.output[time_index][client_name][site_name] = [stream]
        self.site_used_vol_list[time_index][site] += vol
        if time_index + 1 < self.time_num:
            if self.site_cache_list[time_index + 1][site] == 0:
                self.site_cache_list[time_index + 1][site] += self.site_cache_list[time_index][site] * 0.05
            self.site_cache_list[time_index + 1][site] += vol * 0.05

    def get_one_site_score(self, use_vol, site):
        """
        获取某个节点的得分
        Args:
            use_vol:
            site:

        Returns:

        """
        # if use_vol <= self.base_cost:
        #     return self.base_cost
        return (use_vol) ** 2 / self.site_bandwidth[site]

    def handle_demand(self):
        """按照客户点数排序"""
        tmp = [(site, len(self.get_leisure_client(site)), self.site_bandwidth[site]) for site in self.site_keys
               if len(self.get_leisure_client(site)) > 0]
        sites = sorted(tmp, key=lambda k: k[1],reverse=True)
        # sites = sorted(sites, key=lambda k: k[2], reverse=True)

        for site in sites:
            self.handle_demand_one_site(site[0])

    def handle_demand_one_site(self, site):
        priority_time_list = self.get_priority_time_list_of_site(site)
        if len(priority_time_list) == 0:
            return
        for time_index in priority_time_list:

            if time_index == 0:
                limit_vol = 0
            else:
                limit_vol = int(self.site_bandwidth[site] * 0.05)
            clients = self.get_leisure_client(site)
            streams_names, streams = self.get_streams(clients, time_index)
            for stream_name in streams_names:
                client = stream_name // 100
                stream = stream_name - client * 100
                stream_vol = self.client_demands[time_index][client][stream]
                site_vol = self.site_bandwidth[site] - self.site_used_vol_list[time_index][site]
                if site_vol - limit_vol < stream_vol:
                    continue
                self.update_output(client, stream, stream_vol, site, time_index)
                self.client_demands[time_index][client][stream] = 0
                self.remove_demand(client, stream_vol, time_index)
                self.client_all_demand[time_index][client] -= stream_vol

    def get_priority_time_list_of_site(self, site):
        priority_time_list = sorted(range(len(self.site_sum_list[site])),
                                    key=lambda x: self.site_sum_list[site][x], reverse=True)[:self.max_prehandle_num]
        return priority_time_list

    def get_streams(self, clients, time_index):
        '''
        将一个时刻所有的stream整合到一起，每一个stream名字变为 client_stream
        Args:
            clients:
            time_index:
        Returns:
            streams : 整合好的流
        '''
        streams = {}
        for client in clients:
            sts = self.client_demands[time_index][client]
            for st in range(len(sts)):
                if sts[st] > 0:
                    idx = client * 100 + st
                    streams[idx] = sts[st]
                    # streams_names.append(idx)
        streams_names = sorted(list(streams.keys()), key=lambda k: streams[k], reverse=True)
        return streams_names, streams

    def match_once(self, time_index):
        """
        对一个时刻进行分配
        Args:
            time_index:

        Returns:

        """
        demand = self.client_demands[time_index]
        streams_names, streams = merge_streams(demand)
        for stream_name in streams_names:
            client = stream_name // 100
            stream = stream_name - client * 100
            vol = streams[stream_name]
            site = self.get_min_vol_site(client, vol, time_index)
            self.update_output(client, stream, vol, site, time_index)

    def add_cache_to_cur(self, time_index):
        for site in self.site_keys:
            self.site_used_vol_list[time_index][site] += int(self.site_cache_list[time_index][site])

    def remove_cache_to_cur(self, time_index):
        for site in self.site_keys:
            self.site_used_vol_list[time_index][site] -= int(self.site_cache_list[time_index][site])

    def get_min_vol_site(self, client, vol, time_index):
        """
        获取当前时刻所选择的流可以分配的边缘节点中增长最慢的边缘节点
        Args:
            client:
            vol:
            time_index:

        Returns:

        """
        sites = self.get_leisure_site(client)
        target_site = None
        min_score = 1000000
        for site in sites:
            use_vol = self.site_used_vol_list[time_index][site] + vol
            if use_vol <= self.site_bandwidth[site]:
                score = self.get_one_site_score(use_vol, site)
                if score < min_score:
                    min_score = score
                    target_site = site
        return target_site

    def precent95_distribution(self):
        self.match_once(0)
        for time_index in range(1, self.time_num):
            self.add_cache_to_cur(time_index)
            self.match_once(time_index)
            self.remove_cache_to_cur(time_index)

    def run(self):
        self.handle_demand()
        self.precent95_distribution()
        self.write_to_txt(self.output)

    def test_run(self):
        self.handle_demand()
        if not self.judge():
            print("预分配不合法")
            return False
        self.precent95_distribution()
        if not self.judge():
            print("95分配不合法")
            return False
        self.write_to_txt(self.output)
        return True

    def judge(self):
        for time_index in range(self.time_num):
            for site in self.site_keys:
                if self.site_bandwidth[site] < self.site_used_vol_list[time_index][site] + \
                        int(self.site_cache_list[time_index][site]):
                    print(f'时刻 {time_index} 边缘节点 {site} 超限')
                    return False
        return True


if __name__ == '__main__':
    method = BaseLine()
    flag = method.test_run()
    method.get_run_time()
    if flag:
        from judgement_tools.judgement import JudgeMent

        judge = JudgeMent('solution.txt')
        judge.run_judge()
