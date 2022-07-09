#!/usr/bin/env python
# -*- coding:utf-8 -*-
import platform
import os
import time
# import csv

start_time = time.time()
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OS = platform.system()

if OS == 'Windows':
    dataPath = root_path + os.sep + r"data"
    outputPath = root_path + os.sep + 'output'
else:
    dataPath = os.sep + r"data"
    outputPath = os.sep + r'output'


def split_line(s):
    '''
    处理一行数据，返回切分好的数组
    Args:
        s: 待处理数据
    '''
    result = []
    data = s.strip('\r\n').split(',')
    result.append(data[0])
    result.append(data[1])

    for vol in data[2:]:
        result.append(int(vol))
    return result


def load_config():
    """
    读取config.ini

    Returns:
        qos_constraint, base_cost, center_cost
    """

    with open(dataPath + '/config.ini') as f:
        lines = f.readlines()
        qos_constraint = int(lines[1].strip('\r\n').strip('qos_constraint='))
        base_cost = int(lines[2].strip('\r\n').strip('base_cost='))
        center_cost = float(lines[3].strip('\r\n').strip('center_cost='))
    return qos_constraint, base_cost, center_cost


def load_qos(qos_constraint):
    """
    读取qos.csv
    Args:
        qos_constraint: 时延限制
    Returns:
        leisure_clients: Dict[site] = List[client,...]
        leisure_sites: Dict[client] = List[site,...]
        site_keys: List[site,...]
    """
    leisure_clients = {}
    site_keys = []
    with open(dataPath+'/qos.csv') as f:
        # datas = csv.reader(f)
        datas = f.readlines()
        client_names = datas[0].strip('\r\n').split(',')[1:]
        leisure_sites = {client: [] for client in client_names}
        for data in datas[1:]:
            data = data.strip('\r\n').split(',')
            site = data[0]
            leisure_clients[site] = []
            # print(data)
            for i in range(len(client_names)):
                client, qos = client_names[i], int(data[i + 1])
                if qos < qos_constraint:
                    leisure_clients[site].append(client)
                    leisure_sites[client].append(site)
            if leisure_clients:
                site_keys.append(site)

    return leisure_clients, leisure_sites, site_keys


def load_bandwidth():
    """
    读取 site_bandwidth.csv

    Returns:
        site_bandwidth: dict[site] = int
        site_keys: List[site1,site2,site3,...]

    """
    site_bandwidth = {}  # 节点带宽上限 key : 节点名  value : 带宽上限
    with open(dataPath + "/site_bandwidth.csv") as f:
        # datas = csv.reader(f)
        datas = f.readlines()

        for data in datas[1:]:
            data = data.split(',')
            site_bandwidth[data[0]] = int(data[1])
    return site_bandwidth


def add_to_time_map(data, client_names, time_map):
    """
    读取一行文件
    Args:
        data: List[]
        client_names: List[]
        time_map: Dict{client: {stream:int}}

    """
    stream_name = data[1]
    nums = data[2:]
    for i in range(len(client_names)):
        num = int(nums[i])
        if num != 0:
            time_map[client_names[i]][stream_name] = num


def load_demand():
    """
    读取 demand.csv
    Returns:
        client_names: List[client1, client2,...]
        client_demands: List[demand1,demand2,...]
    """
    client_demands = []
    with open(dataPath + '/demand.csv') as f:
        datas = f.readlines()

        client_names = datas[0].strip('\r\n').split(',')[2:]
        data = split_line(datas[1])
        last_time = data[0]
        time_map = {client: {} for client in client_names}
        add_to_time_map(data,client_names,time_map)
        for data in datas[2:]:
            data = split_line(data)
            now_time = data[0]
            if now_time != last_time:
                client_demands.append(time_map)
                time_map = {client: {} for client in client_names}
                add_to_time_map(data, client_names, time_map)
            last_time = now_time
        client_demands.append(time_map)
    return client_names, client_demands

if __name__ == '__main__':
    site_bandwidth = load_bandwidth()
    qos_constraint, base_cost, center_cost = load_config()
    leisure_clients, leisure_sites, site_keys = load_qos(qos_constraint)
    print(time.time() - start_time)
    client_names, client_demands = load_demand()
    print(time.time() - start_time)


