from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Text, Statistics


class Command(BaseCommand):
    """
    Management command para configurar grupos de permissões.
    Implementa os grupos Visitors e Members conforme especificação.
    """
    
    help = 'Configura grupos de permissões Visitors e Members'
    
    def handle(self, *args, **options):
        """Executa a configuração dos grupos de permissões."""
        
        self.stdout.write(
            self.style.SUCCESS('Iniciando configuração de grupos de permissões...')
        )
        
        # Configurar grupo Visitors
        self._setup_visitors_group()
        
        # Configurar grupo Members  
        self._setup_members_group()
        
        self.stdout.write(
            self.style.SUCCESS('Grupos de permissões configurados com sucesso!')
        )
    
    def _setup_visitors_group(self):
        """
        Configura o grupo Visitors com permissões de visualização.
        """
        visitors_group, created = Group.objects.get_or_create(name='Visitors')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Grupo "Visitors" criado com sucesso')
            )
        else:
            self.stdout.write('Grupo "Visitors" já existe, atualizando permissões...')
        
        # Limpar permissões existentes
        visitors_group.permissions.clear()
        
        # Adicionar permissões de visualização
        view_permissions = [
            'core.view_text',
            'core.view_statistics'
        ]
        
        for perm_codename in view_permissions:
            app_label, codename = perm_codename.split('.')
            try:
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                visitors_group.permissions.add(permission)
                self.stdout.write(f'  + Adicionada permissão: {perm_codename}')
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  - Permissão não encontrada: {perm_codename}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Grupo "Visitors" configurado com {visitors_group.permissions.count()} permissões')
        )
    
    def _setup_members_group(self):
        """
        Configura o grupo Members com todas permissões exceto delete.
        """
        members_group, created = Group.objects.get_or_create(name='Members')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Grupo "Members" criado com sucesso')
            )
        else:
            self.stdout.write('Grupo "Members" já existe, atualizando permissões...')
        
        # Limpar permissões existentes
        members_group.permissions.clear()
        
        # Adicionar todas permissões exceto delete
        member_permissions = [
            'core.add_text',
            'core.change_text', 
            'core.view_text',
            'core.add_statistics',
            'core.change_statistics',
            'core.view_statistics'
        ]
        
        for perm_codename in member_permissions:
            app_label, codename = perm_codename.split('.')
            try:
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                members_group.permissions.add(permission)
                self.stdout.write(f'  + Adicionada permissão: {perm_codename}')
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  - Permissão não encontrada: {perm_codename}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Grupo "Members" configurado com {members_group.permissions.count()} permissões')
        )
    
    def _list_available_permissions(self):
        """Lista todas as permissões disponíveis para debug."""
        self.stdout.write('\n=== PERMISSÕES DISPONÍVEIS ===')
        
        for model in [Text, Statistics]:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)
            
            self.stdout.write(f'\n{model.__name__}:')
            for perm in permissions:
                self.stdout.write(f'  - {content_type.app_label}.{perm.codename}: {perm.name}')