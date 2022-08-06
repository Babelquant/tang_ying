from django.db import models

# Create tangying data here.

class HotStocks(models.Model):
    Name = models.CharField('股票名',max_length=8)
    Rank = models.SmallIntegerField('排名')
    Change = models.SmallIntegerField('排名变化')
    Concept = models.CharField('概念',max_length=32)
    Popularity = models.FloatField('人气')
    Express = models.CharField('表现',max_length=16,null=True)
    Time = models.DateTimeField('时间',auto_now=True)

    class Meta:
        db_table = 'hotstocks'

class LimitupStocks(models.Model):
    Name = models.CharField('股票名',max_length=8)
    Code = models.CharField('股票代码',max_length=8)
    Latest = models.FloatField('涨停价')
    Currency_value = models.FloatField('流通值')
    Reason_type = models.CharField('涨停原因',max_length=32)
    Limitup_type = models.CharField('涨停形态',max_length=8)
    High_days = models.CharField('几天几板',max_length=8,null=True)
    Change_rate = models.FloatField('换手率')
    Date = models.DateTimeField('日期',auto_now=True)

    class Meta:
        db_table = 'limitupstocks'