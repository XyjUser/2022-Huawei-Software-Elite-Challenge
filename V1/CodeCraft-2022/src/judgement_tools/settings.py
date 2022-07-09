#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import time

from load_files import start_time, load_bandwidth, load_qos, load_config, \
    load_demand, output_path


class Settings:

    qos_constraint, base_cost, center_cost = load_config()
    leisure_clients, leisure_sites, site_keys, client_id_map, \
    site_id_map, client_names, site_names = load_qos(qos_constraint)
    site_bandwidth = load_bandwidth(site_id_map)




    def __init__(self):
        _, self.client_demands, self.stream_names_list = load_demand(self.client_id_map)
        self.time_num = len(self.client_demands)
        self.client_all_demand = self.load_all_demand()
        self.site_sum_list, self.demand_sum_list = self.load_statistic_lists()
        # self.site_keys = sorted(self.site_keys, key=lambda k: self.site_bandwidth[k])
        self.stream_id_map = [{stream: i for i, stream in enumerate(self.stream_names_list[time_index])}
                              for time_index in range(self.time_num)]
        # new_site_keys = [site for site in self.site_keys if len(self.get_leisure_client(site)) > 0]
        # self.site_keys = new_site_keys



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
            for client in range(len(self.client_names)):
                client_all_demand[timeIndex][client] = sum(demand[client])
        return client_all_demand

    def load_statistic_lists(self):
        """
        加载 demand_sum_list和site_sum_list
        Returns:
            site_sum_list:
            demand_sum_list:
        """
        site_sum_list = [[0 for _ in range(self.time_num)] for _ in self.site_keys]
        demand_sum_list = [0 for _ in range(self.time_num)]
        for time_index in range(self.time_num):
            for client in range(len(self.client_names)):
                for site in self.get_leisure_site(client):
                    site_sum_list[site][time_index] += self.client_all_demand[time_index][client]
                demand_sum_list[time_index] += self.client_all_demand[time_index][client]
        return site_sum_list, demand_sum_list

    def remove_demand(self, client, vol, time_index):
        """
            删除demand_sum_list和site_sum_list 对应客户节点client的需求量vol
            Args:
                settings: site_sum_list 所属的实例
                client: 客户节点名
                vol:   待更新的量
                time_index:  时刻
            """
        for site in self.get_leisure_site(client):
            self.site_sum_list[site][time_index] -= vol
        self.demand_sum_list[time_index] -= vol

    def write_to_txt(self, output):
        """
        将分配方案按要求格式写入文件
        Args:
            output: 输出信息

        Returns:

        """
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with open(output_path + os.sep + "solution.txt", 'w') as f:

            for j in range(len(output)):
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
        Returns:

        """
        print("运行时间为: {}".format(time.time() - start_time))

if __name__ == '__main__':
    s = Settings()
    print(time.time() - start_time)
