from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'', views.index, name='HotKeyStat-index'),
    url(r'^ProgressOverview/$', views.progress, name='hkstat-progress'),
    url(r"^ProgressOverview/block/(?P<block_id>\d+)/$", views.progress_block, name='hkstat-progress-block'),
    url(r'^ModuleDetails/$', views.module_details, name='hkstat-module-details'),
    url(r"^ModuleDetails/block/(?P<block_id>\d+)/$", views.learner_details, name='hkstat-learner-details'),
    # url(r'^LearnerDetails/$', views.learner_details, name='hkstat-learner-details'),
]