# -*- coding:utf-8  -*-
u'''
Формы приложения night
'''
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import permission_required
from HotKeyStat.models import (Learner, Result, Block)


# from django_tools.middlewares import ThreadLocal

class ProgressForm(forms.ModelForm):
    u'''
    Форма количество проголосовавших на контрольное время по избирательному участку
    '''

    def __init__(self, *args, **kwargs):
        super(TurnOutForm, self).__init__(*args, **kwargs)

        self.fields["time_point"].widget = forms.HiddenInput()

        if self.instance is not None:
            self.fields["is_ready"].initial = self.instance.lot.is_ready
            self.fields["pre_votes"].initial = self.instance.lot.pre_votes

            if not self.instance.time_point.is_first_time():
                self.fields["is_ready"].disabled = True
                self.fields["pre_votes"].disabled = True
            self.fields["time_point"].disabled = True

            for field in Turnout.VALUE_FIELDS:
                self.fields[field].min_value = 0

            user = ThreadLocal.get_current_user()

            if self.instance.time_point.is_closed and self.instance.is_filled :
                if not user.has_perm('night.view_admin'):
                    for field in Turnout.VALUE_FIELDS:
                        self.fields[field].disabled = True

    class Meta:
        model = Turnout
        fields = [
            'time_point', 'is_ready', 'pre_votes',
            'electors_count', 'votes', 'vote_out_s',
            'vote_out_f', 'count_complain', 'vote_percent'
        ]

    is_ready = forms.BooleanField(
        label=u'Готовность ИУ',
        widget=forms.CheckboxInput(),
        required=False
    )

    pre_votes = forms.IntegerField(
        label=u'Число избирателей, проголосовавших досрочно',
        min_value=0,
        required=False
    )

    def save(self, *args, **kwargs):
        super(TurnOutForm, self).save(*args, **kwargs)

        if self.instance.time_point.is_first_time():
            self.instance.lot.is_ready = self.cleaned_data['is_ready']
            self.instance.lot.pre_votes = self.cleaned_data['pre_votes']
            self.instance.lot.save()

        return self.instance

    def clean(self):
        u"""
        Проверка, чтобы все поля формы были либо пустыми, либо заполненными
        """
        cleaned_data = super(TurnOutForm, self).clean()

        values = [cleaned_data.get(field, None) for field in Turnout.VALUE_FIELDS]

        if any(v is None for v in values) and any(v is not None for v in values):
            self.add_error(
                "__all__",
                u"Недопустимо частичное заполнение данных на отчетное время. " +
                u"Все поля должны быть заполнены."
            )

        return cleaned_data