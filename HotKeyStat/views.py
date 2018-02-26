# -*- coding: utf-8 -*-

from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
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
    if not request.user.is_authenticated():
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
    # список заголовков таблицы
    headers = [u'Learners', u'Start Date', u'Overall Progress', u'Graph']
    # проценты ученика по академии, игре, mixGame и общий процент
    academy_percent = 0
    game_percent = 0
    mixgame_percent = 0
    all_percent = 0
    # общий максимальный процент
    all_max_percent = 0

    for learner in learners:
        # список результатов каждого ученика
        learner_results = []
        learner_results.append(learner)
        academy_percent = learner.get_result_type(academy_type)
        game_percent = learner.get_result_type(game_type)
        mixgame_percent = learner.get_result_type(mixgame_type)
        all_percent = academy_percent + game_percent + mixgame_percent

        # Максимальное кол-во ключей по академии равно мак кол-ву ключей по игре
        maxkey_academy = Block.get_max_academy() or 0
        # Максимальное кол-во ключей по mixgame
        maxkey_mixgame = Block.get_max_MixGame() or 0
        if maxkey_academy and maxkey_academy > 0:
            academy_percent = 100.00*(academy_percent/maxkey_academy)
            game_percent = 100.00*(game_percent/maxkey_academy)
        if maxkey_mixgame and maxkey_mixgame > 0:
            mixgame_percent = 100.00*(mixgame_percent/maxkey_mixgame)  
        # Общий процент по академии, игре и mixgame
        all_maxe_percent = 2* maxkey_academy + maxkey_mixgame
        if all_max_percent and all_max_percent > 0:
            all_percent = 100.00*(all_percent/all_max_percent)

        learner_results.append( 
            {
                "academy": academy_percent, 
                "game": game_percent, 
                "mixgame": mixgame_percent,
                "all_percent": all_percent, 
            }
        )
        # learner_results.append(results)
        all_results.append(learner_results)
    
    return render(request, 'progress.html', {
        'all_results': all_results,
        'headers': headers,
    })


def progress_block(request):
    u'''
    отчет Прогресс по блокам
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
    time = 0
    for i, learner in enumerate(learners, start=0):
        # список результатов каждого ученика
        learner_results = []
        results = []
        learner_results.append(learner)
        for block in parent_blocks:
            if i == 0:
                headers.append(block)
            # Игра или академия
            if block.number_block != '500':
                academy_percent = block.get_percent_block(learner, academy_type)
                game_percent = block.get_percent_block(learner, game_type)
                time = block.get_avgtime_block(learner, game_type)
                results.append( 
                    {"academy": academy_percent, "game": game_percent, "time": time}
                )
            # MixGame
            else:
                game_percent = block.get_percent_block(learner, mixgame_type)
                results.append( 
                    {"game": game_percent}
                )

        learner_results.append(results)
        all_results.append(learner_results)
    
    return render(request, 'progress_block.html', {
        'blocks': parent_blocks,
        'all_results': all_results,
        'headers': headers,
    })    


def progress_topic(request, block_id):
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
    block_type = 'Academy'

    for i, learner in enumerate(learners, start=0):
        # список результатов каждого ученика
        learner_results = []
        results = []
        learner_results.append(learner)
        for topic in topics:
            if i == 0:
                headers.append(topic)
            # Если раскрываем не MixGame
            if parent_block.number_block != '500':
                academy_key = learner.get_result(topic, academy_type)
                game_key = learner.get_result(topic, game_type)
                results.append( 
                    {"academy": academy_key, "game": game_key}
                )
            else:
                block_type = 'MixGame'
                game_key = learner.get_result(topic, mixgame_type)
                results.append( 
                    {"game": game_key}
                )

        learner_results.append(results)
        all_results.append(learner_results)
    
    return render(request, 'progress_topic.html', {
        'blocks': topics,
        'all_results': all_results,
        'headers': headers,
        'block_type': block_type,
    })


def module_details(request):
    u'''
    отчет Сводный по блокам 
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    # Списки родительских блоков
    parent_blocks = Block.get_parent_block()

    # типы результатов
    academy_type = TypeResults.objects.get(code=0)
    game_type = TypeResults.objects.get(code=1)
    mixgame_type = TypeResults.objects.get(code=2)

    headers = [u'Topics', u'Average Time Spent', u'%', u'Graph']
    all_results = []

    for block in parent_blocks:
        result_academy = 0
        result_game = 0
        result_all = 0

        block_result = []
        block_result.append(block)
        if block.number_block != '500':
            block_time = 0
            block_time = block.get_time_block(manager, game_type)
            result_academy = block.get_avgresult_block(manager, academy_type)
            result_game = block.get_avgresult_block(manager, game_type)
            # общий процент по блоку
            result_all = (result_academy + result_game)/2
        else:
            result_game = block.get_avgresult_block(manager, mixgame_type)
            # общий процент по блоку
            result_all = result_game

        block_result.append({
                "time": block_time, 
                "academy": result_academy, 
                "game": result_game,
                "result_all": result_all,
            })

        all_results.append(block_result)

    return render(request, 'module_detail.html', {
        'all_results': all_results,
        'headers': headers,
    })


def block_details(request, block_id):
    u'''
    отчет Сводный по topics
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    # Списки учеников, результаты которых доступны текущему проверяющему:
    learners = manager.get_learner_list()
    # блок, топики которого мы раскрываем
    parent_block = get_object_or_404(Block, id=block_id)
    # Списки топиков родительского блока
    topics = parent_block.get_topic()

    # типы результатов
    academy_type = TypeResults.objects.get(code=0)
    game_type = TypeResults.objects.get(code=1)
    mixgame_type = TypeResults.objects.get(code=2)

    headers = [u'Topics', u'Average Time Spent', u'%', u'Graph']
    all_results = []

    for topic in topics:
        result_academy = 0
        result_game = 0
        result_all = 0

        topic_result = []
        topic_result.append(topic)
        if topic.number_block != '500':
            topic_time = 0
            topic_time = topic.get_time_block(manager, game_type)
            result_academy = topic.get_avgresult_block(manager, academy_type)
            result_game = topic.get_avgresult_block(manager, game_type)
            # общий процент по блоку
            result_all = (result_academy + result_game)/2
        else:
            result_game = topic.get_avgresult_block(manager, mixgame_type)
            # общий процент по блоку
            result_all = result_game

        topic_result.append({
                "time": topic_time, 
                "academy": result_academy, 
                "game": result_game,
                "result_all": result_all,
            })

        all_results.append(topic_result)

    return render(request, 'topic_detail.html', {
        'all_results': all_results,
        'headers': headers, 
        'parent_block': parent_block,
    })


