from django.urls import path
from data.views import *

urlpatterns = [
    path('hot_stocks/', getHotRankStocks),
    path('hot10_stocks/', getHotTop10Stocks),
    path('limitup_stocks/', getLimitupStocks),
    path('concept_stocks/', getConceptStocks),
    path('all_securities/', getAllSecurities),
    path('candlestick/<code>/', getCandlestick),
]
