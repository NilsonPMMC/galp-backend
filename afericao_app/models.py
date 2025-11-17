from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --- Modelo de Usuários ---
# Expande o User padrão do Django com base no BD_Usuários.csv [cite: 5]

class PerfilUsuario(models.Model):
    """
    Armazena informações adicionais do usuário (Fiscal, Coordenador, Gestor),
    ligado ao sistema de autenticação do Django.
    """
    PERFIL_CHOICES = [
        # Valores do BD_Usuários.csv
        ('Fiscal de Equipamento', 'Fiscal de Equipamento'),
        ('Coordenador', 'Coordenador'),

        # Requisito SMGCP e outros
        ('Gestor Contrato', 'Gestor Contrato'),
        ('Fiscal', 'Fiscal'), # Mantemos caso seja útil
    ]

    # Link com o User nativo do Django (para login/senha)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    # Campos do BD_Usuários.csv
    cpf = models.CharField(max_length=11, unique=True, help_text="Apenas números")
    telefone = models.CharField(max_length=20, blank=True, null=True)

    # AQUI A MUDANÇA: Aumentado de 20 para 50
    perfil = models.CharField(max_length=50, choices=PERFIL_CHOICES)

    def __str__(self):
        # Retorna o nome completo do User (definido no Admin) ou o username
        return self.user.get_full_name() or self.user.username

# --- Modelo de Locais ---
# Mapeamento do BD_CR.csv [cite: 2-4]

class CentroResponsabilidade(models.Model):
    """
    Representa um local/prédio a ser fiscalizado (Equipamento Público).
    """
    cod_cr = models.IntegerField(primary_key=True, help_text="Código do Centro de Responsabilidade")
    nome_cr = models.CharField(max_length=255)
    endereco_cr = models.CharField(max_length=500, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    secretaria_responsavel = models.CharField(max_length=100)
    postos_trab_previstos = models.IntegerField(null=True, blank=True, help_text="Postos previstos no contrato")
    
    # Relações com os usuários
    fiscal_padrao = models.ForeignKey(
        PerfilUsuario, 
        on_delete=models.SET_NULL, 
        related_name='cr_fiscais', 
        null=True, blank=True
    )
    coordenador = models.ForeignKey(
        PerfilUsuario, 
        on_delete=models.SET_NULL, 
        related_name='cr_coordenadores', 
        null=True, blank=True
    )
    gestor_contrato = models.ForeignKey(
        PerfilUsuario, 
        on_delete=models.SET_NULL, 
        related_name='cr_gestores', 
        null=True, blank=True,
        help_text="Gestor a ser notificado por e-mail" # Novo requisito SMGCP
    )

    def __str__(self):
        return f"{self.cod_cr} - {self.nome_cr}"

# --- Modelo Principal de Dados ---
# Mapeamento do BD_Afericoes.csv [cite: 1] e do Formulário [cite: 6-8]

class Afericao(models.Model):
    """
    Registro principal de uma aferição de limpeza.
    """
    # Constantes para Choices
    NOTA_CHOICES = [
        (1, '1 - Péssimo'),
        (2, '2 - Ruim'),
        (3, '3 - Regular'),
        (4, '4 - Bom'),
        (5, '5 - Ótimo'),
    ]
    USO_MAQ_CHOICES = [('Sim', 'Sim'), ('Não', 'Não')]
    USO_EPI_CHOICES = [('Sim', 'Sim'), ('Parcial', 'Parcial'), ('Não', 'Não')]

    # Identificação e Relações
    cod_afericao = models.CharField(max_length=20, primary_key=True, help_text="Ex: 20251112900 (AAAAMMDD + Cod_CR)")
    data_afericao = models.DateTimeField(help_text="Data da aferição (pode ser retroativa)") # <-- MUDANÇA AQUI
    data_ultima_revisao = models.DateTimeField(null=True, blank=True, help_text="Data/hora da última revisão (Requisito D+1)")
    
    fiscal = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, help_text="Fiscal que realizou a aferição")
    centro_responsabilidade = models.ForeignKey(CentroResponsabilidade, on_delete=models.PROTECT)
    
    status_revisao = models.BooleanField(default=False, help_text="Controla se a aferição ainda pode ser revisada")

    # 1. Equipe (Baseado na Seção 2 do formulário [cite: 7])
    postos_prev = models.IntegerField(help_text="Postos previstos (puxado do CR)")
    postos_ocup = models.IntegerField(help_text="Postos ocupados na data")
    postos_obs = models.TextField(blank=True, null=True)

    # 2. Serviço (Baseado na Seção 3 do formulário [cite: 7])
    serv_nota = models.IntegerField(choices=NOTA_CHOICES, help_text="Nota para 'As dependências foram limpas?'")
    
    # 3. Materiais - Consumo (Baseado na Seção 4 do formulário [cite: 7, 8])
    mat_qt_nota = models.IntegerField(choices=NOTA_CHOICES, help_text="Nota para 'Quantidade de materiais atendeu?'")
    mat_ql_nota = models.IntegerField(choices=NOTA_CHOICES, help_text="Nota para 'Qualidade está como prevista?'")
    mat_rep_nota = models.IntegerField(choices=NOTA_CHOICES, help_text="Nota para 'Reposição foi dentro do necessário?'")
    mat_obs = models.TextField(blank=True, null=True, help_text="Observações gerais de materiais de consumo")

    # 4. Materiais - Máquinas (Baseado na Seção 5 do formulário [cite: 8])
    uso_maq = models.CharField(max_length=3, choices=USO_MAQ_CHOICES)
    maq_obs = models.TextField(blank=True, null=True, help_text="Caso afirmativo, qual máquina e onde?")

    # 5. Materiais - EPI (Baseado na Seção 6 do formulário [cite: 8])
    uso_epi = models.CharField(max_length=10, choices=USO_EPI_CHOICES)
    epi_obs = models.TextField(blank=True, null=True)

    # Campos de Desempenho (Calculados automaticamente)
    # Fórmulas baseadas no Modelo de Negócio [cite: 8]
    desempenho_serv = models.FloatField(null=True, blank=True, editable=False)
    desempenho_mat_qt = models.FloatField(null=True, blank=True, editable=False)
    desempenho_mat_ql = models.FloatField(null=True, blank=True, editable=False)
    desempenho_mat_rep = models.FloatField(null=True, blank=True, editable=False)

    def __str__(self):
        return f"Aferição {self.cod_afericao} em {self.data_afericao.strftime('%d/%m/%Y')}"

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para calcular os campos de desempenho
        automaticamente antes de salvar. [cite: 8]
        """
        if self.serv_nota:
            self.desempenho_serv = (self.serv_nota / 5) * 100
        
        if self.mat_qt_nota:
            self.desempenho_mat_qt = (self.mat_qt_nota / 5) * 100
        
        if self.mat_ql_nota:
            self.desempenho_mat_ql = (self.mat_ql_nota / 5) * 100
            
        if self.mat_rep_nota:
            self.desempenho_mat_rep = (self.mat_rep_nota / 5) * 100

        # Atualiza a data da revisão se o objeto estiver sendo modificado (não criado)
        if not self._state.adding:
            self.data_ultima_revisao = timezone.now()

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Aferição"
        verbose_name_plural = "Aferições"
        ordering = ['-data_afericao']