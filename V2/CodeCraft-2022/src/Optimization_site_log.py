#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@ Author：CJK_Monomania
@ Data：2022-05-17
"""

# from baseline import BaseLine
import sys

from new_try_2 import BaseLine
from rainbow_log import RainbowLog

''' 
@ 功能：
'''


class Optimization(BaseLine, RainbowLog):
    def __init__(self):
        super(Optimization, self).__init__()
        # ——————————————————————————————————————————————————————————————————————————————
        self.debug_flag = False
        if self.debug_flag:
            self.debug_info = {
                'from_site_list': [],
                'to_site_list': [],
                'choose_st_Vol_list': [],
                'changeVol_list': [],
                'base_score': 0,
                'end_score_list': [],
                'change_score_list': []
            }
        # ——————————————————————————————————————————————————————————————————————————————

        self.center_score_time = [0 for _ in range(self.time_num)]
        # 记录每一时刻 对应 site被分配到的stream
        self.reuslt_time_site_stream_List = [
            {site: {'streamList': {}} for site in self.site_keys} for timeIdx in range(self.time_num)
        ]
        # 记录每一时刻 对应 site 被分配到的stream中最大及第二大的流的流量
        self.each_site_max_second_stream = [
            [
                [
                    [0, 0] for _ in range(len(self.stream_names_list[time_index]))
                ] for _ in self.site_keys
            ] for time_index in range(self.time_num)
        ]

    def opt_func(self):

        # 获取各个site的95点相关信息
        self.site_95time_vol_streams_map = self.__get_site_95time_vol_streams_map()
        self.log_OKBLUE('Start Handle Site List: ' + f'{list(self.site_95time_vol_streams_map.keys())}')
        self.log_OKBLUE('Site List Num: ' + f'{len(list(self.site_95time_vol_streams_map.keys()))}')
        for site in self.site_95time_vol_streams_map.keys():
            self.opt_for_one_site(site)

    def opt_for_one_site(self, site):
        """把最大的优化掉"""
        # 找到site对应的最大流
        time95 = self.site_95time_vol_streams_map[site]['time95']
        streamMap = self.site_95time_vol_streams_map[site]['streamList_95']
        maxStreamId = self.find_maxVol_streamId(streamMap)
        needChangeStream = streamMap[maxStreamId]
        # 从最大流中切入，找到最优的目标site
        targetSite = self.__choose_site(site, time95, needChangeStream)
        # 能找到则移动
        if targetSite:
            self.log_OKGREEN(f'OK: time95:{time95} site_from:{site} site_to:{targetSite} stream-{needChangeStream}')
            self.move_stream(needChangeStream, site, targetSite, time95)
            # if not self.tmp_juge():
            #     sys.exit()
        else:
            self.log_HEADER(f'OK: time95:{time95} site_from:{site} site_to: None')

    def __choose_site(self, site, time_index, needChangeStream):
        # 获取可用列表
        siteList = self.get_leisure_site(needChangeStream.client)
        # 计算源site减少目标流后，改变的容量
        change_vol_site_from = self.siteFrom_change_vol(needChangeStream, site, time_index)
        choose_site = None
        max_change_Vol = 0
        change_Vol = 0
        for site_t in siteList:
            if site_t == site:
                continue
            if self.is_add_legal(needChangeStream.vol, site_t, time_index):
                """首先要保证合法"""
                # 计算目标site减少目标流后，改变的容量
                change_vol_site_to = self.siteTo_change_vol(needChangeStream, site_t, time_index)
                change_center = self.center_change_vol(site, site_t, needChangeStream, time_index)
                change_Vol = (change_vol_site_from + change_vol_site_to + change_center)
                if change_Vol < 0:
                    if change_Vol < max_change_Vol:
                        max_change_Vol = change_Vol
                        choose_site = site_t
                        # return choose_site
        if self.debug_flag:
            self.debug_info['changeVol_list'].append(max_change_Vol)
        return choose_site

    def find_maxVol_streamId(self, streamMap: dict):
        maxStreamId = -1
        maxStreamVol = -1
        for st in streamMap.values():
            if st.vol > maxStreamVol:
                maxStreamId = st.id
                maxStreamVol = st.vol
        return maxStreamId

    def __get_site_95time_vol_streams_map(self):
        site_95time_vol_streams_map = {}
        self.site_Vol_sorted_Map = {}
        for site_name, site in self.site_id_map.items():
            arr = []
            for time_index in range(self.time_num):
                arr.append([time_index, self.site_used_vol_list[time_index][site]])
            arr.sort(key=lambda k: k[1])
            time94 = arr[self.object_position - 1][0]
            time95 = arr[self.object_position][0]
            time96 = arr[self.object_position + 1][0]
            tmpMap = {
                "time94": time94,
                "time95": time95,
                "time96": time96,
                "vol94": arr[self.object_position - 1][1],
                "vol95": arr[self.object_position][1],
                "vol96": arr[self.object_position + 1][1],
                "streamList_94": self.reuslt_time_site_stream_List[time94][site]['streamList'],
                "streamList_95": self.reuslt_time_site_stream_List[time95][site]['streamList'],
                "streamList_96": self.reuslt_time_site_stream_List[time96][site]['streamList'],
            }
            if tmpMap['vol95'] > 0 and len(tmpMap['streamList_95']) >= 1:
                site_95time_vol_streams_map[site] = tmpMap
            self.site_Vol_sorted_Map[site] = arr
        return site_95time_vol_streams_map

    def init(self):
        for time_index in range(self.time_num):
            for st in self.client_demands[time_index]:
                self.reuslt_time_site_stream_List[time_index][st.site]['streamList'].update({st.id: st})

                maxVol = self.each_site_max_second_stream[time_index][st.site][st.stream][0]
                secondVol = self.each_site_max_second_stream[time_index][st.site][st.stream][1]
                if st.vol > maxVol:
                    self.each_site_max_second_stream[time_index][st.site][st.stream][1] = \
                        self.each_site_max_second_stream[time_index][st.site][st.stream][0]
                    self.each_site_max_second_stream[time_index][st.site][st.stream][0] = st.vol
                elif st.vol > secondVol:
                    self.each_site_max_second_stream[time_index][st.site][st.stream][1] = st.vol
        self.init_center_score()
        self.center_cost_pos = self.center_score_index[self.object_position]

    def init_center_score(self):
        for site in self.site_keys:
            for time_index in range(self.time_num):
                self.center_score_time[time_index] += sum(self.each_site_max_second_stream[time_index][site][0])
        self.center_score_index = sorted(range(self.time_num), key=lambda k: self.center_score_time[k])

    def run(self, times=100, time_limit=251):
        self.handle_demand()
        self.percent95_distribution()
        self.init()
        for i in range(times):
            self.opt_func()
            if self.get_run_time() > time_limit:
                break
        # 优化边缘节点
        self.write_to_txt()

    def test_run(self, times=1):
        self.handle_demand()
        self.percent95_distribution()

        self.init()

        score_site, score_center, end_score = self.tmp_juge()
        self.log_OKBLUE(f'score_site: {score_site} score_center: {score_center} end_score: {end_score}')
        if self.debug_flag:
            self.debug_info['base_score'] = end_score
            self.debug_info['end_score_list'].append(end_score)

        for i in range(times):
            self.log_OKBLUE('-' * 80)
            self.log_OKBLUE(f'opt_func: No{i + 1} Start')

            self.opt_func()

            score_site, score_center, end_score = self.tmp_juge()
            if self.debug_flag:
                self.log_OKBLUE(
                    f'score_site: {score_site} score_center: {score_center} end_score: {end_score} base_score:{self.debug_info["base_score"]}')
                self.debug_info['change_score_list'].append(end_score - self.debug_info['end_score_list'][-1])
                self.debug_info['end_score_list'].append(end_score)
            self.log_OKBLUE('-' * 80)

        if not self.judge():
            self.log_ERROR("95分配不合法")
            return False
        self.analyze()
        if self.debug_flag:
            print(self.debug_info)
        self.write_to_txt()

        return True

    def is_add_legal(self, vol, site, time_index):
        """
        当前节点增加流是否合法
        """

        while time_index < self.time_num and vol > 0:
            if self.site_used_vol_list[time_index][site] + vol > self.site_bandwidth[site]:
                return False
            last_cache = int(self.site_used_vol_list[time_index][site] * 0.05)
            new_cache = int((self.site_used_vol_list[time_index][site] + vol) * 0.05)

            vol = new_cache - last_cache
            time_index += 1
        return True

    def center_change_vol(self, site_from, site_to, st, time_index):
        """
        移动该流对中心成本的变化，降低了多少分
        """
        change_vol = 0
        if st.vol == self.each_site_max_second_stream[time_index][site_from][st.stream][0]:
            change_vol += self.each_site_max_second_stream[time_index][site_from][st.stream][1] - st.vol

        if st.vol > self.each_site_max_second_stream[time_index][site_to][st.stream][0]:
            change_vol += st.vol - self.each_site_max_second_stream[time_index][site_to][st.stream][0]

        vol_new = self.center_score_time[time_index] + change_vol
        vol_95 = self.center_score_time[self.center_cost_pos]
        vol_94 = self.center_score_time[self.center_score_index[self.object_position - 1]]
        vol_96 = self.center_score_time[self.center_score_index[self.object_position + 1]]

        if self.center_score_time[time_index] > self.center_score_time[self.center_cost_pos]:
            if vol_new < vol_95:
                if vol_new > vol_94:
                    return vol_new - vol_95
                else:
                    return vol_94 - vol_95
            return 0
        elif self.center_score_time[time_index] == self.center_score_time[self.center_cost_pos]:
            if change_vol < 0:
                return max(vol_new, vol_94) - vol_95
            else:
                return min(vol_new, vol_96) - vol_95
        else:
            if vol_new <= vol_95:
                return 0
            else:
                return min(vol_new, vol_96) - vol_95

    def tmp_juge(self):
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
        # print(f"边缘节点得分为 : {round(sum_score, 2)}")
        score_site = round(sum_score, 2)

        # 中心节点
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
        # print(
        #     f'中心节点的得分计算时刻为: {center_record_time} 得分为: {round(center_score_time[center_record_time] * self.center_cost, 2)}')
        score_center = round(center_score_time[center_record_time] * self.center_cost, 2)
        end_score = score_site + score_center
        return score_site, score_center, end_score

    def siteTo_change_vol(self, st, site_to, time_index):
        """
           移动该流对site_to边缘节点的成本变化，变化了多少分
        """
        if site_to not in self.site_95time_vol_streams_map.keys():
            # self.log_WARNING(
            #     '=' * 20 + f'{site_to}-{self.id_site_map[site_to]} not in site_95time_vol_streams_map' + '=' * 20)
            return 0 - st.vol
        # time95 = self.site_95time_vol_streams_map[site_to]['time95']
        # vol_new = self.site_used_vol_list[time_index][site_to] + st.vol
        # vol_96 = self.site_95time_vol_streams_map[site_to]['vol96']
        # vol_95 = self.site_95time_vol_streams_map[site_to]['vol95']
        time95 = self.site_Vol_sorted_Map[site_to][self.object_position][0]
        vol_new = self.site_used_vol_list[time_index][site_to] + st.vol
        vol_96 = self.site_Vol_sorted_Map[site_to][self.object_position + 1][1]
        vol_95 = self.site_Vol_sorted_Map[site_to][self.object_position][1]

        change_vol = 0
        if self.site_used_vol_list[time_index][site_to] > vol_95:
            if time_index < time95:
                return st.vol ** (time95 - time_index)
            return 0
        elif self.site_used_vol_list[time_index][site_to] == vol_95:
            return min(vol_new, vol_96) - vol_95
        else:
            if time_index < time95:
                change_vol += int(st.vol ** (time95 - time_index))
            if vol_new < vol_95 + change_vol:
                return change_vol
            else:
                return min(vol_new, vol_96) - vol_95

    def siteFrom_change_vol(self, st, site_from, time_index):
        """
           移动该流对site_from边缘节点的成本变化，变化了多少分
        """
        vol_new = self.site_used_vol_list[time_index][site_from] - st.vol
        vol_94 = self.site_Vol_sorted_Map[site_from][self.object_position - 1][1]
        vol_95 = self.site_Vol_sorted_Map[site_from][self.object_position][1]

        if vol_new > vol_94:
            return vol_new - vol_95
        else:
            return vol_94 - vol_95

    def update_stream_cache(self, site, time_index, last_vol):
        """
        更新一个流后，更新对节点的缓存有影响的时刻
        """
        new_vol = self.site_used_vol_list[time_index][site]
        add_cache = int(new_vol * 0.05) - int(last_vol * 0.05)
        time_index += 1
        while time_index < self.time_num and add_cache != 0:
            last_vol = self.site_used_vol_list[time_index][site]
            self.site_used_vol_list[time_index][site] += add_cache
            add_cache = int(self.site_used_vol_list[time_index][site] * 0.05) - int(last_vol * 0.05)
            time_index += 1

    def move_stream(self, st, from_site, to_site, time_index):
        st.site = to_site
        stream_vol = st.vol
        if self.debug_flag:
            self.debug_info['from_site_list'].append(from_site)
            self.debug_info['to_site_list'].append(to_site)
            self.debug_info['choose_st_Vol_list'].append(stream_vol)

        del self.reuslt_time_site_stream_List[time_index][from_site]['streamList'][st.id]
        self.reuslt_time_site_stream_List[time_index][to_site]['streamList'].update({st.id: st})

        last_vol = self.site_used_vol_list[time_index][from_site]
        self.site_used_vol_list[time_index][from_site] -= stream_vol
        self.site_Vol_sorted_Map[from_site][time_index][1] -= stream_vol
        self.site_Vol_sorted_Map[from_site].sort(key=lambda k: k[1])

        self.update_stream_cache(from_site, time_index, last_vol)

        last_vol = self.site_used_vol_list[time_index][to_site]
        self.site_used_vol_list[time_index][to_site] += stream_vol
        self.site_Vol_sorted_Map[to_site][time_index][1] += stream_vol
        self.site_Vol_sorted_Map[to_site].sort(key=lambda k: k[1])

        self.update_stream_cache(to_site, time_index, last_vol)

        if self.each_site_max_second_stream[time_index][from_site][st.stream][0] == stream_vol:
            s_vol, nd_vol = self.find_max_2nd_stream(time_index, from_site, st.stream)
            self.each_site_max_second_stream[time_index][from_site][st.stream][0] = s_vol
            self.each_site_max_second_stream[time_index][from_site][st.stream][1] = nd_vol
            self.center_score_time[time_index] -= stream_vol - s_vol

        if self.each_site_max_second_stream[time_index][to_site][st.stream][0] < stream_vol:
            self.center_score_time[time_index] += stream_vol - \
                                                  self.each_site_max_second_stream[time_index][to_site][st.stream][0]
            self.each_site_max_second_stream[time_index][to_site][st.stream][1] = \
                self.each_site_max_second_stream[time_index][to_site][
                    st.stream][0]
            self.each_site_max_second_stream[time_index][to_site][st.stream][0] = stream_vol

    def find_max_2nd_stream(self, time_index, site, stream):
        max_stream = 0
        second_stream = 0
        siteMap = dict(self.reuslt_time_site_stream_List[time_index][site]['streamList'])
        for st in siteMap.values():
            if st.stream == stream:
                if st.vol > max_stream:
                    second_stream = max_stream
                    max_stream = st.vol
        return max_stream, second_stream


if __name__ == '__main__':
    method = Optimization()
    # flag = method.test_run(10)
    method.run(100)
    # print(method.get_run_time())
    # if flag:
    #     from judgement_tools.judgement import JudgeMent
    #
    #     judge = JudgeMent('solution.txt')
    #     judge.run_judge()

    from judgement_tools.judgement import JudgeMent

    judge = JudgeMent('solution.txt')
    judge.run_judge()
