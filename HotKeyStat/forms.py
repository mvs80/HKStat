# -*- coding:utf-8  -*-
u'''
Формы приложения HotKeyStat
'''
from django import forms
# from django.core.exceptions import ValidationError
# from django.contrib.auth.decorators import permission_required
# from HotKeyStat.models import (Learner, Result, Block)


# from django_tools.middlewares import ThreadLocal

class LearnerFilterForm(forms.Form):
    u'''
    Форма количество проголосовавших на контрольное время по избирательному участку
    '''
    date_from = forms.DateField(
        label=u'Date From', 
        widget=forms.DateInput(),
        required=False,
    )
    date_by = forms.DateField(label=u'Date To', required=False)
    