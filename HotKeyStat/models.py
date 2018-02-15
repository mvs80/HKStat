# -*- coding:utf-8 -*-
u'''
Модели приложения.
'''
# from datetime import date, datetime, timedelta
# from django.utils import timezone
# from django.db.models import Count, Max, Q, Sum

from django.db import models
from django.utils.formats import date_format

from django.conf import settings
from django.contrib.auth.models import User, Group
# Create your models here.


class Organizations(models.Model):
    u'''
    Информация об организации
    '''
    org_parent = models.ForeignKey(
        'self',
        verbose_name=u'Paternal organization', 
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    name = models.CharField(u'The name organization', max_length=200)
    is_work = models.BooleanField(
        u'work', null=False, blank=True, default=False,
        help_text=u'He works at present')

    class Meta:
        verbose_name = u'Organization'
        verbose_name_plural = u'Organizations'
        unique_together = ('name',)
        ordering = ('name',)

    def __str__(self):
        if self.org_parent:
            parent_org = self.org_parent.name
            return u'%s - %s' %(self.name, parent_org)
        else:
            return self.name


class Manager(models.Model):
    u'''
    Менеджеры, просматривающие статистику
    '''
    user = models.ForeignKey(
        User,
        verbose_name=u'user id',
        help_text=u'Id django-user'
    )
    org = models.ForeignKey(
        Organizations, 
        verbose_name=u'Organization'
    )

    class Meta:
        verbose_name = u'Manager'
        verbose_name_plural = u'Managers'

    def __str__(self):
        user = self.get_user_obj()
        if user:
            if user.last_name and user.first_name:
                return u'%s %s' % (user.last_name, user.first_name)
            elif user.last_name:
                return u'%s' % user.last_name
            return u'%s' % user.username
        return u'[User not found]'
    
    def get_user_obj(self):
        u'''
        Возвращает экземпляр класса django.conf.auth - пользователя Django,
        соответствующего текущему менеджеру,
        или None в случае, если текущий менеджер не связан ни с каким пользователем.
        '''
        return User.objects.get(pk=self.user_id)

    def get_learner_list(self):
        u'''
        Возвращает список учеников из организации менеджера (проверяющего)
        '''
        return Learner.objects.filter(org=self.org)

User.manager = property(
    lambda u: Manager.objects.filter(user=u.id).first()
)


class Learner(models.Model):
    u'''
    Ученик, проходящий обучение
    '''
    org = models.ForeignKey(Organizations, verbose_name = 'Organization')
    surname = models.CharField(u'Surname', max_length=100, null=False, blank=False)
    name = models.CharField(u'Name', max_length=100, null=False, blank=False)
    email = models.CharField(u'E-mail', max_length=50, null=False, blank=False)

    class Meta:
        verbose_name = u'Learner'
        verbose_name_plural = u'Learners'
        unique_together = (u'surname', u'name', u'email', u'org')
        ordering = (u'org', u'surname', u'name')

    def __str__(self):
        return u'%s %s(%s) - %s' %(self.surname, self.name, self.email, self.org.name)

    def get_result(self, block, type_res):
        u'''
        Возвращает результат ученика по топику/блоку
        '''        
        academy_res = Result.objects.filter(
                learner=learner,
                block=block,
                type_result=type_res
            ).firts()
        if academy_res:
            return academy_res.key_count
        
        return 0


class Block(models.Model):
    u'''
    Блоки курса
    '''
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        verbose_name=u'Parent block',
        null=True, blank=True
    )
    num = models.PositiveIntegerField(u'Block number block in the group')
    name = models.CharField(u'Block name', max_length=100)
    key_max = models.PositiveIntegerField(u'Maximum number of keys per block', null=False, blank=False)
    number = models.CharField(u'Block id', null=False, max_length=5, blank=False, unique=True)

    class Meta:
        verbose_name = u'Block'
        verbose_name_plural = u'Blocks'
        ordering = (u'num', u'name')

    def __str__(self):
        return u'%s. %s' %(self.num, self.name)

    @classmethod
    def get_parent_block(cls):
        u'''
        Возвращает список родительских блоков.
        '''
        # Находим блоки с пустым полем parent
        return cls.objects.filter(parent__isnull=True)

    def get_topic(self):
        u'''
        Возвращает список топиков из родительского блока
        '''
        return Block.objects.filter(parent=self)

    def get_percent_block(self, learner, type_result):
        u'''
        Возвращает процент по блоку в разделе Академия или Игра (type_result)
        '''
        percent = 0
        learner_key_count = None
        # максимальное количество ключей
        key_max = self.key_max
        # количество ключей у ученика
        learner_key_count = Result.objects.filter(
            learner=learner,
            type_result=type_result,
            block=self
        ).first()
        if learner_key_count and key_max and key_max != 0:
            percent = 100.00*learner_key_count/key_max
        
        return percent


class TypeResults(models.Model):
    u'''
    Справочник типы результатов
    '''
    name = models.CharField(u'result type', max_length=20)
    code = models.PositiveIntegerField(u'Code type result', null=False, blank=False)

    class Meta:
        verbose_name = u'TypeResults'
        verbose_name_plural = u'TypeResults'
        ordering = (u'name', )

    def __str__(self):
        return self.name


class Result(models.Model):
    u'''
    Результаты учеников
    '''
    learner = models.ForeignKey(Learner, verbose_name=u'Learner results', null=False, blank=False)
    block = models.ForeignKey(Block, verbose_name=u'on the block', null=False, blank=False)
    type_result = models.ForeignKey(TypeResults, verbose_name=u'result type')
    date_result = models.DateField(u'Date of result')
    key_count = models.PositiveIntegerField(u'number of keys', default=0)
    correct = models.PositiveIntegerField(u'the number of correct answers', default=0)
    time_result = models.FloatField(u'result time', blank=True, null=True)

    class Meta:
        verbose_name = u'LearnerResult'
        verbose_name_plural = u'LearnerResults'
        unique_together = (u'learner', u'block', u'type_result')
        ordering = (u'block', u'learner')

    def __str__(self):
        return u'%s - %s' %(self.learner, date_format(self.date_result))

    def save(self, *args, **kwargs):
        super(Result, self).save(*args, **kwargs)

        # Пересчитываем количество ключей по род. блокам.
        result_parent, _ = Result.objects.get_or_create(
            learner=self.learner,
            block=self.block.parent,
            type_result=self.type_result
        )
        if result_parent is not None:
            result_parent.recalculate()
            
    def recalculate(self):
        u'''
        Пересчитывает количество ключей в родительском топике.
        '''
        totals = Result.objects.filter(
            learner=self.learner,
            type_result=self.type_result,
            parent=self
        ).aggregate(
            keys_count=Sum('key_count')
        )
        self.key_count = totals["votes"] or 0
        self.save()



 