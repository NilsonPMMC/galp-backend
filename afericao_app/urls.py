# /opt/galp-backend/afericao_app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 1. Cria o roteador
router = DefaultRouter()

# 2. Registra nossos ViewSets. O DRF cuidará de criar as rotas
# (ex: GET, POST, PUT, DELETE) automaticamente.
# '/api/centros/' -> CentroResponsabilidadeViewSet
router.register(r'centros', views.CentroResponsabilidadeViewSet)
# '/api/afericoes/' -> AfericaoViewSet
router.register(r'afericoes', views.AfericaoViewSet)

# 3. Define as URLs do app
urlpatterns = [
    # Inclui as rotas geradas pelo roteador
    path('', include(router.urls)),
    
    # Adiciona nossa URL de login customizada
    # '/api/login/' -> CustomAuthToken
    path('login/', views.CustomAuthToken.as_view(), name='api_login'),
]