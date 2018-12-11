import os

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import File_Uploading
import numpy as np
import pandas as pd
import xlrd

from tests.settings import BASE_DIR


class User_File(APIView):
    legal_name = ['xlsx', 'csv', 'xls']

    def get(self, request, *args, **kwargs):
        file_name = []
        username = request.GET.get('username', '')
        filedata = request.FILES.get('file', '')
        if username and filedata.file:
            File_Uploading.objects.create(name=username, file=filedata.file)
        if username:
            file_list = File_Uploading.objects.filter(name=username)
            for file in file_list:
                file_name.append(file.file)
        return Response({'filename': file_name})

    def post(self, request, *args, **kwargs):
        file_id = request.POST.get('file_id', '')
        target1 = request.POST.get('target1', '')
        target2 = request.POST.get('target2', '')
        result = request.POST.get('result', '')
        if target1 and result and file_id:
            file = File_Uploading.objects.filter(id=file_id).first()
            if target2:
                file.update_or_create(columns1=target1, columns2=target2, result=result)
            else:
                file.update_or_create(columns1=target1, result=result)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)