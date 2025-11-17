from django.contrib import admin
from .models import PerfilUsuario, CentroResponsabilidade, Afericao

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    """
    Configuração da admin para PerfilUsuario.
    """
    list_display = ('user', 'cpf', 'perfil')
    search_fields = ('user__username', 'user__first_name', 'cpf')
    list_filter = ('perfil',)
    # Faz com que o 'user' (nome, sobrenome) seja editável
    # a partir da tela do PerfilUsuario.
    raw_id_fields = ('user',) 

@admin.register(CentroResponsabilidade)
class CentroResponsabilidadeAdmin(admin.ModelAdmin):
    """
    Configuração da admin para CentroResponsabilidade.
    """
    list_display = (
        'cod_cr', 
        'nome_cr', 
        'secretaria_responsavel', 
        'fiscal_padrao', 
        'gestor_contrato'
    )
    search_fields = ('nome_cr', 'cod_cr')
    list_filter = ('secretaria_responsavel',)
    raw_id_fields = ('fiscal_padrao', 'coordenador', 'gestor_contrato')

@admin.register(Afericao)
class AfericaoAdmin(admin.ModelAdmin):
    """
    Configuração da admin para Afericao.
    """
    list_display = (
        'cod_afericao', 
        'centro_responsabilidade', 
        'fiscal', 
        'data_afericao', 
        'serv_nota'
    )
    search_fields = ('cod_afericao', 'centro_responsabilidade__nome_cr', 'fiscal__user__username')
    list_filter = ('data_afericao', 'fiscal', 'centro_responsabilidade__secretaria_responsavel')
    
    # Campos calculados ou definidos por código não devem ser editáveis
    readonly_fields = (
        'data_afericao', 
        'data_ultima_revisao',
        'desempenho_serv',
        'desempenho_mat_qt',
        'desempenho_mat_ql',
        'desempenho_mat_rep',
    )
    raw_id_fields = ('fiscal', 'centro_responsabilidade')