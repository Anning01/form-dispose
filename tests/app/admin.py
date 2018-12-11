from django.contrib import admin

# Register your models here.
from app.models import File_Uploading, User

admin.site.register(User)
admin.site.register(File_Uploading)
