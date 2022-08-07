"""
scrape hot stocks
"""

import json,time,os,math
from datetime import datetime
import pandas as pds
import requests as rq
from tangying.common import getSqliteEngine
import jqdatasdk as jq

class HotRankStocks:
    def __init__(self):
        self.url = "https://eq.10jqka.com.cn/open/api/hot_list/v1/hot_stock/a/hour/data.txt"
        self.stocks_head = ['Name','Rank','Change','Concept','Popularity','Express','Time']
        self.date = time.strftime('%m-%d',time.localtime(time.time()))
        self.header ={
            'Host': 'eq.10jqka.com.cn',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G9810 Build/QP1A.190711.020; wv) \
            AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 \
            Hexin_Gphone/10.13.02 (Royal Flush) hxtheme/0 innerversion/G037.08.462.1.32 userid/-640913281 hxNewFont/1',
            'Referer': 'https://eq.10jqka.com.cn/webpage/ths-hot-list/index.html?showStatusBar=true',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'X-Requested-With': 'com.hexin.plat.android'
        }

    #获取热度榜所有股票，返回dataFrame
    def getHotStocksDataFrame(self):
        rsp = rq.get(url=self.url,headers=self.header)
        rsp_body = rsp.json()
        hot_list = parseHotStockPackage(rsp_body)
   
        #返回股票热度榜表单
        return pds.DataFrame(data=hot_list,columns=self.stocks_head) 

    #获取热度榜所有股票，返回list
    def getHotStocksList(self):
        ls = [self.stocks_head]
        rsp = rq.get(url=self.url,headers=self.header)
        rsp_body = rsp.json()
        hot_list = parseHotStockPackage(rsp_body)
        ls.extend(hot_list)
        return ls

class LimitUpStocks:
    def __init__(self):
        self.url = "https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool"
        self.stocks_head = ['Name', 'Code', 'Latest', 'Currency_value', 'Reason_type', 'Limitup_type', 'High_days', 'Change_rate', 'Date']
        self.reason_head = ['涨停股票数','占比','相关股票']
        self.date = time.strftime('%m-%d',time.localtime(time.time()))
        self.header = {
                'Host': 'data.10jqka.com.cn',
                'Connection': 'keep-alive',
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; HD1900 Build/QKQ1.190716.003; wv) \
                AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.92 Mobile \
                Safari/537.36 Hexin_Gphone/10.40.10 (Royal Flush) hxtheme/1 innerversion/\
                G037.08.577.1.32 followPhoneSystemTheme/1 userid/475543965 \
                hxNewFont/1 isVip/0 getHXAPPFontSetting/normal getHXAPPAdaptOldSetting/0',
                'Sec-Fetch-Mode': 'cors',
                'X-Requested-With': 'com.hexin.plat.android',
                'Sec-Fetch-Site': 'same-origin',
                'Referer': 'https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                }

    def requestParam(self,page=1):
        return  {'page': page,'limit': 15,'field': '199112,10,9001,330323,330324,330325,9002,330329,\
                133971,133970,1968584,3475914,9003,9004','filter': 'HS,GEM2STAR','order_field': 330324,\
                'order_type': 0,'data': '','_': 1657151054188}

    #获取涨停所有股票
    def getLimitUpStocks(self):
        rsp = rq.get(url=self.url,headers=self.header,params=self.requestParam())
        rsp_body = rsp.json()
        one_page_data = parseLimitUpStockPackage(rsp_body)
        page = rsp_body['data']['page']
        page_count = math.ceil(page['total']/page['limit'])

        #获取翻页全量数据
        full_stocks = []
        for i in range(2,page_count+1):
            rsp = rq.get(url=self.url,headers=self.header,params=self.requestParam(i))
            one_page_data.extend(parseLimitUpStockPackage(rsp.json()))        

        #返回股票详情表单
        self.limit_up_stocks = pds.DataFrame(data=one_page_data,columns=self.stocks_head)
        return self.limit_up_stocks
        
        #涨停原因表单
        return pds.DataFrame(data=reason_type,columns=self.reason_head)

#解析热度榜数据包
def parseHotStockPackage(body):
    date = datetime.now()
    # date = datetime.now().strftime("%Y-%m-%d %H:%M")
    if body['status_code'] == 0:
        # date = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        rows = []
        infos = body['data']['stock_list']
        for info in infos:
            row = [ info['name'],info['order'],info['hot_rank_chg'],\
                    '&'.join(info['tag']['concept_tag']),int(float(info['rate'])),info['tag'].get('popularity_tag',None),date]
            rows.append(row)
        return rows

#解析涨停池数据包
def parseLimitUpStockPackage(body):
    if body['status_code'] == 0:
        date = datetime.now()
        rows = []
        infos = body['data']['info']
        # print(infos)
        for info in infos:
            #ctx.log.warn("stock name:%s"%info['name'])
            row = [ info['name'],info['code'],info['latest'],info['currency_value']/100000000,\
                    info['reason_type'],info['limit_up_type'],info['high_days'],\
                    info['change_rate'],date ]
            rows.append(row)
        return rows


def hotStocks2Sqlite():
    hot_stocks = HotRankStocks()
    try:
        # conn = sqlConn.connect(
        #     host = "localhost",
        #     port = 3306,
        #     user = "root",
        #     password = "888888",
        #     database = "tangying"
        # )
        # print("connect mysql success.")
        # conn.start_transaction()
        # cursor = conn.cursor(prepared=True)
        # sql = "INSERT into hotstocks VALUES(%s,%s,%s,%s,%s,%s,%s)"
        # cursor.execute(sql,("中通客车", 1, 0, "燃料电池&新能源汽车", 432514325.2, None, "2022-04-23 08:33:45"))
        # conn.commit()

        hot_stocks_df = hot_stocks.getHotStocksDataFrame()
        engine = getSqliteEngine()
        hot_stocks_df.to_sql("hotstocks",engine,index=False,if_exists="append")
    except Exception as e:
        print("err:",e)
        # if "conn" in dir():
        #     conn.rollback()
    finally:
        pass
        # if "engine" in dir():
        #     engine.close()

def limitupStocks2Sqlite():
    limitup_stocks = LimitUpStocks()
    try:
        limitup_stocks_df = limitup_stocks.getLimitUpStocks()
        # limitup_stocks_df.loc('Currency_value')/10^8

        #拆分涨停原因
        rows = []
        for _,row in limitup_stocks_df.iterrows():
            for reason in row.loc['Reason_type'].split('+'):
                # row.loc['Reason_type'] = reason
                new_row = row.copy()
                new_row.Reason_type = reason
                rows.append(new_row)
        new_limitup_stocks_df = pds.DataFrame(rows,columns=limitup_stocks.stocks_head).reset_index(drop=True)
   
        engine = getSqliteEngine()
        new_limitup_stocks_df.to_sql("limitupstocks",engine,index=False,if_exists="append")
    except Exception as e:
        print(e)

def allSecurities2Sqlite():
    jq.auth('17521718347','Zb110110')
    all_stocks = jq.get_all_securities(types=['stock'], date=None).drop(columns=['start_date', 'end_date','type'])
    all_stocks.rename(columns={'display_name':'value'},inplace=True)
    engine = getSqliteEngine()
    all_stocks.to_sql("securities",engine,index_label='code',if_exists="append")


