from django.shortcuts import render

# Create your views here.

import easytrader as et

user = et.use('ths')
user.prepare(user='阿狗M',password='')