#!/usr/bin/env python
# -*- coding:utf-8 -*-
import math
from baseline import BaseLine


class ArrDict:
    def __init__(self):
        self.arr = []
        self.dict = {}

    def put(self, val):
        self.arr.append(val)
        self.dict[val[0]] = val[1]

    def top(self):
        return self.arr[0]

    def pop(self):
        val = self.arr[0]
        if len(self.arr) > 1:
            self.arr = self.arr[1:]
            del self.dict[val[0]]
        else:
            self.arr = []
            self.dict = {}
        return val

    def is_empty(self):
        return len(self.arr) == 0


class PriorLearning(BaseLine):
    def __init__(self):
        super(PriorLearning, self).__init__()
        self.site_cost_info, self.site_max_vol = self.prior_run()
            
        self.initialize()
        self.client_all_demand = self.load_all_demand()
        self.site_sum_list, self.demand_sum_list = self.load_statistic_lists()
        self.site_labeled_time = [[] for _ in range(self.time_num)]
        self.site_target_vol = [0 for _ in range(self.time_num)]

    def label_sites(self):
        # sites = [(site, len(self.get_leisure_client(site)), self.site_bandwidth[site]) for site in self.site_keys
        #          if len(self.get_leisure_client(site)) > 0]
        # sites = sorted(sites, key=lambda k: (k[1], k[2]), reverse=True)
        # for site in sites:
        #     self.label_site(site[0])
        for site in self.site_keys:
            vol, obj = self.site_cost_info[site]
            self.site_labeled_time[obj].append(site)
            self.site_target_vol[site] = vol
            

    # def label_site(self, site):
    #     self.max_pre_handle_num = int(0.05 * self.time_num)
    #     time_index_list = self.get_priority_time_list_of_site(site)
    #     labeled_num = 0
    #     clients = self.get_leisure_client(site)
    #     client_stream_map = {client: None for client in clients}
    #     for time_index in time_index_list:
    #         if site in self.site_labeled_time[time_index]:
    #             continue
    #         self.site_labeled_time[time_index].append(site)
    #         labeled_num += 1
    #         if labeled_num == self.max_pre_handle_num:
    #             return
    #         used_vol = self.handle_site(site, time_index, client_stream_map)
    #         t = time_index + 1
    #         while int(used_vol * 0.05) >= self.site_cost_vol[site] and t < self.time_num:
    #             if site in self.site_labeled_time[t]:
    #                 break
    #             self.site_labeled_time[t].append(site)
    #             labeled_num += 1
    #             if labeled_num == self.max_pre_handle_num:
    #                 return
    #             used_vol = self.handle_site(site, t, client_stream_map)
    #             t += 1

    def handle_site(self, site, time_index, client_stream_map):
        streams = []
        for st in self.client_demands[time_index]:
            if st.site == -1 and st.client in client_stream_map:
                streams.append(st)
        streams = sorted(streams, key=lambda k: k.vol, reverse=True)
        total_vol = 0
        for st in streams:
            stream_vol = st.vol
            site_vol = self.site_bandwidth[site] - self.site_used_vol_list[time_index][site]
            if site_vol < stream_vol:
                continue
            total_vol += stream_vol
            self.update_output(st, site, time_index)
            self.remove_demand(st.client, stream_vol, time_index)
            self.client_all_demand[time_index][st.client] -= stream_vol
        return total_vol

    def maximum_allocation(self, site, streams, time_index):
        clients = self.get_leisure_client(site)
        client_stream_map = {client: None for client in clients}
        for st in streams:
            if st.site != -1 or st.client not in client_stream_map:
                continue
            stream_vol = st.vol
            used_vol = self.site_used_vol_list[time_index][site] + self.site_cache_list[time_index][site]
            site_vol = self.site_bandwidth[site] - used_vol
            if site_vol < stream_vol:
                continue
            self.update_output(st, site, time_index)

    def match_time_index(self, time_index):
        streams = [st for st in self.client_demands[time_index]]
        streams = sorted(streams, key=lambda k: k.vol, reverse=True)
        sites = self.site_labeled_time[time_index]
        for site in sites:
            self.maximum_allocation(site, streams, time_index)
        for st in streams:
            if st.site != -1:
                continue
            suitable_site = self.get_site(st, time_index)
            self.update_output(st, suitable_site, time_index)

    def get_site(self, st,time_index):
        stream_name = st.stream
        stream_vol = st.vol
        sites = self.get_leisure_site(st.client)
        under_target_sites = []
        min_cost = float('inf')
        most_reasonable_site = None
        for site in sites:
            cache = self.site_cache_list[time_index][site]
            use_vol = self.site_used_vol_list[time_index][site] + cache + st.vol
            if use_vol <= self.site_target_vol[site]:
                under_target_sites.append(site)
        if under_target_sites:
            for site in under_target_sites:
                center_cost = 0 if self.each_site_max_stream[time_index][site][
                                       stream_name] >= stream_vol else stream_vol
                if center_cost < min_cost:
                    most_reasonable_site = site
                    min_cost = center_cost
            return most_reasonable_site
        else:
            for site in sites:
                cache = self.site_cache_list[time_index][site]
                use_vol = self.site_used_vol_list[time_index][site] + cache + st.vol
                if use_vol > self.site_bandwidth[site]:
                    continue
                center_cost = 0 if self.each_site_max_stream[time_index][site][
                                       stream_name] >= stream_vol else stream_vol
                site_cost = use_vol ** 2 / self.site_bandwidth[site]
                cost = center_cost * self.center_cost + site_cost
                if cost < min_cost:
                    min_cost = cost
                    most_reasonable_site = site
        return most_reasonable_site

    def match(self):
        self.initialize()
        for time_index in range(self.time_num):
            self.get_cache_list(time_index)
            self.match_time_index(time_index)

    def run(self):
        self.label_sites()
        self.match()
        self.judge()
        self.analyze()
        self.write_to_txt()

if __name__ == '__main__':
    method = PriorLearning()
    method.run()
    method.get_run_time()
    from judgement_tools.judgement import JudgeMent
    judge = JudgeMent('solution.txt')
    judge.run_judge()
