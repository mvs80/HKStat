# -*- coding: utf-8 -*-

from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.db.models import Max, Count, Sum, Avg

from HotKeyStat.models import (
    Learner, Block, TypeResults, Result, Organizations, Manager
    )

# Create your views here.

def index(request):
    u'''
    Страница выбора типа отчета
    '''
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")
    org = manager.org
    return render(request, 'index.html', {
        'org': org,
    })


def progress(request):
    u'''
    отчет Прогресс
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    # Списки учеников, результаты которых доступны текущему проверяющему:
    learners = manager.get_learner_list()
    # Списки родительских блоков
    parent_blocks = Block.get_parent_block()

    academy_type = TypeResults.objects.get(code=0)
    game_type = TypeResults.objects.get(code=1)
    mixgame_type = TypeResults.objects.get(code=2)
    # Список редультатов всех учеников
    all_results = []
    # список имен родительских блоков
    headers = []
    academy_percent = 0
    game_percent = 0
    for i, learner in enumerate(learners, start=0):
        # список результатов каждого ученика
        learner_results = []
        results = []
        learner_results.append(learner)
        for block in parent_blocks:
            if i == 0:
                headers.append(block)
            academy_percent = block.get_percent_block(learner, academy_type)
            game_percent = block.get_percent_block(learner, game_type)
            results.append( 
                {"academy": academy_percent, "game": game_percent}
            )
        learner_results.append(results)
        all_results.append(learner_results)
    
    return render(request, 'progress.html', {
        'blocks': parent_blocks,
        'all_results': all_results,
        'headers': headers,
    })


def progress_block(request, block_id):
    u'''
    отчет Прогресс внутри блока (по топикам)
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего наблюдателя.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    # Списки учеников, результаты которых доступны текущему проверяющему:
    learners = manager.get_learner_list()
    # блок, топики которого мы раскрываем
    parent_block = get_object_or_404(Block, id=block_id)
    # Списки топиков родительского блока
    topics = parent_block.get_topic()

    academy_type = TypeResults.objects.get(code=0)
    game_type = TypeResults.objects.get(code=1)
    mixgame_type = TypeResults.objects.get(code=2)
    # Список редультатов всех учеников
    all_results = []
    # список топиков
    headers = []
    academy_key = None
    game_key = None

    for i, learner in enumerate(learners, start=0):
        # список результатов каждого ученика
        learner_results = []
        results = []
        learner_results.append(learner)
        for topic in topics:
            if i == 0:
                headers.append(topic)
            academy_key = learner.get_result(topic, academy_type)
            game_key = learner.get_result(topic, game_type)
            results.append( 
                {"academy": academy_key, "game": game_key}
            )
        learner_results.append(results)
        all_results.append(learner_results)
    
    return render(request, 'progress_block.html', {
        'blocks': topics,
        'all_results': all_results,
        'headers': headers,
    })


def module_details(request):
    u'''
    отчет Сводный по блокам (mix-game)
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    # Списки учеников, результаты которых доступны текущему проверяющему:
    learners = manager.get_learner_list()
    learner_count = len(learners)
    # Списки родительских блоков
    parent_blocks = Block.get_parent_block()
    mixgame_type = TypeResults.objects.get(code=2)


    headers = [u'Topics', u'Average Time Spent', u'Answers(correct/incorrect)', u'%', u'Graph']
    all_results = []

    for block in parent_blocks:
        # среднее кол-во правильных ответов по блоку
        avg_correct_count = 0
        avg_total_count = 0
        incorrect_count = 0
        block_time = 0
        block_percent = 0
        
        block_results = Result.objects.filter(
            learner__in=learners,
            block=block,
            type_result=mixgame_type
        )
        learner_count = len(block_results)
        if block_results:
            block_time = block_results.aggregate(Avg('time_result'))['time_result__avg']
            correct_count = block_results.aggregate(Sum('correct'))['correct__sum']
            total_count = block_results.aggregate(Sum('total'))['total__sum']
            if total_count and  correct_count:
                incorrect_count = total_count - correct_count
            # среднее кол-во правильных ответов
            if learner_count and learner_count>0 and correct_count:
                avg_correct_count = correct_count//learner_count
            # среднее кол-во всего ответов
            if learner_count and learner_count>0 and total_count:
                avg_total_count = total_count//learner_count
            # среднее кол-во неправильных ответов
            if learner_count and learner_count>0 and incorrect_count:
                incorrect_count = incorrect_count//learner_count
            # процент
            if avg_total_count > 0:
                block_percent = 100.00 * (avg_correct_count/avg_total_count)

        all_results.append([block, {
            'block_time': block_time,
            'correct_count': avg_correct_count,
            'incorrect_count': incorrect_count,
            'block_percent': block_percent}
        ])

    return render(request, 'module_detail.html', {
        'all_results': all_results,
        'headers': headers
    })


def learner_details(request, block_id):
    u'''
    отчет Сводный по ученикам
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    # Списки учеников, результаты которых доступны текущему проверяющему:
    learners = manager.get_learner_list()
    # Текущий блок
    block = get_object_or_404(Block, id=block_id)
    mixgame_type = TypeResults.objects.get(code=2)
    headers = [u'Learner', u'average time', u'Answers(correct/incorrect)', u'%']
    all_results = []

    for learner in learners:
        # кол-во правильных ответов по блоку
        correct_count = 0
        total_count = 0
        incorrect_count = 0
        block_time = 0
        block_percent = 0
        
        learner_result = Result.objects.filter(
            learner=learner,
            block=block,
            type_result=mixgame_type
        ).first()

        if learner_result:
            block_time = learner_result.time_result
            correct_count = learner_result.correct
            total_count = learner_result.total
            if total_count and  correct_count:
                incorrect_count = total_count - correct_count
        
            # процент
            if total_count > 0:
                block_percent = 100.00 * (correct_count/total_count)

        all_results.append([learner, {
            'block_time': block_time,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'block_percent': block_percent}
        ])

    return render(request, 'learner_detail.html', {
        'all_results': all_results,
        'headers': headers, 
        'block_name': block,
    })


