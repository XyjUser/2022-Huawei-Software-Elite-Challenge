import math
import re
# from matplotlib import pyplot as plt
from .load_files import load_demand, output_path
from .settings import Settings

class JudgeMent(Settings):
    def __init__(self,output_file):
        super(JudgeMent, self).__init__()
        self.outputfile = output_path + f"/{output_file}"
        self.pattern = r'<(\w{1,2},[,\w]*)>'
        _, self.client_demands, self.stream_names_list = load_demand(self.client_id_map)

        self.num = len(self.client_names)
        self.obj = int(math.ceil(len(self.client_demands) * 0.95) - 1)

        self.site_info_list = {site: [0 for _ in range(self.time_num)]for site in self.site_id_map}
        self.center_cost_list = [{site: {} for site in self.site_id_map} for _ in range(self.time_num)]

        self.center_cost_all_list = []
        with open(self.outputfile) as f:
            self.datas = f.readlines()

    def run_judge(self):
        site_infos = {name: 0 for name in self.site_id_map}
        time_index = 0
        for i in range(1, len(self.datas) + 1):
            client, infos = self.prase_line(self.datas[i - 1])
            client_id = self.client_id_map[client]
            for info in infos:
                site, streams = info[0], info[1:]
                for stream in streams:
                    stream_id = self.stream_id_map[time_index][stream]
                    vol_cur = self.client_demands[time_index][client_id][stream_id]
                    if stream in self.center_cost_list[time_index][site]:
                        if vol_cur > self.center_cost_list[time_index][site][stream]:
                            self.center_cost_list[time_index][site][stream] = vol_cur
                    else:
                        self.center_cost_list[time_index][site][stream] = vol_cur

                    self.site_info_list[site][time_index] += self.client_demands[time_index][client_id][stream_id]
                    # print(site)
                    site_infos[site] += self.client_demands[time_index][client_id][stream_id]
                    if site_infos[site] > self.site_bandwidth[self.site_id_map[site]]:
                        print(f'第 {time_index} 组数据 边缘节点 {site} 超限 {site_infos[site]} / '
                              f'{self.site_bandwidth[self.site_id_map[site]]}')
                        return False
                    if self.client_demands[time_index][client_id][stream_id] == 0:
                        print(f'第 {time_index} 组数据 客户节点 {client} {stream}流多次分配')
                        return False
                    else:
                        self.client_demands[time_index][client_id][stream_id] = 0
            client_info = self.client_demands[time_index][client_id]
            unmatched_streams = [i for i in range(len(client_info)) if client_info[i] != 0]
            if len(unmatched_streams) != 0:
                print(f'第 {time_index} 组数据 客户节点 {client} 存在未分配流 {unmatched_streams}')
                return False

            if i % self.num == 0:
                site_infos = {name: 0 for name in self.site_id_map}
                time_index += 1

        if self.judge_again():
            print("分配合理")
            self.get_score()
            return True
        else:
            return False

    def judge_again(self):

        for time_index in range(1, self.time_num):
            sites_all = 0
            for site in self.site_id_map:
                site_last_vol = self.site_info_list[site][time_index - 1]
                self.site_info_list[site][time_index] += int(site_last_vol * 0.05)
                if self.site_info_list[site][time_index] > self.site_bandwidth[self.site_id_map[site]]:
                    print(f"时刻 {time_index} 边缘节点 {site} 加入上一时刻5%带宽后超限 {self.site_info_list[site][time_index]} / {self.site_bandwidth[self.site_id_map[site]]}")
                    return False
                temp = 0
                for stream in self.center_cost_list[time_index][site]:
                    temp += self.center_cost_list[time_index][site][stream]
                sites_all += temp
            self.center_cost_all_list.append(sites_all)
        return True

    def prase_line(self, s):
        client, infos = s.split(':')
        infos = re.findall(self.pattern, infos)
        infos = [info.split(',') for info in infos]
        return client, infos

    def get_score(self):
        sum = 0
        for site in self.site_id_map:
            self.site_info_list[site].sort()
            if self.site_info_list[site] == 0:
                continue
            w = self.site_info_list[site][self.obj]
            if w < self.base_cost:
                sum += self.base_cost
            else:
                sum += (w - self.base_cost)**2 / self.site_bandwidth[self.site_id_map[site]] + w
        # print(self.center_cost_all_list)
        self.center_cost_all_list.sort()
        center_score = self.center_cost_all_list[self.obj] * self.center_cost
        total_score = int(center_score + sum + 0.5)
        print(f"边缘节点得分为 {round(sum,2)} 中心节点得分为 {round(center_score,2)} 最终得分为: {total_score}")

if __name__ == '__main__':
    j = JudgeMent('solution.txt')
    # print(j.site_id_map.keys())
    j.run_judge()
