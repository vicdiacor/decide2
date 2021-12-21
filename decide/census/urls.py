from django.urls import path, include
from . import views
from .views import ListGroupsView


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('union', views.GroupOperations.GroupUnion.as_view(), name='group_union'),
    path('intersection', views.GroupOperations.GroupIntersection.as_view(),
         name='group_intersection'),
    path('difference', views.GroupOperations.GroupDifference.as_view(),
         name='group_difference'),
     path('groupList', ListGroupsView.as_view())
]
