from django.contrib import admin
from api.models import *

admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(Category)
admin.site.register(Expense)
admin.site.register(ExpenseSplit)
admin.site.register(Settlement)
admin.site.register(Activity)
