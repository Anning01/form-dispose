import random
import time

from django.db import models


# Create your models here.


class MallUser(models.Model):
    username = models.CharField(unique=True, max_length=50, verbose_name='用户名')
    pass_field = models.CharField(db_column='pass', editable=False, max_length=64, blank=True, null=True,
                                  verbose_name='密码')

    class Meta:
        db_table = 'file_uploading'
        verbose_name = 'ex文件上传表'
        verbose_name_plural = verbose_name

    def __str__(self):
        if not self.username:
            return str(self.id)
        return self.username


class ExpressCoding(models.Model):
    code = models.CharField(max_length=80, verbose_name='快递公司编码')
    name = models.CharField(max_length=100, verbose_name='快递公司名称')

    class Meta:
        managed = False
        db_table = 'expresscoding'
        verbose_name = '快递公司表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class File_Uploading(models.Model):
    file = models.FileField(upload_to='files', verbose_name='文件名')
    name = models.ForeignKey(to='MallUser', on_delete=models.CASCADE, verbose_name='所属人')
    columns1 = models.CharField(max_length=20, null=True, blank=True, verbose_name='索引名1')
    columns2 = models.CharField(max_length=20, null=True, blank=True, verbose_name='索引名2')
    result = models.CharField(max_length=20, null=True, blank=True, verbose_name='结果')
    QR_code = models.CharField(max_length=100, null=True, blank=True, verbose_name='查询二维码')
    file_name = models.CharField(max_length=80, null=True, blank=True, verbose_name='查询昵称')
    is_set = models.BooleanField(default=0, choices=((0, '未设置'), (1, '已设置')), editable=False, verbose_name='是否设置')
    uploading_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        db_table = 'file_uploading'
        verbose_name = 'ex文件上传表'
        verbose_name_plural = verbose_name

    def __str__(self):
        if not self.file_name:
            return self.file.name
        return self.file_name
