# -*- coding:utf-8 -*-
u'''
Модели приложения.
'''
# from datetime import date, datetime, timedelta
# from django.db.models import Count, Max, Q, Sum

from django.db import models
from django.db.models import Count, Sum, Avg
from django.utils.formats import date_format

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.utils import timezone
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
        permissions = (('view_statistic', u'Hot Key Statistics'),)

    def __str__(self):
        if self.org_parent:
            parent_org = self.org_parent.name
            return u'%s - %s' %(self.name, parent_org)
        else:
            return self.name

    def get_learner_org(self):
        u'''
        Возвращает список учеников из организации
        '''
        return Learner.objects.filter(org=self)


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
        permissions = (('view_statistic', u'Hot Key Statistics'),)

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
    date_reg = models.DateField(u'Date registartion', auto_now_add=True, null=True)
    rank = models.PositiveIntegerField(u'Rank of the learner', null=True, default = 100000)

    class Meta:
        verbose_name = u'Learner'
        verbose_name_plural = u'Learners'
        unique_together = (u'surname', u'name', u'email', u'org')
        ordering = (u'org', u'surname', u'name')
        permissions = (('view_statistic', u'Hot Key Statistics'),)

    def __str__(self):
        return u'%s %s(%s) - %s' %(self.surname, self.name, self.email, self.org.name)

    def get_result(self, block, type_res):
        u'''
        Возвращает результат ученика по топику/блоку
        '''        
        academy_res = Result.objects.filter(
                learner=self,
                block=block,
                type_result=type_res
            ).first()
        if academy_res:
            return academy_res.key_count
        
        return 0

    def get_result_type(self, type_res):
        u'''
        Возвращает результат ученика по академии/игре или mix
        '''        
        learner_res = Result.objects.filter(
                learner=self,
                type_result=type_res
            ).first()
        if learner_res:
            return learner_res.key_count
        
        return 0
    
    def get_result_excercise(self ):
        u'''
        Возвращает результат ученика по упражнению (Excel Excercise)
        '''        
        block_excercise = Block.objects.filter(number_block='600').first()
        if block_excercise:
            learner_res = Result.objects.filter(
                learner=self,
                block=block_excercise
            ).first()
            if learner_res and learner_res.correct and learner_res.total and learner_res.total > 0 :
                return 100.00*(learner_res.correct/learner_res.total)
        
        return 0

    def get_time_excercise(self):
        u'''
        Возвращает время ученика по упражнению (Excel Excercise)
        '''        
        block_excercise = Block.objects.filter(number_block='600').first()
        if block_excercise:
            learner_res = Result.objects.filter(
                learner=self,
                block=block_excercise
            ).first()
            if learner_res:
                return learner_res.time_result
        
        return 0

    
    def get_learner_avgtime(self, type_res):
        u'''
        Возвращает среднее время ученика по игре'''        
        learner_res = Result.objects.filter(
                learner=self,
                type_result=type_res
            ).aggregate(time=Avg('time_result'))

        if learner_res['time']:
            return learner_res['time']
        
        return 0

    def get_key_count(self):
        u'''
        Возвращает среднее время ученика по игре'''        
        learner_res = Result.objects.filter(
                learner=self,
                block__in=Block.get_parent_block()
            ).aggregate(key_count=Sum('key_count'))

        if learner_res['key_count']:
            return learner_res['key_count']
        
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
    num = models.CharField(u'Block number block in the group', max_length=10)
    name = models.CharField(u'Block name', max_length=100)
    key_max = models.PositiveIntegerField(u'Maximum number of keys per block', null=False, blank=False)
    number_block = models.CharField(u'Block id', null=False, max_length=5, blank=False, unique=True)

    class Meta:
        verbose_name = u'Block'
        verbose_name_plural = u'Blocks'
        ordering = (u'num', u'name')
        permissions = (('view_statistic', u'Hot Key Statistics'),)

    def __str__(self):
        return u'%s. %s' %(self.num, self.name)

    def save(self, *args, **kwargs):
        super(Block, self).save(*args, **kwargs)

        if self.parent:
            # Пересчитываем максимальное количество ключей по дочерним топикам
            BlockParent = self.parent
            BlockParent.recalculate()
            
    def recalculate(self):
        u'''
        Пересчитывает максимальное количество ключей в родительском топике.
        '''
        totals = Block.objects.filter(parent=self).aggregate(key_max=Sum('key_max'))
        self.key_max = totals["key_max"] or 0
        self.save()
    
    @classmethod
    def get_parent_block(cls):
        u'''
        Возвращает список родительских блоков.
        '''
        # Находим блоки с пустым полем parent
        return cls.objects.filter(parent__isnull=True).exclude(number_block='600')

    def get_topic(self):
        u'''
        Возвращает список топиков из родительского блока
        '''
        return Block.objects.filter(parent=self)

    def get_percent_block(self, learner, type_result):
        u'''
        Возвращает процент ученика по блоку в разделе Академия или Игра (type_result)
        '''
        percent = 0
        learner_key_count = 0

        # максимальное количество ключей
        key_max = self.key_max
        # количество ключей у ученика
        learner_result = Result.objects.filter(
            learner=learner,
            type_result=type_result,
            block=self
        ).first()

        if learner_result:
            learner_key_count = learner_result.key_count
        if key_max and key_max != 0:
            percent = 100.00*(learner_key_count/key_max)
        
        return percent
    
    def get_avgtime_block(self, learner, type_result):
        u'''
        Возвращает среднее время ученика по блоку в разделе Академия или Игра (type_result)
        '''
        learner_time = 0

        # среднее время ученика
        learner_result = Result.objects.filter(
            learner=learner,
            type_result=type_result,
            block=self
        ).first()

        if learner_result:
            learner_time = learner_result.time_result
        
        return learner_time

    @classmethod
    def get_max_academy(self):
        u'''
        Возвращает максимальное кол-во ключей по всей академии(=игре)
        '''

        totals = Block.objects.filter(
                parent__isnull=True).exclude(number_block='500'
            ).aggregate(key_max=Sum('key_max'))

        return totals['key_max']
    
    @classmethod
    def get_max_MixGame(self):
        u'''
        Возвращает максимальное кол-во ключей по mixGame
        '''
        return  Block.objects.filter(number_block='500').first().key_max


    def get_avgresult_block(self, manager, type_result):
        u'''
        Возвращает процент по блоку в разделе Академия или Игра (type_result)
        '''
        percent = 0
        block_key_count = 0
        result_count = 0

        # Списки учеников, результаты которых доступны текущему проверяющему:
        learners = manager.get_learner_list()
        # максимальное количество ключей
        key_max = self.key_max
        
        # результаты всех учеников по блоку
        block_results = Result.objects.filter(
            learner__in=learners,
            type_result=type_result,
            block=self
        )
        if block_results:
            # Количество ответов
            result_count = len(learners)
            # Общее кол-во ключей
            block_key_count = block_results.aggregate(Sum('key_count'))['key_count__sum']
            if block_key_count and key_max and key_max > 0:
                percent = (100.00*block_key_count)/(key_max*result_count)
            
        return percent

    def get_time_block(self, manager, type_result):
        u'''
        Возвращает процент по блоку в разделе Академия или Игра (type_result)
        '''
        block_time = 0

        # Списки учеников, результаты которых доступны текущему проверяющему:
        learners = manager.get_learner_list()
        
        # результаты всех учеников по блоку
        block_results = Result.objects.filter(
            learner__in=learners,
            type_result=type_result,
            block=self
        )
        if block_results:
            block_time = block_results.aggregate(Avg('time_result'))['time_result__avg']
            
        return block_time


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
        permissions = (('view_statistic', u'Hot Key Statistics'),)

    def __str__(self):
        return self.name


class Result(models.Model):
    u'''
    Результаты учеников
    '''
    learner = models.ForeignKey(Learner, verbose_name=u'Learner results', null=False, blank=False)
    block = models.ForeignKey(Block, verbose_name=u'on the block', null=False, blank=False)
    type_result = models.ForeignKey(TypeResults, verbose_name=u'result type')
    date_result = models.DateField(u'Date of result', null=True, default=timezone.now())
    key_count = models.PositiveIntegerField(u'count of keys', default=0)
    correct = models.PositiveIntegerField(u'count of correct answers', default=0, null=True)
    total = models.PositiveIntegerField(u'count of total answers', default=0, null=True)
    time_result = models.FloatField(u'result time', blank=True, null=True)

    class Meta:
        verbose_name = u'LearnerResult'
        verbose_name_plural = u'LearnerResults'
        unique_together = (u'learner', u'block', u'type_result')
        ordering = (u'block', u'learner')
        permissions = (('view_statistic', u'Hot Key Statistics'),)

    def __str__(self):
        return u'%s - %s (%s)' %(self.learner, date_format(self.date_result), self.type_result)

    def save(self, *args, **kwargs):
        super(Result, self).save(*args, **kwargs)

        if self.block.parent:
            # Пересчитываем количество ключей по род. блокам.
            result_parent, _ = Result.objects.get_or_create(
                learner=self.learner,
                block=self.block.parent,
                type_result=self.type_result
            )
            date_result = self.date_result
            if result_parent is not None:
                # try:
                result_parent.recalculate(date_result)
                # except:
                #     pass
            
    def recalculate(self, date_res):
        u'''
        Пересчитывает количество ключей в родительском топике.
        '''
        totals = Result.objects.filter(
            learner=self.learner,
            type_result=self.type_result,
            block__in=self.block.block_set.all()
        ).aggregate(
            key_count=Sum('key_count'),
            correct_count=Sum('correct'),
            totalt_count=Sum('total'),
            time_sum=Sum('time_result')
        )

        self.key_count = totals["key_count"] or 0
        self.correct = totals["correct_count"] or 0
        self.total = totals["totalt_count"] or 0
        self.time_result = totals["time_sum"] or 0
        self.date_result = date_res
        self.save()

 