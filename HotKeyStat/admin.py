from django.contrib import admin
from HotKeyStat.models import(
    Organizations, Manager, Learner, Block,
    TypeResults, Result
)
# Register your models here.

class ResultAdmin(admin.ModelAdmin):
    list_filter = ['type_result', 'block', 'learner']
    ordering = ('learner', 'type_result',  'block')

admin.site.register([
    Organizations, Manager, Learner, Block, TypeResults
    ]
)

admin.site.register(Result, ResultAdmin)
