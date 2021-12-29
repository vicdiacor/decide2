from django.urls import path
from . import views


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('union', views.GroupOperations.as_view(), name='group_union'),
    path('intersection', views.GroupOperations.as_view(),
         name='group_intersection'),
    path('difference', views.GroupOperations.as_view(),
         name='group_difference'),
]
