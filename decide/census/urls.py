from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('union', views.GroupUnion.as_view(), name='group_union'),
    path('intersection', views.GroupIntersection.as_view(),
         name='group_intersection'),
    path('difference', views.GroupDifference.as_view(), name='group_difference'),
]
