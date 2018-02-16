from django.contrib import admin
from HotKeyStat.models import(
    Organizations, Manager, Learner, Block,
    TypeResults, Result
)
# Register your models here.

admin.site.register([
    Organizations, Manager, Learner, Block, TypeResults, Result
    ]
)
