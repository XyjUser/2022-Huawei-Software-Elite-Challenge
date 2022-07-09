import math
import time
from load_files import load_demand, start_time



# self.client_demands = copyDemand()
class Optimization():
    def __init__(self, base_line):
        self.bs = base_line
        self.site_keys = base_line.site_keys
        self.time_num = base_line.time_num
        _, self.client_demands, _ = load_demand(base_line.client_id_map)
        self.stream_id_map = base_line.stream_id_map
        self.object_positon = base_line.object_positon
        self.site_used_vol_list = base_line.site_used_vol_list
        self.draw_site_info = {site: [] for site in base_line.site_keys}
        self.output = base_line.output
        self.datas = [{site: {} for site in base_line.site_keys} for _ in self.output]
        for time_index in range(self.time_num):
            for client in self.output[time_index]:
                for site in self.output[time_index][client]:
                    self.datas[time_index][site][client] = self.output[time_index][client][site]
        
        self.site_datas = [[] for site in self.site_keys]
        self.site_index = [[] for site in self.site_keys]
        for site_used_vol in self.site_used_vol_list:
            for site in self.site_keys:
                self.site_datas[site].append(site_used_vol[site])
        for site in self.site_keys:
            self.site_index = sorted(range(len(self.site_datas[site])), key=lambda k: self.site_datas[site][k])


    def getClientVol(self,client,site,timeIndex):
        streams = [self.stream_id_map[st] for st in self.datas[timeIndex][site][client]]
        vol = 0
        for stream in streams:
            vol += self.client_demands[timeIndex][client][stream]
        return vol

    def sortIndex(self,site):
        self.site_index[site] = sorted(range(len(self.site_datas[site])), key=lambda k: self.site_datas[site][k])

    def getMostSuitableSite(self,clients, timeIndex, siteSelf):
        '''
            选取最优的site 和 client 用于更新
            :param clients: 候选客户点
            :param timeIndex: 当前时间点
            :param siteSelf:      当前边缘节点
            :return: client: 选中的客户点
            :return: site: 选中的site
            :return: vol: 选中的site的余量
            :return: flag: 是否找到满足的点
            '''
        maxVol = 0
        maxSite = siteSelf
        maxClient = 0
        for client in clients:
            clientVol = self.getClientVol(client,siteSelf,timeIndex)
            sites = getLeisureSite(client)
            for site in sites:
                if site == siteSelf:
                    continue
                totalIndex = self.site_index[site].index(timeIndex)
                siteVol = siteBandwidth[site] - self.site_datas[site][timeIndex]
                if totalIndex > self.objectPositon:  # 当前为尾部节点，则返回尾部节点剩余容量
                    vol = min(clientVol,siteVol)
                    if vol > maxVol:
                        maxVol = vol
                        maxSite = site
                        maxClient = client

                elif totalIndex < self.objectPositon:  # 若在95点前面，则返回在不影响95点值的前提下最多新增容量
                    thresholdIndex = self.site_index[site][self.objectPositon]
                    vol = self.site_datas[site][thresholdIndex] - \
                          self.site_datas[site][timeIndex]
                    vol = min(clientVol,vol)
                    if vol > maxVol:
                        maxVol = vol
                        maxSite = site
                        maxClient = client
                else:
                    siteToVol = self.site_datas[site][timeIndex]
                    siteFromVol = self.siteSeqByTime[siteSelf]['datas'][timeIndex]

                    if siteFromVol >= siteToVol and siteBandwidth[siteSelf] <= siteBandwidth[site]:
                        # print(siteFromVol, siteToVol)
                        lastVolIndex = self.siteSeqByTime[siteSelf]['index'][self.objectPositon - 1]
                        listVol = self.siteSeqByTime[siteSelf]['datas'][lastVolIndex]
                        maxChangeVol = siteFromVol - listVol
                        vol = siteFromVol - (siteToVol + siteFromVol) // 2
                        vol = min(siteVol,clientVol,vol,maxChangeVol)
                        if vol > maxVol:
                            maxVol = vol
                            maxSite = site
                            maxClient = client

        if maxVol > 0:
            return True, maxVol, maxSite, maxClient
        return False,maxVol, maxSite, maxClient


    def optimizeOnce(self,site):
        '''
        优化一个节点
        :param site: 节点名
        :return: 优化前后的值
        '''
        timeIndex = self.site_index[site][self.objectPositon]  # 获取95点的索引
        pre = self.site_datas[site][timeIndex]

        if self.site_datas[site][timeIndex] > base_cost:
            clients = list(self.datas[timeIndex][site].keys())  # 获取节点包含的客户点
            flag,vol,siteTo,client = self.getMostSuitableSite(clients, timeIndex, site)  # 获取用于更新的边缘节点
            if flag:
                self.update(site,siteTo,client,timeIndex,vol)

        timeIndex = self.site_index[site][self.objectPositon]
        aft = self.site_datas[site][timeIndex]

        return pre, aft


    def update(self,siteFrom,siteTo,client,timeIndex,vol):
        streamsFrom = self.outputList[timeIndex][client][siteFrom]

        if siteTo not in self.outputList[timeIndex][client].keys():
            self.outputList[timeIndex][client][siteTo] = []
        if client not in self.datas[timeIndex][siteTo].keys():
            self.datas[timeIndex][siteTo][client] = self.outputList[timeIndex][client][siteTo]

        clients = self.client_demands[timeIndex]
        streams = {stream:clients[client][stream] for stream in streamsFrom}
        useStreams,useVol = self.chooseStreams(streams,vol)
        if not useStreams:
            return

        while useStreams:
            index = streamsFrom.index(useStreams[0])
            del self.outputList[timeIndex][client][siteFrom][index]
            # print(len(self.outputList[timeIndex][client][siteFrom]),len(self.datas[timeIndex][siteFrom][client]))
            self.outputList[timeIndex][client][siteTo].append(useStreams[0])
            del useStreams[0]


        self.siteSeqByTime[siteFrom]['datas'][timeIndex] -= useVol
        self.siteInfoSetList[timeIndex][siteFrom] += useVol

        self.siteSeqByTime[siteTo]['datas'][timeIndex] += useVol
        self.siteInfoSetList[timeIndex][siteTo] -= useVol

        self.sortIndex(siteFrom)
        if self.siteSeqByTime[siteTo]['index'].index(timeIndex) <= self.objectPositon:
            self.sortIndex(siteTo)

    def optimize(self,maxTime):
        time_span = time.time() - start_time

        # cnt = 1
        # startScore = self.GetScore()
        # LastScore = startScore

        while time_span < maxTime:
            objectPositonList = [
                self.site_datas[site][self.objectPositon] - self.site_datas[site][self.objectPositon - 1]
                for site in siteKeys]
            # # objectPositonList = [self.site_datas[site][self.objectPositon] for site in siteKeys]
            # objectPositonListIndex = sorted(range(len(objectPositonList)), key=lambda k: objectPositonList[k],
            #                                 reverse=True)

            objectPositonListIndex = sorted(range(len(siteKeys)),key=lambda k:siteBandwidth[siteKeys[k]])

            for index in objectPositonListIndex:
                site = siteKeys[index]
                pre, aft = self.optimizeOnce(site)



            #     self.drawSiteInfo[site].append(self.getOneScore(aft, site))
            # if cnt % 10 == 0 :
            #     totalScore = self.GetScore()
            #     changeVol = LastScore - totalScore
            #     LastScore = totalScore
            #     print("第{}轮优化,当前得分: {} 本轮优化: {} 已优化: {}".format(cnt
            #                                                     , totalScore, changeVol,startScore - totalScore,))
            #     if changeVol == 0:
            #         break
            # cnt += 1


            time_span = time.time() - start_time


    def GetScore(self):
        self.siteinfos = {}
        score = 0
        for site in siteKeys:
            siteVols = [siteBandwidth[site] - self.siteInfoSetList[k][site] for k in range(timeNum)]
            self.siteinfos[site] = siteVols
            siteVols.sort()
            if siteVols[-1] == 0:
                continue
            vol = siteVols[self.objectPositon]
            if vol <= base_cost:
                score += base_cost
            else:
                score += vol + (vol - base_cost)**2 / siteBandwidth[site]
        # print("该方案最终得分为: {}".format(int(score + 0.5)))
        return int(score + 0.5)

    def getOneScore(self,vol,site):
        if vol > base_cost:
            vol = (vol - base_cost)**2 / siteBandwidth[site] + vol
        else:
            vol = base_cost
        return vol
    def getErr(self,pre,aft,site):
        return int(self.getOneScore(pre,site) - self.getOneScore(aft,site))

    def chooseStreams(self,streams,V):
        '''
        选择最合适的流去填充额定的容量
        :param streams: 可选流 ：{stream:vol}
        :param V:       额定容量
        :return suitableStreams,vol: 是否存在合理分配,最合适的流,与剩余容量
        '''
        streamKeys = list(streams.keys())
        totalVol = 0
        suitableStreams = []
        streamIndexs = sorted(range(len(streamKeys)),key = lambda k:streams[streamKeys[k]],reverse=True)
        for index in streamIndexs:
            stream = streamKeys[index]
            if totalVol + streams[stream] <= V:
                suitableStreams.append(stream)
                totalVol += streams[stream]
            else:
                # return suitableStreams,totalVol
                continue
        return suitableStreams,totalVol

    def drawSites(self):
        from matplotlib import pyplot as plt

        plt.figure(figsize=(12,8),dpi=600)
        for site in siteKeys:
            plt.plot(self.drawSiteInfo[site],label=site)
        # plt.legend(siteKeys)
        plt.title("Each site change curve",fontsize=18)
        plt.xlim(0,len(self.drawSiteInfo[siteKeys[0]]))
        plt.ylim(0, 1000)
        plt.show()