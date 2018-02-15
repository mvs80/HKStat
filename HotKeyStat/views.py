# -*- coding: utf-8 -*-

from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

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
    return render(request, 'index.html')


def progress(request):
    u'''
    отчет Прогресс
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего наблюдателя.
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
            results.append(academy_percent)
            results.append(game_percent)
        learner_results.append(results)
        all_results.append(learner_results)
    # print(learner_results) 
    # print(all_results)       
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
    parent_block = Block.get_object_or_404(id=block_id)
    # Списки топиков родительского блока
    topics = Block.get_topic()

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
            results.append(academy_key)
            results.append(game_key)
        learner_results.append(results)
        all_results.append(learner_results)
    
    return render(request, 'progress_block.html', {
        'blocks': topics,
        'all_results': all_results,
        'headers': headers,
    })


def module_details(request):
    u'''
    отчет Детали1
    '''

    return render(request, 'index.html')


def learner_details(request):
    u'''
    отчет Детали2
    '''

    return render(request, 'index.html')
