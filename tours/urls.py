from django.urls import path

from tours import views

app_name = 'tours'

urlpatterns = [
    path('', views.excursion_list, name='excursion_list'),
    path('sobre-nosotros/', views.about, name='about'),
    path('excursiones-anteriores/', views.past_excursions, name='past_excursions'),
    path('excursiones/<int:pk>/', views.excursion_detail, name='excursion_detail'),
    path('salidas/<int:slot_id>/reservar/', views.reserve_slot, name='reserve_slot'),
]
