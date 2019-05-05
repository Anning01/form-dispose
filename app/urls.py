#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/5/5 16:16
# @Author  : An ning
# @email   : 18279460212@163.com
# @File    : urls.py
# @Software: PyCharm
from django.urls import path

from app import views

app_name = 'app'
urlpatterns = [
    # 用户文件上传API
    path('User_File/', views.User_File.as_view()),

    # 返回用户查询数据PI
    path('file_inquire/', views.File_query.as_view()),

    # 获取快递公司及快递公司编码
    path('getKDCode/', views.getKDCodeView.as_view()),

    # 用户物流查询API
    path('query/', views.query.as_view()),

    # 用户删除数据API
    path('rm/', views.rmViews.as_view()),
]
