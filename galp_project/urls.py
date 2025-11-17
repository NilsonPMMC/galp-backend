# /opt/galp-backend/galp_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Rota do Admin (que já usamos)
    path('admin/', admin.site.urls),
    
    # 2. Conecta nossa API
    # Qualquer URL que comece com 'api/' será enviada
    # para o arquivo 'afericao_app/urls.py'
    path('api/', include('afericao_app.urls')),
    
    # (Quando o frontend (Vue) estiver pronto, adicionaremos
    # uma rota aqui para servir o index.html dele)
]