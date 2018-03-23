# -*- coding: utf-8 -*-

import base64
from copy import deepcopy
from datetime import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.db.models import Max, Count, Sum, Avg

# import xlrd
import xlwt
import math
# from xlutils.copy import copy

from HotKeyStat.models import (
    Learner, Block, TypeResults, Result, Organizations, Manager
    )
from .forms import LearnerFilterForm

# Create your views here.

# стили форматирования для вывода в отчет

style_none = xlwt.easyxf('''font: name Calibri, height 200, color_index black;
    border: left 0, right 0, top 0, bottom 0;
    alignment: horz CENTER, vert CENTER;
    align: wrap 1
''')
style_right = deepcopy(style_none)
style_right.borders.right = 1
style_right_left_text = deepcopy(style_right)
style_right_left_text.alignment.horz = 1
style_left = deepcopy(style_none)
style_left.borders.left = 1

# нижняя граница текст жирно
style_bold_bottom_gray = xlwt.easyxf('''font: name Calibri, height 200, color_index black, bold on;
    border: left 0, right 0, top 0, bottom 1;
    alignment: horz CENTER, vert CENTER;
    pattern: pattern 1, pattern_fore_colour 67;
    align: wrap 1;
''')
style_bold_bottom_green = deepcopy(style_bold_bottom_gray)
style_bold_bottom_green.pattern.pattern_fore_colour = 42
style_bold_bottom_pink = deepcopy(style_bold_bottom_gray)
style_bold_bottom_pink.pattern.pattern_fore_colour = 26
style_bottom_gray = deepcopy(style_bold_bottom_gray)
style_bottom_gray.font.bold = 0
style_bottom_gray.alignment.horz = 1
style_bottom_gray.alignment.wrap = 0
style_bottom_right_gray = deepcopy(style_bottom_gray)
style_bottom_right_gray.borders.right = 1

# правая и нижняя граница текст жирно
style_bold_bottom_right_pink = deepcopy(style_bold_bottom_gray)
style_bold_bottom_right_pink.borders.right = 1
style_bold_bottom_right_pink.pattern.pattern_fore_colour = 26
style_bold_bottom_right_green = deepcopy(style_bold_bottom_gray)
style_bold_bottom_right_green.borders.right = 1
style_bold_bottom_right_green.pattern.pattern_fore_colour = 42

# левая и нижняя граница текст жирно
style_bold_bottom_left_pink = deepcopy(style_bold_bottom_gray)
style_bold_bottom_left_pink.borders.left = 1
style_bold_bottom_left_pink.pattern.pattern_fore_colour = 26
style_bold_bottom_left_green = deepcopy(style_bold_bottom_gray)
style_bold_bottom_left_green.borders.left = 1
style_bold_bottom_left_green.pattern.pattern_fore_colour = 42

# Левая, правая и нижняя граница - текст жирно
style_bold_left_right_pink = deepcopy(style_bold_bottom_left_pink)
style_bold_left_right_pink.borders.right = 1
style_bold_left_right_green = deepcopy(style_bold_bottom_left_green)
style_bold_left_right_green.borders.left = 1

# Нижняя граница, нежирный текст
style_bottom_green = deepcopy(style_bold_bottom_green)
style_bottom_green.font.bold = 0
style_bottom_pink = deepcopy(style_bold_bottom_pink)
style_bottom_pink.font.bold = 0

# Нижняя и правая граница, нежирный текст
style_bottom_right_green = deepcopy(style_bold_bottom_green)
style_bottom_right_green.borders.right = 1
style_bottom_right_green.font.bold = 0
style_bottom_right_pink = deepcopy(style_bold_bottom_pink)
style_bottom_right_pink.borders.right = 1
style_bottom_right_pink.font.bold = 0

# Нижняя и левая граница, нежирный текст
style_bottom_left_green = deepcopy(style_bold_bottom_green)
style_bottom_left_green.borders.left = 1
style_bottom_left_green.font.bold = 0
style_bottom_left_pink = deepcopy(style_bold_bottom_pink)
style_bottom_left_pink.borders.left = 1
style_bottom_left_pink.font.bold = 0

# Нижняя, правая и левая граница, нежирный текст
style_left_right_green = deepcopy(style_bold_left_right_green)
style_left_right_green.font.bold = 0
style_left_right_pink = deepcopy(style_bold_left_right_pink)
style_left_right_pink.font.bold = 0


def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor 
    # s = base64.b64decode(b64_string)
    return base64.b64decode(inp.translate(dict(zip(map(ord, u'-_'), u'+/'))))


def get_time_str(excercise_time):
    u"""
    Возвращает время ученика в формате "Nmin Ms"
    """
    excercise_time_str = "0"
    if excercise_time > 60:
        excercise_time_sec = excercise_time%60
        excercise_time_min = excercise_time/60
        excercise_time_str = str(int(excercise_time_min)) + "min " + str(int(excercise_time_sec)) + "sес"
    elif excercise_time > 0:
        excercise_time_str = str(int(excercise_time)) + "s"
    
    return excercise_time_str


# @permission_required('HotKeyStat.view_statistic')
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



# @permission_required('HotKeyStat.view_statistic')
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
    form = LearnerFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data["date_from"]:
            learners = learners.filter(date_reg__gte=form.cleaned_data["date_from"])
        if form.cleaned_data[u"date_by"]:
            learners = learners.filter(date_reg__lte=form.cleaned_data[u"date_by"])

    order = u'surname'
    if request.GET.get('order', None) :
        order = request.GET['order']
    # Списки учеников, результаты которых доступны текущему проверяющему:
    if order == u'date_reg' or order == u'-date_reg':
        learners = learners.order_by(order, u'surname')
    else:
        learners = learners.order_by(order, u'date_reg')
    
        
    # Списки родительских блоков
    # parent_blocks = Block.get_parent_block()

    academy_type = TypeResults.objects.get(code=0)
    game_type = TypeResults.objects.get(code=1)
    mixgame_type = TypeResults.objects.get(code=2)

    # Список редультатов всех учеников
    all_results = []
    # список заголовков таблицы
    headers = [u'Name', u'E-mail', u'Start Date', u'Overall Progress', u'Graph', u'Excel Excercise']
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
        time = get_time_str(learner.get_learner_avgtime(game_type))
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
        all_max_percent = 2* maxkey_academy + maxkey_mixgame
        if all_max_percent and all_max_percent > 0:
            all_percent = 100.00*(all_percent/all_max_percent)

        # Excel Excercise
        excercise_percent = learner.get_result_excercise()
        excercise_time = get_time_str(learner.get_time_excercise())
        # excercise_time = learner.get_time_excercise()


        learner_results.append( 
            {
                "academy": academy_percent, 
                "game": game_percent, 
                "time": time,
                "all_percent": all_percent, 
                "excercise_percent": excercise_percent,
                "excercise_time": excercise_time,
            }
        )
        # learner_results.append(results)
        all_results.append(learner_results)
    
    return render(request, 'progress.html', {
        'all_results': all_results,
        'headers': headers,
        'order': order,
        'form': form,
    })


# @permission_required('HotKeyStat.view_statistic')
def progress_block(request):
    u'''
    отчет Прогресс по блокам
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    date_from = None
    date_from_s = None
    date_by = None
    date_by_s = None
    order = u'surname'
    if request.GET.get('order', None) :
        order = request.GET['order']
    if request.GET.get('date_from', None) :
        date_from = request.GET['date_from']
        date_from_s = datetime.strptime(date_from, "%Y-%m-%d").strftime("%m/%d/%Y")
    if request.GET.get('date_by', None) :
        date_by = request.GET['date_by']
        date_by_s = datetime.strptime(date_by, "%Y-%m-%d").strftime("%m/%d/%Y")

    # Списки учеников, результаты которых доступны текущему проверяющему:
    learners = manager.get_learner_list()
    # Применяем фильры по дате
    if date_from:
        learners = learners.filter(date_reg__gte=date_from)
    if date_by:
        learners = learners.filter(date_reg__lte=date_by)
    learners = learners.order_by(order)
    
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
                time = get_time_str(block.get_avgtime_block(learner, game_type))
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
        'order': order,
        'date_from': date_from,
        'date_by': date_by,
        'date_from_s': date_from_s,
        'date_by_s': date_by_s,
    })    


# @permission_required('HotKeyStat.view_statistic')
def progress_topic(request, block_id):
    u'''
    отчет Прогресс внутри блока (по топикам)
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего наблюдателя.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    
    date_from = None
    date_from_s = None
    date_by = None
    date_by_s = None
    order = u'surname'
    if request.GET.get('order', None) :
        order = request.GET['order']
    if request.GET.get('date_from', None) :
        date_from = request.GET['date_from']
        date_from_s = datetime.strptime(date_from, "%Y-%m-%d").strftime("%m/%d/%Y")
    if request.GET.get('date_by', None) :
        date_by = request.GET['date_by']
        date_by_s = datetime.strptime(date_by, "%Y-%m-%d").strftime("%m/%d/%Y")
 
    # Списки учеников, результаты которых доступны текущему проверяющему:
    learners = manager.get_learner_list()
    # Применяем фильры по дате
    if date_from:
        learners = learners.filter(date_reg__gte=date_from)
    if date_by:
        learners = learners.filter(date_reg__lte=date_by)
    learners = learners.order_by(order)


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
        'order': order,
        'date_from': date_from,
        'date_by': date_by,
        'date_from_s': date_from_s,
        'date_by_s': date_by_s,
    })


# @permission_required('HotKeyStat.view_statistic')
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

    headers = [u'Topics', u'Average Time Spent', u'Overall Progress', u'Graph']
    all_results = []

    for block in parent_blocks:
        result_academy = 0
        result_game = 0
        result_all = 0

        block_result = []
        block_result.append(block)
        if block.number_block != '500':
            block_time = 0
            block_time = get_time_str(block.get_time_block(manager, game_type))
            result_academy = block.get_avgresult_block(manager, academy_type)
            result_game = block.get_avgresult_block(manager, game_type)
            # общий процент по блоку
            result_all = (result_academy + result_game)/2
        else:
            result_game = block.get_avgresult_block(manager, mixgame_type)
            block_time = get_time_str(block.get_time_block(manager, mixgame_type))
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


# @permission_required('HotKeyStat.view_statistic')
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
    # блок, топики которого мы раскрывaем
    parent_block = get_object_or_404(Block, id=block_id)
    # блок mixgame
    block_mixgame = get_object_or_404(Block, number_block = '500')
    # Списки топиков родительского блока
    topics = parent_block.get_topic()

    # типы результатов
    academy_type = TypeResults.objects.get(code=0)
    game_type = TypeResults.objects.get(code=1)
    mixgame_type = TypeResults.objects.get(code=2)


    headers = [u'Topics', u'Average Time Spent', u'Overall Progress', u'Graph']
    all_results = []

    for topic in topics:
        result_academy = 0
        result_game = 0
        result_all = 0
        topic_time = 0

        topic_result = []
        topic_result.append(topic)
        if topic != block_mixgame and topic.parent != block_mixgame:
            topic_time = get_time_str(topic.get_time_block(manager, game_type))
            result_academy = topic.get_avgresult_block(manager, academy_type)
            result_game = topic.get_avgresult_block(manager, game_type)
            # общий процент по блоку
            result_all = (result_academy + result_game)/2
        else:
            result_game = topic.get_avgresult_block(manager, mixgame_type)
            topic_time = get_time_str(topic.get_time_block(manager, mixgame_type))
            # общий процент по блоку
            result_all = result_game

        topic_result.append({
                "time": topic_time, 
                "academy": result_academy, 
                "game": result_game,
                "result_all": result_all,
            })

        all_results.append(topic_result)

    return render(request, 'block_detail.html', {
        'all_results': all_results,
        'headers': headers, 
        'parent_block': parent_block,
    })


def result_save(request):
    u'''
    Запись результатов ученика
    '''
    if request.GET['results'] :
        results = request.GET['results']
        results = base64_url_decode(results)
        results_list = str(results).split(u';')
        organization = None

        # Первый элемент списка - данные ученика
        learner_info = results_list[0].split(u',')
        if learner_info:
            org_name = learner_info[0][2:]
            learner_name = learner_info[1]
            learner_email = learner_info[2]
            if learner_info[3]:
                learner_date = datetime.date(datetime.strptime(learner_info[3], '%d.%m.%Y') )
            # Проверяем, есть ли организация в справочнике
            organization = get_object_or_404(Organizations, name=org_name)
            # Вычисляем блок - упраженение excel excercise
            block_excercise = get_object_or_404(Block, number_block='600')
        # Проверяем есть ли в БД ученик с указанным e-mail
        learner, _ = Learner.objects.get_or_create(
            org=organization,
            email=learner_email,
        )
        if learner:
            learner.name=learner_name
            learner.date_reg=learner_date
            learner.save()

        if organization and learner:
            for i, result in enumerate(results_list):
                if i > 0 and len(result) > 1:
                    total = 0
                    correct = 0
                    key_count = 0
                    learner_res = None
                    type_result = None
                    date_result = datetime.now()
                    # Если последний элемент списка - убрать кавычку в конце
                    if i == len(results_list) - 1:
                        result = result[0:-1]
                    learner_res = result.split(u',')
                    # print("learner_res=", learner_res)
                    # Результаты ученика
                    number_block = learner_res[0]
                    try:
                        time_result = float(learner_res[1])
                    except:
                        time_result = 0
                    try:
                        correct = int(learner_res[2])
                    except:
                        pass
                    try:
                        total = int(learner_res[3])
                    except:
                        pass
                    if learner_res[4]:
                         date_result = datetime.date(datetime.strptime(learner_res[4], '%d.%m.%Y') )
                    try:
                        typeresult = int(learner_res[6])
                    except:
                        pass
                    # Определяем кол-во ключей 
                    # если mixgame (кол-во верных ответов=кол-во всего ответов и кол-во всего ответов > 20)
                    if (typeresult == 2 and
                        (total and correct and total == correct) and 
                        ((total >= 20 and number_block != '503') or (total >= 14 and number_block == '503'))):
                            key_count = 5
                    # если game (кол-во верных ответов=кол-во всего ответов)
                    elif (typeresult == 1 and total and correct and total == correct and total > 0) :
                        key_count = 1
                    # академия
                    elif typeresult == 0:
                        key_count = 1
                    # Определяем блок, тип результата
                    block = Block.objects.filter(number_block=number_block).first()
                    type_result = TypeResults.objects.filter(code=typeresult).first()

                    # Записываем результаты по блоку 
                    if block:   
                        result, _ = Result.objects.get_or_create(
                            learner=learner,
                            block=block,
                            type_result=type_result,
                        )
                        if result:
                            result.date_result = date_result
                            result.key_count = key_count
                            result.correct = correct
                            result.total = total
                            result.time_result = time_result 

                            result.save()
                    # print(result, 'type_result=', type_result, 'total=', total, 'correct=', correct, key_count)
        
        # пересчитываем ранги учеников
        learners_results = Result.objects.filter(
            learner__org=organization, 
            block=block_excercise
        ).order_by('-correct', 'time_result')
        for learner_rank, learner_res in enumerate(learners_results, start=1):
            learner_res.learner.rank = learner_rank
            learner_res.learner.save()

    return redirect('hkstat-champions', organization, learner)


def champions(request, org=None, learner=None):
    u'''
    Статистика для учеников
    '''
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера или ученика.
    if manager is None and learner is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    # org_name = "PwC"
    # organization = get_object_or_404(Organizations, name=org_name)
    if org:
        organization = org
        state = 'manager'
    else:
        organization = get_object_or_404(Organizations, id = manager.org.id)
        state = 'learner'

    block_excercise = get_object_or_404(Block, number_block='600')
    percent = 0
    places = []

    order = u'rank'
    if request.GET.get('order', None) :
        order = request.GET['order']
    # Список учеников организации
    learners = organization.get_learner_org().order_by(order)
    results = Result.objects.filter(
        block=block_excercise,
        learner__in=learners
    ).order_by("-correct", "time_result")[:3]

    for result in results:
        if result.total  and result.correct and result.correct > 0:
            percent = 100.00*(result.correct/result.total)
        time_result = get_time_str(result.time_result)
        places.append(
            {'learner': result.learner, 'percent': percent, 'time': time_result}
        )
    # Меняем местами 1 и 2 место - для вывода 1го места по центру
    places[0], places[1] = places[1], places[0]

    # Список редультатов всех учеников
    all_results = []
    # список заголовков таблицы
    headers = [u'Ranking', u'Date',  u'First Name',  u'Last Name', u'Collected Keys', u'Excel Excercise']

    for learner in learners:
        # список результатов каждого ученика
        learner_results = []
        learner_results.append(learner)

        # Excel Excercise
        excercise_percent = learner.get_result_excercise()
        excercise_time = get_time_str(learner.get_time_excercise())

        key_count = learner.get_key_count()

        learner_results.append( 
            {
                "rank": learner.rank,
                "key_count": key_count,
                "excercise_percent": excercise_percent,
                "excercise_time": excercise_time,
            }
        )
        all_results.append(learner_results)

     
    return render(request, 'champions.html', {
        'places': places,
        'all_results': all_results,
        'headers': headers,
        'organization': organization,
        'order': order,
        'state': state,
    })


# @permission_required('HotKeyStat.view_statistic')
def progress_report(request):
    u"""
    Отчетная форма для Progress(main)
    """
    user = request.user
    manager = user.manager
    # Проверяем права доступа текущего менеджера.
    if manager is None:
        return HttpResponseForbidden(u"You don't have enough rights. Please contact support")

    # Создание книги excel и страницы в ней
    book = xlwt.Workbook()
    sheet = book.add_sheet('Learner Progress')
    sheet2 = book.add_sheet('Module Details')
    #Убираем колонтитулы
    sheet.set_header_margin(0)
    sheet.set_footer_margin(0)
    sheet.print_scaling=100
    sheet.left_margin=0.41
    # sheet.set_header_str(u"")
    # sheet.set_footer_str(u"")

    # Заполняем данными
    # Списки учеников, результаты которых доступны текущему проверяющему:
    learners = manager.get_learner_list()
    
    if request.GET.get('date_from', None) :
        date_from = request.GET['date_from']
        learners = learners.filter(date_reg__gte=date_from)
    if request.GET.get('date_by', None) :
        date_by = request.GET['date_by']
        learners = learners.filter(date_reg__lte=date_by)

    learners = learners.order_by(u'surname')
    
    # Списки родительских блоков
    parent_blocks = Block.get_parent_block()
    block_mixgame = get_object_or_404(Block, number_block = '500')

    academy_type = TypeResults.objects.get(code=0)
    game_type = TypeResults.objects.get(code=1)
    mixgame_type = TypeResults.objects.get(code=2)

    # список заголовков таблицы
    headers = [u'First Name', u'Last Name', u'E-mail', u'Start Date', u'Excel Exercise', u'Overall Progress']
    
    # проценты ученика по академии, игре, mixGame и общий процент
    academy_percent = 0
    game_percent = 0
    mixgame_percent = 0

    # 1й лист 
    # Выводим шапку отчета
    for i, header in enumerate(headers):
        if header == u'Overall Progress':
            sheet.col(i).width = 3000
            sheet.col(i + 1).width = 3000
            sheet.col(i + 2).width = 3400
            sheet.write_merge(0, 0, i + 1, i + 3, header, style_bold_left_right_green)
            sheet.write(1, i + 1, u'Academy,%', style_bold_bottom_left_green)
            sheet.write(1, i + 2, u'Game,%', style_bold_bottom_green)
            sheet.write(1, i + 3, u'Time Spent', style_bold_bottom_right_green)
        elif header == u'Excel Exercise':
            sheet.col(i).width = 2500
            sheet.col(i + 1).width = 3000
            sheet.write_merge(0, 0, i, i + 1, header, style_bold_left_right_pink)
            sheet.write(1, i, u'Time', style_bold_bottom_left_pink)
            sheet.write(1, i + 1, u'Accuracy, %', style_bold_bottom_right_pink)
        else:
            sheet.col(i).width = 4000
            sheet.write_merge(0, 1, i, i, header, style_bold_bottom_gray)
    
    # Выводим данные
    n = 2
    for i, learner in enumerate(learners):
        # список результатов каждого ученика
        sheet.write(n, 0, learner.name, style_right)
        sheet.write(n, 1, learner.surname, style_right)
        sheet.write(n, 2, learner.email, style_right)
        sheet.write(n, 3, learner.date_reg.strftime("%d.%m.%Y"), style_right)
        #Excel Excercise
        time = learner.get_time_excercise()
        sheet.write(n, 4, '%.2f' % time, style_right)
        academy_percent = learner.get_result_excercise()
        sheet.write(n, 5, '%.2f' % academy_percent + r'%', style_left)
        # Overall Progress
        academy_percent = learner.get_result_type(academy_type)
        sheet.write(n, 6, '%.2f' % academy_percent + r'%', style_left)
        game_percent = learner.get_result_type(game_type)
        sheet.write(n, 7, '%.2f' % game_percent + r'%', style_none)
        time = learner.get_learner_avgtime(game_type)
        sheet.write(n, 8, '%.2f' % time, style_right)

        # номер столбца, с которого начинаются результаты по этапам
        k = 9
        for j, block in enumerate(parent_blocks):
            # k += j
            if i == 0:
                sheet.col(k).width = 3000
                if block.number_block != '500':
                    sheet.col(k + 1).width = 3000
                    sheet.col(k + 2).width = 3000
                    if j%2 > 0:
                        sheet.write_merge(0, 0, k, k + 2, '%s.%s' %(block.num, block.name), style_left_right_green)
                        sheet.write(1, k, u'Academy,%', style_bottom_left_green)
                        sheet.write(1, k + 1, u'Game,%', style_bottom_green)
                        sheet.write(1, k + 2 , u'Time Spent', style_bottom_right_green)
                    else:
                        sheet.write_merge(0, 0, k, k + 2, '%s.%s' %(block.num, block.name), style_left_right_pink)
                        sheet.write(1, k, u'Academy,%', style_bottom_left_pink)
                        sheet.write(1, k + 1, u'Game,%', style_bottom_pink)
                        sheet.write(1, k + 2 , u'Time Spent', style_bottom_right_pink)
                else:
                    sheet.write(0, k, '%s.%s' %(block.num, block.name), style_left_right_pink)
                    sheet.write(1, k, u'%', style_bottom_right_pink)
            # Игра или академия
            if block.number_block != '500':
                academy_percent = block.get_percent_block(learner, academy_type)
                sheet.write(n, k, '%.2f' % academy_percent + r'%', style_left)
                game_percent = block.get_percent_block(learner, game_type)
                sheet.write(n, k +1 , '%.2f' % game_percent + r'%', style_none)
                time = block.get_avgtime_block(learner, game_type)
                sheet.write(n, k + 2, '%.2f' % time + r'%', style_right)
                k += 3
            # MixGame
            else:
                game_percent = block.get_percent_block(learner, mixgame_type)
                sheet.write(n, k, '%.2f' % game_percent + r'%', style_right) 
                k += 2
        n += 1    

    # 2й лист    
    headers = [u'Topics', u'Academy, %', u'Game, %', u'Time Spent']
    
    for i, header in enumerate(headers):
        if i == 0 :
            sheet2.col(i).width = 4000
            sheet2.col(i + 1).width = 9000
            sheet2.write_merge(0,0,0,1, header, style_bold_bottom_right_pink)
        elif i == 3:
            sheet2.col(i + 1).width = 3000
            sheet2.write(0, i + 1 , header, style_bold_bottom_right_pink)
            sheet2.write(1, i + 1 , "", style_bottom_right_gray)
        else:
            sheet2.col(i + 1).width = 3000
            sheet2.write(0, i + 1 , header, style_bold_bottom_right_pink)
            sheet2.write(1, i + 1 , "", style_bottom_gray)
    
    sheet2.write_merge(1, 1, 0, 1, 'Overall Progress', style_bottom_gray)
    nstr = 2
    for j, block in enumerate(parent_blocks):
        sheet2.write_merge(nstr, nstr, 0, 1, '%s.%s' %(block.num, block.name), style_right_left_text)
        result_academy = 0
        result_game = 0

        if block.number_block != '500':
            block_time = 0
            result_academy = block.get_avgresult_block(manager, academy_type)
            sheet2.write(nstr, 2, '%.2f' %result_academy + r'%', style_none)
            result_game = block.get_avgresult_block(manager, game_type)
            sheet2.write(nstr, 3, '%.2f' %result_game + r'%', style_none)
            block_time = block.get_time_block(manager, game_type)
            sheet2.write(nstr, 4, '%.2f' %block_time, style_right)
        else:
            
            sheet2.write(nstr, 2, '-' , style_none)
            result_game = block.get_avgresult_block(manager, mixgame_type)
            sheet2.write(nstr, 3, '%.2f' %result_game + r'%', style_none)
            # block_time = block.get_time_block(manager, mixgame_type)
            sheet2.write(nstr, 4, '-', style_right)

        # Дочерние топики
        topics = block.get_topic()
        for k, topic in enumerate(topics, start=1):
            sheet2.write(nstr + k, 1, '%s.%s' %(topic.num, topic.name), style_right_left_text)
            result_academy = 0
            result_game = 0
            topic_time = 0

            if topic != block_mixgame and topic.parent != block_mixgame:
                result_academy = topic.get_avgresult_block(manager, academy_type)
                sheet2.write(nstr + k, 2, '%.2f' %result_academy + r'%', style_none)
                result_game = topic.get_avgresult_block(manager, game_type)
                sheet2.write(nstr + k, 3, '%.2f' %result_game + r'%', style_none)
                topic_time = topic.get_time_block(manager, game_type)
                sheet2.write(nstr + k, 4, '%.2f' %topic_time, style_right)
            else:
                sheet2.write(nstr + k, 2, '-' , style_none)
                result_game = topic.get_avgresult_block(manager, mixgame_type)
                sheet2.write(nstr + k, 3, '%.2f' %result_game + r'%', style_none)
                # topic_time = topic.get_time_block(manager, mixgame_type)
                sheet2.write(nstr + k, 4, '-', style_right)
        sheet2.write_merge(nstr + k + 1, nstr + k + 1, 0, 1, '', style_right)
        sheet2.write(nstr + k + 1, 4, '', style_right)
        nstr += k + 2


    response = HttpResponse(content_type='application/ms-excel')
    dt = datetime.now().strftime("%y%m%d %H:%M")
    file_name = dt + '_progress_main'
    file_name += '.xls'
    response['Content-Disposition'] = 'attachment; filename=' + file_name
    book.save(response)

    return response

