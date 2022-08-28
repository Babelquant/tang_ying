from django.urls import path
from data.views import *

urlpatterns = [
    #获取热度榜数据
    path('hot_stocks/', getHotRankStocks),
    #获取排名前十的股票
    path('hot10_stocks/', getHotTop10Stocks),
    #获取当日涨停股票
    path('limitup_stocks/', getLimitupStocks),
    #获取概念分析数据
    path('concept_statistic/', conceptStatistic),
    #获取所有股票信息
    path('all_securities/', getAllSecurities),
    #获取所有概念信息
    path('all_concepts/', getAllConcepts),
    #获取单只股票蜡烛图数据
    path('candlestick/<code>/', getCandlestick),
    #涨停策略数据
    path('limitup_strategy/', limitupStrategyData),
    #概念策略数据
    path('concept_strategy/<codes>/', conceptStrategyData),
    #快速下跌策略数据
    path('sharpfall_strategy/', getSharpfallStrategy),
    #获取实时资讯
    path('news/', getNews),

]
