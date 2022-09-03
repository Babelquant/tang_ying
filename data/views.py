from django.shortcuts import render
from data.models import *
import pandas as pd
import json
import time as tm
from django.core.serializers.json import DjangoJSONEncoder
from datetime import *
from chinese_calendar import is_workday
import numpy as np
import akshare as ak
from data.cron import *
from django.http import HttpResponse
from django.db.models import Aggregate,CharField,Count

#交易日判断
def is_trade_day(date):
    if is_workday(date):
        if date.isoweekday() < 6:
            return True
    return False

#获取前n个交易日的日期
def beforDaysn(date: str,n: int):
    if n<0:
        return 
    d = datetime.strptime(date,'%Y%m%d')
    i=0
    while i<n:
        d= d-timedelta(days=1)
        if is_trade_day(d):
            i+=1
    return d.strftime('%Y%m%d')
        

#自定义数据库API
class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(distinct)s%(expressions)s)'

    def __init__(self, expression, distinct=False,separator='+', **extra):
        super(GroupConcat, self).__init__(  #python中super用于子类重写父类方法
            expression,
            distinct='DISTINCT ' if distinct else '',
            # separator=' separator "%s"' % separator,
            output_field=CharField(),
            **extra)

def getHotRankStocks(request):
    chart = [('Name','Rank','Change','Concept','Popularity','Express','Time')]
    # try:
    #原生sql查询
    # engine = getSqliteEngine()
    # print(engine.execute("SELECT * FROM hotstocks").fetchall())  
    #ORM查询
    hotstocks = HotStocks.objects.filter(Time__gte=datetime.today()-timedelta(days=1)).\
    values_list('Name','Rank','Change','Concept','Popularity','Express','Time')
    # for hotstock in hotstocks:
    #     print(hotstock[-1])
    for hotstock in hotstocks:
        chart.append(hotstock)
    # except Exception as e:
    #     print(e)
    
    return HttpResponse(json.dumps(chart,cls=DjangoJSONEncoder,ensure_ascii=False))

def getHotTop10Stocks(request):
    top10 = []
    # today = datetime.date(2022,8,2)
    stocks = HotStocks.objects.filter(Time__gte=datetime.today()-timedelta(days=1)).filter(Rank__lte=10).values('Name').distinct()
    for stock in stocks:
        top10.append(stock['Name'])
    return HttpResponse(json.dumps(top10,ensure_ascii=False))

#查询最新涨停股
#values做分组
#annotate,aggregate做聚合
def queryLimitupStocks():
    if LimitupStocks.objects.count() == 0:
        return None
    limitup_stocks_pool = LimitupStocks.objects.filter(Date__gte=LimitupStocks.objects.last().Date-timedelta(days=1))
    last_limitup_stocks = limitup_stocks_pool.values('Name').annotate(_Reason_type=GroupConcat('Reason_type'))
    
    return last_limitup_stocks

def getLimitupStocks(request):
    LimitupStocks = queryLimitupStocks()
    if LimitupStocks == None:
        return HttpResponse(json.dumps([],ensure_ascii=False))
    last_limitup_stocks = LimitupStocks.values('Name', 'Latest', 'Currency_value', '_Reason_type', 'Limitup_type', 'High_days', 'Change_rate')
    return HttpResponse(json.dumps(list(last_limitup_stocks),ensure_ascii=False))

#箱体形态模型
#maxdrop:去掉最大值个数
#返回数据：[top,bottom]
def boxPrice(data,maxdrop=0):
    #计算high一介导二阶导
    high_diff1 = data[['high']].diff(periods=1,axis=0).rename(columns={'high':'high_diff1'})
    high_diff2 = data[['high']].diff(periods=2,axis=0).rename(columns={'high':'high_diff2'})
    #计算计算low一介导二阶导
    low_diff1 = data[['low']].diff(periods=1,axis=0).rename(columns={'low':'low_diff1'})
    low_diff2 = data[['low']].diff(periods=2,axis=0).rename(columns={'low':'low_diff2'})
    #合并统计数据
    data = pd.concat([data,high_diff1,high_diff2,low_diff1,low_diff2],axis=1)
    #计算箱体顶部数据集
    high_set = data[(data.high_diff1>0) & (data.high_diff2>0)]
    #计算箱体底部数据集
    low_set = data[(data.low_diff1<0) & (data.low_diff2<0)]

    low_price = low_set[['low']].min()[0]
    # high_price = high_set[['high']].max()[0]
    high_price = high_set.nlargest(maxdrop+1,'high').high.iloc[maxdrop]
    return [high_price,low_price]
    # print("近期最低价:",low_price)

#获取短期快速下跌的票,v型反转
#说明:
#股价低于9元
#流通盘小于80亿
#近5日跌幅超8%
#月内跌幅超18%
#半年跌幅大于月内跌幅1.5倍
#最低价与年内最低价（去掉一个最低价）差价20%以内
def getSharpfallStrategy(request):
    sharpfalls = []
    #获取所有股票
    sh_em_df = ak.stock_sh_a_spot_em()
    sz_em_df = ak.stock_sz_a_spot_em()
    em_df = pd.concat([sh_em_df,sz_em_df]).reset_index(drop=True)
    #筛选
    # first_em_df = em_df[(em_df.最新价<9) & (em_df.流通市值/10**8<80) & (em_df.六十日涨跌幅<-50.0)][['代码','名称','最低','最新价','六十日涨跌幅']]
    first_em_df = em_df[(em_df.最新价<9) & (em_df.流通市值/10**8<80)][['代码','名称','最低','最新价']].reset_index(drop=True)
    # print(first_em_df)
    end = datetime.today().strftime('%Y%m%d')
    for _,row in first_em_df.iterrows():
        code = getattr(row,'代码')
        print(code)
        if code.startswith('300'):
            continue
        last_price = getattr(row,'最新价')
        low_price = getattr(row,'最低')
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=beforDaysn(end,250), end_date=end)
        #近5日跌幅
        five_day_high_price = stock_zh_a_hist_df.tail().reset_index(drop=True).loc[0,'最高']
        five_day_drop_rate = (five_day_high_price-low_price)/five_day_high_price*100
        if five_day_drop_rate < 8:
            continue
        #月内最高价
        a_month_high_price = stock_zh_a_hist_df.tail(25).最高.max()
        #月内跌幅
        a_month_drop_rate = (a_month_high_price-last_price)/a_month_high_price*100
        #近半年最高价
        # print(stock_zh_a_hist_df)
        half_year_high_price = stock_zh_a_hist_df.tail(120).最高.max()
        #半年最高跌幅
        half_year_drop_rate = (half_year_high_price-last_price)/half_year_high_price*100
        #半年跌幅必须大于月内跌幅1.5倍
        if half_year_drop_rate < a_month_drop_rate*1.5:
            continue
        #月内跌幅超18%，5日跌幅超8%,与年内最低点差价10%以内
        if a_month_drop_rate>18:
            stock_individual_info_em_df = ak.stock_individual_info_em(symbol=code)
            #年内最低价，去掉1个最小值
            year_low_price = stock_zh_a_hist_df.nsmallest(2,'最低').最低.iloc[1]
            if year_low_price*0.8 < low_price and year_low_price*1.2 > low_price:
                sharpfall = {
                    '股票': getattr(row,'名称'),
                    '行业': stock_individual_info_em_df.iloc[2,1],
                    '最新价': last_price,
                    '半年最高价': half_year_high_price,
                    '半年最高跌幅': str(round(half_year_drop_rate,1))+'%',
                    '5日跌幅': str(round(five_day_drop_rate,1))+'%', 
                    '月内跌幅': str(round(a_month_drop_rate,1))+'%', 
                }
                sharpfalls.append(sharpfall)
        #     continue
        # if five_day_drop_rate < 15:
        #     continue
        # #最高价时间点
        # index = stock_zh_a_hist_df[stock_zh_a_hist_df.最高==half_year_high_price].index[0]
        # #最高点出现在2个月以前
        # print('index:',index)
        # if index > 80:
        #     continue
        # print(half_year_high_price,five_day_drop_rate,half_year_drop_rate)
        # if half_year_drop_rate < 40.0:
        #     continue
        # #个股信息
        # stock_individual_info_em_df = ak.stock_individual_info_em(symbol=code)
        # sharpfall = {
        #     '股票': getattr(row,'名称'),
        #     '行业': stock_individual_info_em_df.iloc[2,1],
        #     '最新价': last_price,
        #     '半年最高价': half_year_high_price,
        #     '半年最高跌幅': str(round(half_year_drop_rate,1))+'%',
        #     '5日跌幅': str(round(five_day_drop_rate,1))+'%', 
        #     '月内跌幅': str(round(a_month_drop_rate,1))+'%', 
        # }
        # print(sharpfall)
        # sharpfalls.append(sharpfall)
    return HttpResponse(json.dumps(sharpfalls,cls=DjangoJSONEncoder,ensure_ascii=False))

#概念策略
def conceptStrategyData(request,codes):
    win_stock_set = []
    try:
        for concept_code in codes.split(','):
            concept = Concepts.objects.get(code=concept_code).name
            win_stock = conceptWinStocks(concept_code)
            if not win_stock.empty:
                win_stock.insert(loc=4,column='concept',value=concept)
                win_stock_set.append(win_stock)
    except Exception as e:
        print(e)
        return HttpResponse('err:',e)

    if win_stock_set == []:
        return HttpResponse(json.dumps([],cls=DjangoJSONEncoder,ensure_ascii=False))
    # concept_stocks = []
    if len(win_stock_set) == 1:
        origin_stocks = win_stock_set[0]
    else:
        #df数据分组聚合 
        # print('win_df:',win_stock_set)
        origin_stocks = pd.concat(win_stock_set,ignore_index=True)
        # origin_stocks['concept_count'] = origin_stocks.groupby('name')['name'].transform('count')
        origin_stocks['concept'] = origin_stocks.groupby('name')['concept'].transform(','.join)
        origin_stocks.drop_duplicates(ignore_index=True)
    #df转dict
    # for concept_stock in np.array(origin_stocks).tolist():
    #     concept_stocks.append({'name':concept_stock[0],'code':concept_stock[1],'concept':concept_stock[4],'last_price':concept_stock[2],'increase':concept_stock[3]})
    concept_stocks = origin_stocks.to_dict('records')
    return HttpResponse(json.dumps(concept_stocks,cls=DjangoJSONEncoder,ensure_ascii=False))

#获取概念潜力股筛选数据
def conceptWinStocks(concept_code):
    now = datetime.now().strftime('%Y-%m-%d')
    end = datetime.today().strftime('%Y%m%d')
    rows = []
    #获取概念成份股
    stock_board_cons_ths_df = ak.stock_board_cons_ths(symbol=concept_code)
    # print(concept_code,'获取成分股：\n',stock_board_cons_ths_df)
    #获取每支股票最新价
    for _,row in stock_board_cons_ths_df.iterrows():
        print(row.名称)
        stock_code = row.代码
        if stock_code.startswith('300'):
            continue
        #判断是否st
        # if jq.get_extras('is_st',stock,end_date=now,count=1,df=True).iloc[0,0]:
        #     continue
        last_price = float(row.现价)
        if last_price > 9:
            continue
        #流通值/亿
        if float(row.流通市值.rstrip('亿')) > 100:
            continue
        #近1周最低价
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=beforDaysn(end,4), end_date=end)
        if stock_zh_a_hist_df.empty:
            continue
        five_day_low_price = stock_zh_a_hist_df.最低.min()
        #最新价不高于近1周最低价的15%涨幅
        if last_price > five_day_low_price*1.15:
            continue
        #2019年1月波谷,去掉1个最小值
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code,start_date='20190101',end_date='20190220')
        #有股票在对应的时间段未开盘
        if stock_zh_a_hist_df.empty:
            continue
        bottom_price2019 = stock_zh_a_hist_df.nsmallest(2,'最低').最低.iloc[1]
        #2020年1月波谷,去掉1个最小值
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code,start_date='20200101',end_date='20200220')
        if stock_zh_a_hist_df.empty:
            continue
        bottom_price2020 = stock_zh_a_hist_df.nsmallest(2,'最低').最低.iloc[1]
        #近1周内出现最低价且与2019年1月或2020年1月最低价相差1元以内
        # if abs(five_day_low_price-bottom_price2019)<1 or abs(five_day_low_price-bottom_price2020)<1:
        if five_day_low_price<bottom_price2019+1 or five_day_low_price<bottom_price2020+1:
            #近1周涨幅
            inc = str(round((last_price - five_day_low_price)/five_day_low_price*100,1))+'%'
            name = row.名称
            print(name,last_price,five_day_low_price)
            rows.append([name,stock_code,last_price,inc])
    win_stocks = pd.DataFrame(rows,columns=['name','code','last_price','increase'])
    #分组聚合
    # g = (win_stocks['concept']).groupby(win_stocks['name']).agg(','.join)
    return win_stocks

#妖股策略
#code:股票代码
#near:统计最近多少个交易日的股价最低点
#ratio:首板价与最近几个月最低价比值范围 
def isMonster(code,nearday=100,ratio=[1,1.5]):
    if code == "":
        return False
    #获取最近100个交易日行情数据df
    price_data_100 = getStockPrice(code).tail(nearday)
    #获取最新最高价
    latest_high = price_data_100[['high']].tail(1).values[0][0]
    #计算最近3个月最低价
    box100 = boxPrice(price_data_100)
    high100 = box100[0]
    low100 = box100[1]
    #获取最近1年行情数据df
    price_data_250 = getStockPrice(code).tail(250)
    box250 = boxPrice(price_data_250,maxdrop=2)
    high250 = box250[0]
    low250 = box250[1]

    #获取最近3年行情数据df
    price_data_800 = getStockPrice(code).tail(800)
    box800 = boxPrice(price_data_800,maxdrop=4)
    high800 = box800[0]
    low800 = box800[1]

    if high800/low800 > 2.5:
        return False

    if high250/low250 > 2:
        return False    

    if latest_high/low100 < ratio[0] or latest_high/low100 > ratio[1]:
        return False

    #当前最新价大于最近3月最高价1.1倍
    if latest_high > high100*1.1:
        return False

    # print('近期最低价：',low100)
    # print('近期最高价：',high100)
    # print('近3年最低价：',low800) 
    # print('近3年最高价：',high800)
    return True

#涨停策略输出
def limitupStrategyData(request):
    LimitupStocks = queryLimitupStocks()
    if LimitupStocks == None:
        return HttpResponse(json.dumps([],ensure_ascii=False))
    now = datetime.now().strftime('%Y%m%d')
    #获取涨停池
    last_limitup_stocks = LimitupStocks.values('Name', '_Reason_type', 'Latest', 'Limitup_type', 'High_days', 'Currency_value', 'Code')
    #策略选股
    win_stocks = []
    # all_stocks = Securities.objects.values('name','code')
    for stock in list(last_limitup_stocks):
        if stock['Latest'] > 12:
            continue
        if stock['Currency_value'] > 100:
            continue
        if stock['Limitup_type'] == '一字板':
            continue
        if stock['High_days'].startswith('首'):
            if stock['Latest'] > 9:
                continue
        # code  = Securities.objects.get(name=stock['Name']).code
        stock_code = stock['Code']

        #2019年1月波谷,去掉1个最小值
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code,start_date='20190101',end_date='20190220')
        #有股票在对应的时间段未开盘
        if stock_zh_a_hist_df.empty:
            continue
        bottom_price2019 = stock_zh_a_hist_df.nsmallest(2,'最低').最低.iloc[1]
        #2020年1月波谷,去掉1个最小值
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code,start_date='20200101',end_date='20200220')
        if stock_zh_a_hist_df.empty:
            continue
        bottom_price2020 = stock_zh_a_hist_df.nsmallest(2,'最低').最低.iloc[1]
        #近80日最低价
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=beforDaysn(now,80), end_date=now)
        if stock_zh_a_hist_df.empty:
            continue
        eighty_day_low_price = stock_zh_a_hist_df.最低.min()
        #近80日内出现最低价且与2019年1月或2020年1月最低价相差1元以内
        # if abs(eighty_day_low_price-bottom_price2019)<1 or abs(eighty_day_low_price-bottom_price2020)<1:
        if eighty_day_low_price<bottom_price2019+1 or eighty_day_low_price<bottom_price2020+1:
            win_stocks.append(stock)
            
    return HttpResponse(json.dumps(win_stocks,ensure_ascii=False))

#涨停板统计分析
def limitupStatistic(request):
    head = [['High_days','Name','Date']]
    #过滤本月数据
    # data1 = LimitupStocks.objects.get(High_days__regex=r'(首|2|3).*').filter(Date__month=datetime.today().month).values('Name','Date').\
    data = LimitupStocks.objects.filter(Date__month=datetime.today().month).values('Name','Date','High_days').distinct()
    if data.count() == 0:
        return HttpResponse(json.dumps(head,cls=DjangoJSONEncoder,ensure_ascii=False))
    data_df = pd.DataFrame.from_records(data)
    #df按多列分组
    # data_df['Num'] = data_df.groupby(['High_days','Date'])['Name'].transform('count')
    data_df['Name'] = data_df.groupby(['High_days','Date'])['Name'].transform(','.join)
    # data_df.drop(columns=['Name'],inplace=True)
    data_df.drop_duplicates(ignore_index=True,inplace=True)
    # print(data_df[data_df.Date=='2022-08-30'])
    # data1 = data.values('Date','High_days').annotate(Num=Count('Name')).values_list('High_days','Num','Date').order_by('Date')
    # print(pd.DataFrame.from_records(data1.filter(Date__gte='2022-08-28').values('Name','_Reason_type','Date','High_days')))
    # print(pd.DataFrame.from_records(data))
    for _,d in data_df.iterrows():
        head.append([d.High_days,d.Name,d.Date.strftime('%m-%d')])
    return HttpResponse(json.dumps(head,cls=DjangoJSONEncoder,ensure_ascii=False))

#获取概念股统计数据
def conceptStatistic(request):
    chart = [['Reason_type', 'Limitup_count','Relative_stocks','Date']]
    limitup_stocks_pool = LimitupStocks.objects.filter(Date__month=datetime.now().month).\
    values('Reason_type').annotate(Limitup_count=Count('Name'),Relative_stocks=GroupConcat('Name')).values_list('Reason_type', 'Limitup_count','Relative_stocks','Date').order_by('Date')
    for limitup_stock_pool in limitup_stocks_pool:  #返回值类型为元组
        #拿到数据库中时间字符串二次加工以满足图表对时间格式的要求
        list_limitup_stock_pool = list(limitup_stock_pool)
        list_limitup_stock_pool[3] = list_limitup_stock_pool[3].strftime('%Y-%m-%d')
        chart.append(list_limitup_stock_pool)
    # return HttpResponse(json.dumps(list(limitup_stocks_pool),cls=DjangoJSONEncoder,ensure_ascii=False))
    return HttpResponse(json.dumps(chart,cls=DjangoJSONEncoder,ensure_ascii=False))

#获取所有股票信息
def getAllSecurities(request):
    all_stocks_name = Securities.objects.values('value','code') 
    #qs数据格式返回字典的列表方法:list
    return HttpResponse(json.dumps(list(all_stocks_name),ensure_ascii=False))

#获取所有概念信息
#index:概念代码
#name：概念名称
def getAllConcepts(request):
    all_concepts = Concepts.objects.values('name','code') 
    #qs数据格式返回字典的列表方法:list
    return HttpResponse(json.dumps(list(all_concepts),ensure_ascii=False))
    #直接接口获取 弃用
    # #获取概念
    # stock_board_concept_name_ths_df = ak.stock_board_concept_name_ths()[['概念名称','代码']]
    # stock_board_concept_name_ths_df.rename(columns={'概念名称':'name','代码':'code'},inplace=True)
    # #获取行业
    # stock_board_industry_name_ths_df = ak.stock_board_industry_name_ths()
    # #合并
    # stock_board_name_ths_df = pd.concat([stock_board_concept_name_ths_df,stock_board_industry_name_ths_df]).reset_index(inplace=True)

    #df数据格式返回字典的列表方法:np.array转二维数组--->tolist--->构造字典列表
    #与for v in df.values等效
    # concepts = []
    # for concept in np.array(stock_board_name_ths_df).tolist():
    #     concepts.append({'name':concept[0],'code':concept[1]})
    # return HttpResponse(json.dumps(concepts,cls=DjangoJSONEncoder,ensure_ascii=False))

#获取单只股票数据
def getStockPrice(code):
    today = datetime.today().strftime('%Y%m%d')
    candlestick_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20181201", end_date=today, adjust="qfq")
    # candlestick_df_nona.reset_index(inplace=True)

    return candlestick_df.dropna()

#搜索股票数据接口
def getCandlestick(request,code):
    candlestick = getStockPrice(code)
    # candlestick_df.rename(columns={'index','date'},inplace=True)
    return HttpResponse(json.dumps(np.array(candlestick).tolist(),cls=DjangoJSONEncoder,ensure_ascii=False))

#获取实时资讯
def getNews(request):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    while True:
        try:
            js_news_df = ak.js_news(timestamp=ts)
        except:
            tm.sleep(2)
            continue
        break
    js_news_df.sort_index(ascending=False,inplace=True)
    return HttpResponse(json.dumps(js_news_df.to_dict('records'),cls=DjangoJSONEncoder,ensure_ascii=False))