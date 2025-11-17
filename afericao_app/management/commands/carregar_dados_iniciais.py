import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from afericao_app.models import PerfilUsuario, CentroResponsabilidade

class Command(BaseCommand):
    help = 'Carrega os dados iniciais dos arquivos BD_Usuários.csv e BD_CR.csv'

    def _clean_float(self, s):
        """Helper para converter strings numéricas formatadas (BR) para float."""
        if not s:
            return None
        try:
            s_cleaned = s.strip()            # 1. Remove espaços
            s_cleaned = s_cleaned.replace('.', '')   # 2. Remove separador de milhar
            s_cleaned = s_cleaned.replace(',', '.')   # 3. Troca vírgula decimal por ponto
            return float(s_cleaned)
        except (ValueError, TypeError):
            self.stdout.write(self.style.ERROR(f'Não foi possível converter o valor flutuante: {s}'))
            return None

    def handle(self, *args, **kwargs):
        # --- 1. Carregar Usuários e Perfis ---
        self.stdout.write(self.style.SUCCESS('Iniciando carga de Usuários e Perfis...'))
        
        # Caminho para o arquivo CSV
        usuarios_csv_path = os.path.join(settings.BASE_DIR, 'data', 'bd_usuarios.csv') # Assumindo que você renomeou o arquivo

        with open(usuarios_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                cpf = row['CPF_Usuario']
                nome_completo = row['Nome_Usuario']
                email = row['E-mail']
                perfil = row['Perfil']
                
                # Divide o nome completo em primeiro e último nome
                partes_nome = nome_completo.split(' ', 1)
                primeiro_nome = partes_nome[0]
                ultimo_nome = partes_nome[1] if len(partes_nome) > 1 else ''

                # Cria o User do Django (para login)
                # Usamos o CPF como username para garantir unicidade e facilitar o login
                user, user_created = User.objects.get_or_create(
                    username=cpf,
                    defaults={
                        'first_name': primeiro_nome,
                        'last_name': ultimo_nome,
                        'email': email,
                    }
                )
                
                # Define uma senha padrão (ex: o próprio CPF) - **AVISO DE SEGURANÇA**
                # Em produção, devemos forçar a troca no primeiro login.
                if user_created:
                    user.set_password(cpf) # A senha será o CPF
                    user.save()

                # Cria o PerfilUsuario (com CPF, perfil, etc.)
                perfil_usuario, perfil_created = PerfilUsuario.objects.get_or_create(
                    user=user,
                    defaults={
                        'cpf': cpf,
                        'telefone': row['Telefone'],
                        'perfil': perfil,
                    }
                )
                
                if perfil_created:
                    self.stdout.write(self.style.SUCCESS(f'Usuário {nome_completo} criado.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Usuário {nome_completo} já existia.'))

        self.stdout.write(self.style.SUCCESS('Carga de Usuários finalizada.'))

        # --- 2. Carregar Centros de Responsabilidade ---
        self.stdout.write(self.style.SUCCESS('Iniciando carga de Centros de Responsabilidade...'))
        
        cr_csv_path = os.path.join(settings.BASE_DIR, 'data', 'bd_cr.csv') # Assumindo que renomeou

        with open(cr_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Pula linhas vazias (ex: Mogi Fácil Biritiba Ussu [cite: 2])
                if not row['Cod_CR']:
                    continue

                # Busca os perfis de Fiscal e Coordenador pelo CPF [cite: 2]
                fiscal = PerfilUsuario.objects.filter(cpf=row['CPF_Fiscal']).first()
                coordenador = PerfilUsuario.objects.filter(cpf=row['CPF_Coordenador']).first()
                
                cr, cr_created = CentroResponsabilidade.objects.get_or_create(
                    cod_cr=int(row['Cod_CR']),
                    defaults={
                        'nome_cr': row['Nome_CR'],
                        'endereco_cr': row['Endereco_CR'],
                        'latitude': self._clean_float(row.get('Latitude')),
                        'longitude': self._clean_float(row.get('Longitude')),
                        'secretaria_responsavel': row['Secretaria_Responsavel'],
                        'postos_trab_previstos': int(row['Postos_trab_previstos']) if row['Postos_trab_previstos'] else 0,
                        'fiscal_padrao': fiscal,
                        'coordenador': coordenador,
                        # Gestor Contrato será preenchido manualmente via Admin por enquanto
                    }
                )
                
                if cr_created:
                    self.stdout.write(self.style.SUCCESS(f'CR {row["Nome_CR"]} criado.'))
                else:
                    self.stdout.write(self.style.WARNING(f'CR {row["Nome_CR"]} já existia.'))

        self.stdout.write(self.style.SUCCESS('Carga de Centros de Responsabilidade finalizada.'))