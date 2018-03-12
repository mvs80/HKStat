from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='HotKeyStat-index'),
    url(r'ProgressOverview/$', views.progress, name='hkstat-progress'),
    url(r"^ProgressOverview/block/$", views.progress_block, name='hkstat-progress-block'),
    url(r"^ProgressOverview/block/(?P<block_id>\d+)/$", views.progress_topic, name='hkstat-progress-topic'),
    url(r'^ModuleDetails/$', views.module_details, name='hkstat-module-details'),
    url(r"^ModuleDetails/block/(?P<block_id>\d+)/$", views.block_details, name='hkstat-block-details'),
    url(r"^result/$", views.result_save, name='result-save'),
    url(r'^ProgressOverview/report/$', views.progress_report, name='hkstat-progress-report'),
]