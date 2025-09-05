from django.contrib import admin
from django.contrib.auth.models import User, Group, Permission
from .models import Text, Statistics


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    """Configuração do admin para o modelo Text."""
    
    list_display = ('description_short', 'created_by', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at', 'created_by')
    search_fields = ('description', 'text_content')
    readonly_fields = ('created_at',)
    
    def description_short(self, obj):
        """Retorna uma versão encurtada da descrição."""
        return f"{obj.description[:50]}..." if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Descrição'


@admin.register(Statistics)
class StatisticsAdmin(admin.ModelAdmin):
    """Configuração do admin para o modelo Statistics."""
    
    list_display = ('generated_texts', 'approved_texts', 'denied_texts', 'updated_at')
    readonly_fields = ('updated_at',)
    
    def has_add_permission(self, request):
        """Permite apenas uma instância de Statistics."""
        return not Statistics.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Não permite deletar a instância de Statistics."""
        return False


# Configuração de grupos de permissões conforme especificação
def setup_permission_groups():
    """
    Configura os grupos de permissões conforme especificado:
    - Visitors: acesso de visualização a todos os textos
    - Members: todas as permissões exceto exclusão de registros
    """
    
    # Criar grupo Visitors
    visitors_group, created = Group.objects.get_or_create(name='Visitors')
    if created:
        # Permissões de visualização para textos
        text_view_perm = Permission.objects.get(codename='view_text')
        statistics_view_perm = Permission.objects.get(codename='view_statistics')
        
        visitors_group.permissions.add(text_view_perm, statistics_view_perm)
    
    # Criar grupo Members
    members_group, created = Group.objects.get_or_create(name='Members')
    if created:
        # Todas as permissões exceto delete
        text_perms = Permission.objects.filter(
            codename__in=['add_text', 'change_text', 'view_text']
        )
        stats_perms = Permission.objects.filter(
            codename__in=['add_statistics', 'change_statistics', 'view_statistics']
        )
        
        for perm in text_perms:
            members_group.permissions.add(perm)
        for perm in stats_perms:
            members_group.permissions.add(perm)
