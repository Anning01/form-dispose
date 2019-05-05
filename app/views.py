from django.shortcuts import render
import datetime
import os
import time

from django.core.exceptions import ObjectDoesNotExist

# Create your views here.
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_extensions.cache.decorators import cache_response

import numpy as np
import pandas as pd
import xlrd
import xlwt
import qrcode
import requests

from app.models import File_Uploading, ExpressCoding, MallUser

from yichadan.settings import MEDIA_ROOT


# 序列化器
class FileSerializers(serializers.ModelSerializer):
    uploading_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = File_Uploading
        fields = '__all__'


# 序列化器
class ExpressCodingSerializers(serializers.ModelSerializer):
    class Meta:
        model = ExpressCoding
        fields = '__all__'


# 设置可上传的文件尾称
legal_name = ['xlsx', 'csv', 'xls']


# 做一个复用的切片获取文件类型的函数 并且获取所有的columns
def utils(filename, file_id=None, columns1=None, columns2=None, result=None):
    file = filename.split('.')[-1]
    if file in legal_name:
        if file == 'csv':
            data = pd.read_csv(os.path.join(MEDIA_ROOT, filename))
        else:
            data = pd.read_excel(os.path.join(MEDIA_ROOT, filename))
        if columns1 and result and file_id:
            if columns2:
                data = data.set_index([columns1, columns2])
            else:
                data = data.set_index(columns1)
            return data[result]
        else:
            datalist = data.columns
            return datalist
    return []


# 文件上传
class User_File(APIView):

    def post(self, request, *args, **kwargs):
        """通过POST来传递"""
        user_id = request.POST.get('user_id', '')
        filedata = request.FILES.get('files', '')
        if user_id and filedata:
            """用户上传文件处理"""
            userid = MallUser.objects.filter(id=user_id).first()
            if userid:
                File_Uploading.objects.create(name=userid, file=filedata)
                return Response(data={'code': 0}, status=status.HTTP_200_OK)
            else:
                return Response(data={'code': 1})
        elif user_id and not filedata:
            """用户查询自己下的所有文件"""
            file_list = File_Uploading.objects.filter(name=user_id)
            ser = FileSerializers(instance=file_list, many=True)
            return Response(ser.data, status=status.HTTP_200_OK)
        else:
            return Response(data={'code': 1})

    def get(self, request, *args, **kwargs):
        """
        获取到用户设置的目标参数和结果参数，写入数据库，下次就方便查找，生成查询路由二维码
        """
        # 文件ID
        file_id = request.GET.get('file_id', '')
        # 目标1 查询的key 可以多个
        target1 = request.GET.get('target1', '')
        # 目标2 查询的key 可以多个
        target2 = request.GET.get('target2', '')
        # 结果 查询的value
        result = request.GET.get('result', '')
        # 设置的文件昵称
        file_name = request.GET.get('file_name', '')
        try:
            file = File_Uploading.objects.get(id=file_id)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if file_id and not target1 and not target2 and not result and not file_name:
            datalist = utils(file.file.name)
            data = []
            data_list = [col for col in datalist]
            for index, info in enumerate(data_list):
                data.append({index: info})
            return Response({'data': data})
        elif target1 and result and file_id and file_name:
            if target2:
                File_Uploading.objects.filter(id=file_id).update(columns1=target1, columns2=target2, result=result,
                                                                 is_set=1, file_name=file_name)
            else:
                File_Uploading.objects.filter(id=file_id).update(columns1=target1, result=result, is_set=1,
                                                                 file_name=file_name)
            paths = 'http://qianduan.sailafeinav.com/courier?file_id={}'.format(file_id)
            path = os.path.join(MEDIA_ROOT, 'QR_code', file_id)
            url = os.path.join('media/QR_code/{}'.format(file_id))
            img = qrcode.make(paths)
            with open('{}.png'.format(path), 'wb') as f:
                img.save(f)
            File_Uploading.objects.filter(id=file_id).update(QR_code=url + '.png')
            data = {
                'id': file_id,
                'QR_code': url + '.png',
            }
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(data={'code': 1}, status=status.HTTP_200_OK)


class File_query(APIView):
    """文件查询"""
    def get(self, request, *args, **kwargs):
        """接收目标参数和文件id"""
        target = request.GET.get('target', '')
        id = request.GET.get('file_id', '')
        datas = []
        query = File_Uploading.objects.filter(id=id).first()
        if target and query:
            # 读取用户文件
            data = pd.read_excel(os.path.join(MEDIA_ROOT, query.file.name).replace('\\', '/'))
            # 查看是否存在
            a = target in [str(i) for i in data[query.columns1]]
            if query.columns2:
                b = target in [str(i) for i in data[query.columns2]]
            else:
                b = False
            if a and b:
                data1 = data.set_index([query.columns1, query.columns2])
                data2 = data1[query.result]

            elif a:
                data1 = data.set_index(query.columns1)
                data2 = data1[query.result]
            elif b:
                data1 = data.set_index(query.columns2)
                data2 = data1[query.result]
            else:
                return Response({'error': '目标不存在'})
            try:
                if type(data2[target]) == np.int64:
                    datas.append({'1': data2[target]})
                else:
                    info = [i for i in data2[target]]
                    for index, j in enumerate(info):
                        datas.append({index: j})
            except:
                if type(data2[int(target)]) == np.int64:
                    datas.append({'1': data2[int(target)]})
                else:
                    info = [i for i in data2[int(target)]]
                    for index, j in enumerate(info):
                        datas.append({index: j})
        return Response({'data': datas}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """追加数据，一样的文件，一样的columns，才可以追加数据"""
        file_id = request.POST.get('file_id', '')
        filedata = request.FILES.get('files', '')
        if file_id and filedata:
            try:
                file_query = File_Uploading.objects.get(id=file_id)
            except ObjectDoesNotExist:
                return Response({'error': 'id不存在'})
            oldfile = [i for i in utils(file_query.file.name)]
            newfile = [j for j in pd.read_csv(filedata).columns] if filedata.name.split('.')[-1] == 'csv' else [j for j
                                                                                                                in
                                                                                                                pd.read_excel(
                                                                                                                    filedata).columns]
            if oldfile == newfile:
                file1 = file_query.file.name.split('.')[-1]
                if file1 == 'csv':
                    data1 = pd.read_csv(os.path.join(MEDIA_ROOT, file_query.file.name))
                else:
                    data1 = pd.read_excel(os.path.join(MEDIA_ROOT, file_query.file.name))
                file2 = filedata.name.split('.')[-1]
                if file2 == 'csv':
                    data2 = pd.read_csv(filedata)
                else:
                    data2 = pd.read_excel(filedata)
                data = pd.concat([data1, data2])
                writer = pd.ExcelWriter(os.path.join(MEDIA_ROOT, file_query.file.name))
                data.to_excel(writer, 'Sheet1', index=False)
                writer.save()
                return Response({'code': 0})
            return Response({'code': 1, 'oldfile': oldfile, 'newfile': newfile})
        return Response({'error': '未接收到任何参数'})


class rmViews(APIView):
    """删除操作"""
    def get(self, request, *args, **kwargs):
        """查询文件设置的昵称"""
        file_id = request.GET.get('file_id', '')
        if file_id:
            try:
                fileid = File_Uploading.objects.get(id=file_id)
            except:
                return Response({'error': 'id不存在'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'file_name': fileid.file_name}, status=status.HTTP_200_OK)
        return Response({'error': '400'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        """删除文件"""
        file_id = request.POST.get('file_id', '')

        if file_id:
            try:
                fileid = File_Uploading.objects.get(id=file_id)
            except:
                return Response({'error': 'id不存在'}, status=status.HTTP_400_BAD_REQUEST)
            if fileid.file:
                os.remove(MEDIA_ROOT + '/' + fileid.file.name)
                if fileid.QR_code:
                    os.remove(MEDIA_ROOT + '/QR_code/' + fileid.QR_code.split('/')[-1])
            File_Uploading.objects.filter(id=file_id).delete()
            return Response({'rm': True}, status=status.HTTP_200_OK)
        return Response({'rm': False}, status=status.HTTP_400_BAD_REQUEST)


class query(APIView):
    """查询类"""
    def get(self, request, *args, **kwargs):
        code = request.GET.get('code', '')
        number = request.GET.get('number', '')
        if code and number:
            data = getWuLiuMsg(postid=number, code=code)
            return Response(data, status=status.HTTP_200_OK)
        elif number and not code:
            data = getWuLiuMsg(postid=number)
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': '1111'}, status=status.HTTP_200_OK)


class getKDCodeView(APIView):
    @cache_response(timeout=60 * 60 * 24 * 7, cache='redis_special')
    def get(self, request, *args, **kwargs):
        info_list = ExpressCoding.objects.all()
        data = ExpressCodingSerializers(instance=info_list, many=True)
        return Response(data.data, status=status.HTTP_200_OK)


# 百度快递查询接口
def getbaiduWuLi(postid, code='yunda'):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }
    # 新建session对象来保存cookie
    session = requests.session()
    # 先去访问百度获取到百度的cookie
    session.get('https://www.baidu.com', headers=headers)

    query = {
        'appid': 4001,
        'com': code,
        'nu': postid
    }
    response = session.get('https://sp0.baidu.com/9_Q4sjW91Qh3otqbppnN2DJv/pae/channel/data/asyncqury', params=query,
                           headers=headers)
    # 获取到的是所有的快递物流信息
    if response.content.decode('utf-8') == "":
        getbaiduWuLi(postid, code)
    else:

        datadict = eval(response.content)
        if int(datadict['error_code']) == 0:
            return {'data': datadict['data']['info']['context'], 'code': datadict['error_code']}
        else:
            return {'msg': datadict['msg'], 'code': datadict['error_code']}


# 快递100获取物流信息的组建
def getWuLiuMsg(postid, code='yunda', *args, **kwargs):
    data = {
        "token": "",
        "platform": "MWW",
        "coname": "sailafeina"
    }
    query = {
        "type": code,
        "postid": postid,
        "id": 1,
        "valicode": "",
    }
    response = requests.post('https://m.kuaidi100.com/query', data=data, params=query)
    text = response.text
    if 'null' in text:
        text = text.replace('null', '\"\" ')
    datadict = eval(text)
    if int(datadict['status']) == 604:
        wuliudata = getbaiduWuLi(postid, code)
        return wuliudata
    else:
        if len(datadict['data']) == 0:
            return {'msg': datadict['message'], 'code': datadict['status']}
        else:
            return {'data': datadict['data'], 'code': datadict['status']}


def chaxun(num, wucode, again=False):
    info = getWuLiuMsg(num, wucode)
    # 有物流信息,但超过3天没更新就判断为异常快递单号(快递100的数据格式)
    if info is None:
        chaxun(num, wucode)
    else:
        if int(info['code']) == 200:
            wuliuDate = info['data'][0]['ftime']
            shijian = time.strptime(wuliuDate, '%Y-%m-%d %H:%M:%S')
            shijian2 = datetime.datetime(shijian.tm_year, shijian.tm_mon, shijian.tm_mday)
            now = datetime.datetime.now()
            sepTime = (now - shijian2).days
            if sepTime > 3:
                return True
        # 百度接口的数据格式
        elif int(info['code']) == 0:
            # 返回的是一个字符串格式的时间戳
            wuliuDate = int(info['data'][0]['time'])
            time_local = time.localtime(wuliuDate)
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
            shijian = time.strptime(dt, '%Y-%m-%d %H:%M:%S')
            shijian2 = datetime.datetime(shijian.tm_year, shijian.tm_mon, shijian.tm_mday)
            now = datetime.datetime.now()
            sepTime = (now - shijian2).days
            if sepTime > 3:
                return True
        elif int(info['code']) == 3:
            return True
        elif int(info['code']) == 201:
            return True
        elif int(info['code']) == 500 or 404:
            return True
        else:
            return False


if __name__ == '__main__':
    getWuLiuMsg(3918010841967, 'yunda')
