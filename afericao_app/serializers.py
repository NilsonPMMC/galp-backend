# /opt/galp-backend/afericao_app/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PerfilUsuario, CentroResponsabilidade, Afericao

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo User (focado em exibir nomes).
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o PerfilUsuario, que inclui os dados do User.
    """
    # Usamos o UserSerializer para aninhar os dados do usuário (nome, email)
    # dentro do perfil. 'read_only=True' significa que será exibido,
    # mas não pode ser editado diretamente por aqui.
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PerfilUsuario
        fields = ['user', 'cpf', 'telefone', 'perfil']

class CentroResponsabilidadeSerializer(serializers.ModelSerializer):
    """
    Serializer para listar os Centros de Responsabilidade.
    
    Este será usado pelo Fiscal no app para escolher qual local vistoriar.
    Inclui o nome do fiscal padrão para referência.
    """
    # 'StringRelatedField' é uma forma simples de exibir o '__str__' 
    # do modelo relacionado (ex: "Francisco Vieira...").
    fiscal_padrao = serializers.StringRelatedField()
    
    class Meta:
        model = CentroResponsabilidade
        fields = [
            'cod_cr', 
            'nome_cr', 
            'endereco_cr', 
            'secretaria_responsavel', 
            'postos_trab_previstos',
            'fiscal_padrao',
        ]

class AfericaoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer especial para CRIAR uma nova Aferição (POST).
    
    Ele é mais simples e espera receber apenas os IDs (chaves primárias)
    para o fiscal e o centro_responsabilidade.
    """
    # Usamos 'PrimaryKeyRelatedField' para que a API espere um ID simples.
    # Ex: "fiscal": 1, "centro_responsabilidade": 900
    
    # O 'HiddenField' pega o usuário logado (fiscal) automaticamente
    # a partir do 'contexto' da view, em vez de pedir no JSON.
    fiscal = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    centro_responsabilidade = serializers.PrimaryKeyRelatedField(
        queryset=CentroResponsabilidade.objects.all()
    )

    class Meta:
        model = Afericao
        # Lista de todos os campos que o Fiscal deve enviar no formulário
        fields = [
            'cod_afericao',
            'fiscal',
            'centro_responsabilidade',
            'data_afericao',
            'postos_prev',
            'postos_ocup',
            'postos_obs',
            'serv_nota',
            'mat_qt_nota',
            'mat_ql_nota',
            'mat_rep_nota',
            'mat_obs',
            'uso_maq',
            'maq_obs',
            'uso_epi',
            'epi_obs',
            'status_revisao', # Incluído para o requisito D+1
        ]
        
    def create(self, validated_data):
        # Aqui podemos adicionar lógicas antes de salvar, se necessário.
        # Por exemplo, garantir que 'postos_prev' seja preenchido
        # automaticamente com base no CR selecionado.
        
        cr = validated_data.get('centro_responsabilidade')
        if cr and not validated_data.get('postos_prev'):
            validated_data['postos_prev'] = cr.postos_trab_previstos
            
        return Afericao.objects.create(**validated_data)

class AfericaoListSerializer(serializers.ModelSerializer):
    """
    Serializer para LISTAR as aferições já feitas.
    
    Mostra os nomes (strings) em vez de apenas IDs,
    facilitando a leitura no frontend.
    """
    fiscal = serializers.StringRelatedField()
    centro_responsabilidade = serializers.StringRelatedField()
    
    class Meta:
        model = Afericao
        # Mostra apenas os campos principais na listagem
        fields = [
            'cod_afericao', 
            'data_afericao',
            'centro_responsabilidade', 
            'fiscal', 
            'serv_nota', 
            'desempenho_serv'
        ]

class AfericaoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para ver (GET), atualizar (PUT) ou
    revisar (PATCH) uma única Aferição.
    """
    # fiscal e centro_responsabilidade são tratados como IDs

    class Meta:
        model = Afericao
        # Lista todos os campos que podem ser lidos ou editados
        fields = [
            'cod_afericao',
            'fiscal',
            'centro_responsabilidade',
            'data_ultima_revisao',
            'postos_prev',
            'postos_ocup',
            'postos_obs',
            'serv_nota',
            'mat_qt_nota',
            'mat_ql_nota',
            'mat_rep_nota',
            'mat_obs',
            'uso_maq',
            'maq_obs',
            'uso_epi',
            'epi_obs',
            'status_revisao', # Para o D+1
            # Campos de desempenho (apenas leitura)
            'desempenho_serv',
            'desempenho_mat_qt',
            'desempenho_mat_ql',
            'desempenho_mat_rep',
        ]

        # Define campos que não devem ser editáveis no PUT/PATCH
        read_only_fields = [
            'cod_afericao', 
            'fiscal', 
            'centro_responsabilidade', 
            'data_afericao',
            'data_ultima_revisao',
            'desempenho_serv',
            'desempenho_mat_qt',
            'desempenho_mat_ql',
            'desempenho_mat_rep',
        ]