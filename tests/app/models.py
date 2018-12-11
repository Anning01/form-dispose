import os
import uuid

from django.db import models


# Create your models here.

class User(models.Model):
    username = models.CharField(max_length=20, verbose_name='用户名')
    password = models.CharField(max_length=20, verbose_name='密码')


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex[:8], ext)
    if ext.lower() in ["csv", "xls", "xlsx"]:
        sub_folder = "avatar"
    else:
        sub_folder = "Trash"
    return os.path.join(sub_folder, instance.file.id, filename)


class File_Uploading(models.Model):
    file = models.FileField(upload_to=user_directory_path, verbose_name='文件名')
    name = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='所属人')
    columns1 = models.CharField(max_length=20, null=True, blank=True, verbose_name='索引名1')
    columns2 = models.CharField(max_length=20, null=True, blank=True, verbose_name='索引名2')
    result = models.CharField(max_length=20, null=True, blank=True, verbose_name='结果')
    url = models.CharField(max_length=500, null=True, blank=True, verbose_name='路由')
