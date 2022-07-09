#!/usr/bin/env python
# -*- coding:utf-8 -*-
import platform
import os
import time
import csv
start_time = time.time()
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OS = platform.system()

if OS == 'Windows':
    root_path = 'C:\\Users\\80541\\Desktop\\CodeCraft_Final\\V3_ProriMethod'
    dataPath = root_path + os.sep + r"data"
    output_path = root_path + os.sep + 'output'
else:
    dataPath = os.sep + r"data"
    output_path = os.sep + r'output'


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
        leisure_clients: List[site] = List[client,...]
        leisure_sites: List[client] = List[site,...]
        site_keys: List[site,...]
        client_id_map:
        site_id_map:
    """

    site_keys = []
    site_names = []
    with open(dataPath+'/qos.csv') as f:
        datas = csv.reader(f)
        client_names = next(datas)[1:]
        leisure_clients = []
        client_id_map = {client: i for client, i in zip(client_names,range(len(client_names)))}
        site_id_map = {}
        site_id = -1
        leisure_sites = [[] for _ in client_names]
        for data in datas:
            site = data[0]
            site_id += 1
            site_id_map[site] = site_id
            leisure_clients.append([])
            for i in range(len(client_names)):
                client, qos = client_names[i], int(data[i + 1])
                if qos < qos_constraint:
                    leisure_clients[site_id].append(i)
                    leisure_sites[i].append(site_id)
            # if leisure_clients:
            site_keys.append(site_id)
            site_names.append(site)

    return leisure_clients, leisure_sites, site_keys, client_id_map, site_id_map, client_names, site_names


def load_bandwidth(site_id_map):
    """
    读取 site_bandwidth.csv

    Returns:
        site_bandwidth: dict[site] = int
        site_keys: List[site1,site2,site3,...]

    """
    site_bandwidth = [0 for _ in site_id_map.keys()]  # 节点带宽上限 key : 节点名  value : 带宽上限
    with open(dataPath + "/site_bandwidth.csv") as f:
        datas = csv.reader(f)
        _ = next(datas)
        for data in datas:
            site_bandwidth[site_id_map[data[0]]] = int(data[1])
    return site_bandwidth


def add_to_time_map(data, client_names, time_map, client_id_map, stream_names):
    """
    读取一行文件
    Args:
        data: List[]
        client_names: List[]
        time_map: Dict{client: {stream:int}}
        client_id_map:
        stream_names:
    """
    stream_name = data[1]
    stream_names.append(stream_name)
    nums = data[2:]
    for i, client in enumerate(client_names):
        time_map[client_id_map[client]].append(int(nums[i]))


def load_demand(client_id_map):
    """
    读取 demand.csv
    Args:
        client_id_map:
    Returns:
        client_names: List[client1, client2,...]
        client_demands: List[demand1,demand2,...]
        stream_names_list: List[List[]]
    """
    client_demands = []
    stream_names_list = []
    with open(dataPath + '/demand.csv') as f:
        datas = csv.reader(f)
        client_names = next(datas)[2:]
        data = next(datas)
        last_time = data[0]
        time_map = [[] for _ in client_names]
        stream_names = []
        add_to_time_map(data, client_names, time_map, client_id_map, stream_names)
        for data in datas:
            now_time = data[0]
            if now_time != last_time:
                client_demands.append(time_map)
                stream_names_list.append(stream_names)
                time_map = [[] for _ in client_names]
                stream_names = []
            add_to_time_map(data, client_names, time_map, client_id_map, stream_names)
            last_time = now_time
        client_demands.append(time_map)
        stream_names_list.append(stream_names)
    return client_names, client_demands, stream_names_list





if __name__ == '__main__':
    qos_constraint, base_cost, center_cost = load_config()
    leisure_clients, leisure_sites, site_keys, client_id_map, site_id_map, client_names, site_names = load_qos(qos_constraint)
    site_bandwidth = load_bandwidth(site_id_map)
    client_names, client_demands, stream_names_list = load_demand(client_id_map)

    print(client_demands[0][0])

