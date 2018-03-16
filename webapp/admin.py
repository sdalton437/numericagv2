from django.contrib import admin



# Register your models here.
from .models import UserTransaction,UserRquestSite
admin.site.register(UserRquestSite)
admin.site.register(UserTransaction)

