# /opt/galp-backend/afericao_app/views.py

from rest_framework import viewsets, permissions, decorators
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .models import CentroResponsabilidade, Afericao, PerfilUsuario
from .serializers import (
    CentroResponsabilidadeSerializer,
    AfericaoCreateSerializer,
    AfericaoListSerializer,
    AfericaoDetailSerializer,
    PerfilUsuarioSerializer
)

# --- 1. View de Autenticação (Login) ---

class CustomAuthToken(ObtainAuthToken):
    """
    Endpoint de login customizado.
    
    Recebe 'username' (que será o CPF) e 'password'.
    Retorna o Token e também os dados do Perfil do usuário (Nome, Perfil),
    para que o frontend possa exibir "Olá, Francisco".
    """
    def post(self, request, *args, **kwargs):
        # Tenta obter o token padrão
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Busca o perfil do usuário para retornar dados extras
        try:
            perfil = PerfilUsuario.objects.get(user=user)
            perfil_data = PerfilUsuarioSerializer(perfil).data
        except PerfilUsuario.DoesNotExist:
            perfil_data = None

        # Retorna o token E os dados do perfil
        return Response({
            'token': token.key,
            'user_profile': perfil_data
        })

# --- 2. ViewSet para Centros de Responsabilidade ---

class CentroResponsabilidadeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint que permite aos usuários (logados)
    visualizar os Centros de Responsabilidade. (Apenas Leitura).
    
    O frontend usará isso para mostrar a lista de locais para o fiscal.
    """
    queryset = CentroResponsabilidade.objects.all().order_by('nome_cr')
    serializer_class = CentroResponsabilidadeSerializer
    permission_classes = [permissions.IsAuthenticated] # Só usuários logados podem ver

# --- 3. ViewSet para Aferições ---

class AfericaoViewSet(viewsets.ModelViewSet):
    """
    API endpoint principal para criar (POST) e listar (GET) Aferições.
    """
    queryset = Afericao.objects.all().order_by('-data_afericao')
    permission_classes = [permissions.IsAuthenticated] # Só usuários logados

    @decorators.action(detail=False, methods=['get'])
    def check_exists(self, request):
        """
        Verifica se já existe uma aferição para um CR em uma data específica.
        """
        cod_cr = request.query_params.get('cr')
        data_str = request.query_params.get('data') # Formato YYYY-MM-DD

        if not cod_cr or not data_str:
            return Response(
                {"error": "Parâmetros 'cr' e 'data' são obrigatórios."},
                status=400
            )

        # Filtra pela data (ignorando a hora)
        exists = Afericao.objects.filter(
            centro_responsabilidade__cod_cr=cod_cr,
            data_afericao__date=data_str
        ).exists()

        return Response({"exists": exists})

    def get_serializer_class(self):
        """
        Define qual serializer usar dependendo da ação.
        """
        if self.action == 'create':
            return AfericaoCreateSerializer # Para POST

        if self.action in ['retrieve', 'update', 'partial_update']:
            return AfericaoDetailSerializer # Para GET (detalhe), PUT, PATCH

        return AfericaoListSerializer # Para GET (lista)

    def get_queryset(self):
        """
        Filtra as aferições para que o Fiscal veja apenas as suas.
        (Futuramente, Coordenadores/Gestores poderão ver todas)
        """
        user = self.request.user
        
        try:
            perfil = user.perfilusuario
            if perfil.perfil == 'Fiscal de Equipamento':
                # Fiscal vê apenas as suas aferições
                return Afericao.objects.filter(fiscal=perfil).order_by('-data_afericao')
        except PerfilUsuario.DoesNotExist:
            # Se for um superuser ou alguém sem perfil, retorna vazio por segurança
            return Afericao.objects.none()

        # Padrão: Coordenadores/Gestores (a ser implementado) veem tudo
        return Afericao.objects.all().order_by('-data_afericao')

    def perform_create(self, serializer):
        """
        Passa o 'request.user' (usuário logado) para o contexto
        do serializer, para que o HiddenField 'fiscal' funcione.
        """
        # Busca o PerfilUsuario do usuário logado
        perfil = PerfilUsuario.objects.get(user=self.request.user)
        serializer.save(fiscal=perfil)