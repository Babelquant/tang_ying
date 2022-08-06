from django.shortcuts import render
from data.models import *
import pandas as pd
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import *

# Create your views here.
from crontab.cron import *
from django.http import HttpResponse
from django.db.models import Aggregate,CharField,Count

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
    hotstocks = HotStocks.objects.filter(Time__gte=datetime.today()-timedelta(days=3)).\
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
    stocks = HotStocks.objects.filter(Time__gte=datetime.today()-timedelta(days=3)).filter(Rank__lte=10).values('Name').distinct()
    for stock in stocks:
        top10.append(stock['Name'])
    return HttpResponse(json.dumps(top10,ensure_ascii=False))

#values做分组
#annotate,aggregate做聚合
def getLimitupStocks(request):
    limitup_stocks_pool = LimitupStocks.objects.values('Name').\
    annotate(_Reason_type=GroupConcat('Reason_type')).values('Name', 'Latest', 'Currency_value', '_Reason_type', 'Limitup_type', 'High_days', 'Change_rate')
    return HttpResponse(json.dumps(list(limitup_stocks_pool),ensure_ascii=False))

#获取概念股统计数据
def getConceptStocks(request):
    chart = [['Reason_type', 'Limitup_count','Relative_stocks','Date']]
    limitup_stocks_pool = LimitupStocks.objects.values('Reason_type').\
    annotate(Limitup_count=Count('Name'),Relative_stocks=GroupConcat('Name')).values_list('Reason_type', 'Limitup_count','Relative_stocks','Date')
    for limitup_stock_pool in limitup_stocks_pool:  #返回值类型为元组
        #拿到数据库中时间字符串二次加工已满足图表对时间格式的要求
        list_limitup_stock_pool = list(limitup_stock_pool)
        list_limitup_stock_pool[3] = list_limitup_stock_pool[3].strftime('%Y-%m-%d')
        chart.append(list_limitup_stock_pool)
    # return HttpResponse(json.dumps(list(limitup_stocks_pool),cls=DjangoJSONEncoder,ensure_ascii=False))
    return HttpResponse(json.dumps(chart,cls=DjangoJSONEncoder,ensure_ascii=False))