#!/usr/bin/env python
# -*- coding:utf-8 -*-
import math
import os
import time

from load_files import start_time, load_bandwidth, load_qos, load_config, \
    load_demand, output_path


def demand_sort(time_num, client_demands):
    for time_index in range(time_num):
        client_demands[time_index].sort(key=lambda k: k.vol, reverse=True)


class Settings:
    qos_constraint, base_cost, center_cost = load_config()
    leisure_clients, leisure_sites, site_keys, client_id_map, site_id_map, client_names, site_names = load_qos(
        qos_constraint)
    id_site_map = {site: site_name for site_name, site in site_id_map.items()}
    site_bandwidth = load_bandwidth(site_id_map)
    _, client_demands, stream_names_list = load_demand(client_id_map)
    time_num = len(client_demands)
    demand_sort(time_num, client_demands)
    object_position = int(math.ceil(0.95 * time_num) - 1)

    def __init__(self):

        self.site_streams_vol_infos = [[[0, 0, 0] for _ in range(self.time_num)] for _ in self.site_keys]
        self.load_site_streams_vol_infos()

    def load_site_streams_vol_infos(self):
        for time_index in range(self.time_num):
            for st in self.client_demands[time_index]:
                vol = st.vol
                for site in self.get_leisure_site(st.client):
                    self.site_streams_vol_infos[site][time_index][0] += vol
                    if vol > self.base_cost:
                        self.site_streams_vol_infos[site][time_index][1] += vol
                        self.site_streams_vol_infos[site][time_index][2] += 1

    def remove_site_vol_infos(self, time_index, st_list):
        for st in st_list:
            vol = st.vol
            for site in self.get_leisure_site(st.client):
                self.site_streams_vol_infos[site][time_index][0] -= vol
                if vol > self.base_cost:
                    self.site_streams_vol_infos[site][time_index][1] -= vol
                    self.site_streams_vol_infos[site][time_index][2] -= 1

    def get_leisure_site(self, client):
        """
        获取客户节点对应的空闲节点
        Args:
            client: 客户节点名称
        Returns:
             List[] 满足时延限制的边缘节点列表
        """
        return self.leisure_sites[client]

    def get_leisure_client(self, site):
        """
        获取边缘节点对应的空闲客户节点
        Args:
            site: 边缘节点名称
        Returns:
             List[] 满足时延限制的客户节点列表
        """
        return self.leisure_clients[site]

    def load_all_demand(self):
        """
        计算每个时刻每个客户节点总的需求量
        """
        client_all_demand = [[0 for _ in self.client_names] for _ in range(self.time_num)]
        for timeIndex in range(self.time_num):
            demand = self.client_demands[timeIndex]
            for stream in demand:
                client_all_demand[timeIndex][stream.client] += stream.vol
        return client_all_demand

    def gen_output(self):
        output = [{client: {} for client in self.client_names} for _ in range(self.time_num)]
        for time_index in range(self.time_num):
            for st in self.client_demands[time_index]:
                if st.vol == 0:
                    continue
                stream_name = self.stream_names_list[time_index][st.stream]
                site_name = self.site_names[st.site]
                client_name = self.client_names[st.client]
                try:
                    output[time_index][client_name][site_name].append(stream_name)
                except:
                    output[time_index][client_name][site_name] = [stream_name]
        return output

    def write_to_txt(self, time_choose_sites):
        """
        将分配方案按要求格式写入文件
        """
        output = self.gen_output()
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with open(output_path + os.sep + "solution.txt", 'w') as f:
            for j in range(len(output)):
                # add time_choose_sites

                if j != 0:
                    for idx, choose_site in enumerate(time_choose_sites[j].keys()):
                        # if len(time_choose_sites[j]) != 20:
                        #     print("len(time_choose_sites[j]) != 20")
                        if idx != 19:
                            f.write(self.id_site_map[choose_site] + ',')
                        else:
                            f.write(self.id_site_map[choose_site] + '\n')

                out_datas = output[j]
                clients = list(out_datas.keys())
                for z in range(len(clients)):
                    client = clients[z]
                    f.write(client + ":")
                    sites = list(out_datas[client].keys())
                    for i in range(len(sites)):
                        f.write('<' + sites[i])
                        for stream in out_datas[client][sites[i]]:
                            f.write(',' + stream)
                        if i == len(sites) - 1:
                            f.write('>')
                        else:
                            f.write('>,')
                    if j == len(output) - 1 and z == len(clients) - 1:
                        pass
                    else:
                        f.write('\n')

    def get_run_time(self):
        """
        打印程序运行耗时
        """
        # print("运行时间为: {}".format(time.time() - start_time))
        return time.time() - start_time


if __name__ == '__main__':
    s = Settings()
    print("load data time:", time.time() - start_time)
