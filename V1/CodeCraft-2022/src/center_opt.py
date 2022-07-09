#!/usr/bin/env python
# -*- coding:utf-8 -*-
from baseline import merge_streams, BaseLine

class CenterOpt(BaseLine):
    def __init__(self):
        super(CenterOpt, self).__init__()
        self.max_stream_of_site = [[[0 for _ in self.stream_names_list[time_index]] for _ in self.site_keys]
                                   for time_index in range(self.time_num)]
        self.max_vol_of_sites = [5000 for _ in self.site_keys]

    def update_output(self, client, stream_id, vol, site, time_index):
        """
        更新信息
        Args:
            client:
            stream_id:
            vol:
            site:
            time_index:

        Returns:

        """
        super(CenterOpt, self).update_output(client, stream_id, vol, site, time_index)

        if self.max_stream_of_site[time_index][site][stream_id] < vol:
            self.max_stream_of_site[time_index][site][stream_id] = vol

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
            site = self.get_min_score_site(client, vol, stream, time_index)
            self.update_output(client, stream, vol, site, time_index)
            if self.site_used_vol_list[time_index][site] > self.max_vol_of_sites[site]:
                self.max_vol_of_sites[site] = self.site_used_vol_list[time_index][site]

    def get_min_score_site(self, client, vol, stream,time_index):
        """
        获取当前时刻所选择的流可以分配的边缘节点中增长最慢的边缘节点
        Args:
            client:
            vol:
            stream:
            time_index:

        Returns:

        """
        sites = self.get_leisure_site(client)
        target_site = None
        min_score = 1000000
        min_center_score = 100000
        flag = False
        for site in sites:
            use_vol = self.site_used_vol_list[time_index][site] + vol
            if use_vol <= self.site_bandwidth[site]:
                score, err = self.get_one_site_err(use_vol, site)
                if not flag and err < 0:
                    if score < min_score:
                        min_score = score
                        target_site = site

                elif err > 0:
                    flag = True
                    center_score = self.choose_center_cost_min_site(stream, vol, site, time_index)
                    if center_score < min_center_score:
                        min_center_score = center_score
                        target_site = site

        return target_site

    def get_one_site_err(self, use_vol, site):
        """
        获取若将某个流放入某个节点的成本增长值
        Args:
            use_vol:
            vol:
            site:
            stream:
            time_index:
        Returns:
        """
        # total_vol = self.site_used_vol_list[time_index][site]
        # cost_err = (use_vol + total_vol) * (use_vol - total_vol) / self.site_bandwidth[site]
        # center_err = max(0, vol - self.max_stream_of_site[time_index][site][stream])
        # return cost_err + center_err
        return use_vol**2 / self.site_bandwidth[site], self.max_vol_of_sites[site] - use_vol

    def choose_center_cost_min_site(self, stream, vol, site, time_index):
        if vol > self.max_stream_of_site[time_index][site][stream]:
            return vol - self.max_stream_of_site[time_index][site][stream]
        return 0

if __name__ == '__main__':
    method = CenterOpt()
    method.run()
    method.get_run_time()
    method.judge()
    from judgement_tools import JudgeMent
    judge = JudgeMent()
    judge.run_judge()
