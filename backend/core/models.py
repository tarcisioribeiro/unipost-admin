from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Text(models.Model):
    """
    Modelo para registro e atualização de textos gerados.
    
    Attributes:
        description (str): Texto de entrada fornecido pelo usuário via Streamlit
        text_content (str): Campo de texto longo para armazenar o conteúdo gerado
        created_by (User): Chave estrangeira para o User que criou o texto
        created_at (datetime): Campo de data e hora preenchido automaticamente ao criar o texto
        is_approved (bool): Campo booleano para indicar o status de aprovação
    """
    
    description = models.TextField(
        verbose_name="Descrição",
        help_text="Texto de entrada fornecido pelo usuário"
    )
    
    text_content = models.TextField(
        verbose_name="Conteúdo do Texto",
        help_text="Conteúdo gerado pelo modelo de linguagem"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Criado por",
        related_name="texts"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Criado em"
    )
    
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Aprovado",
        help_text="Status de aprovação do texto"
    )
    
    class Meta:
        verbose_name = "Texto"
        verbose_name_plural = "Textos"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.description[:50]}..." if len(self.description) > 50 else self.description


class Statistics(models.Model):
    """
    Modelo para rastrear e registrar métricas da aplicação.
    
    Attributes:
        approved_texts (int): Total de textos aprovados
        denied_texts (int): Total de textos negados
        generated_texts (int): Total de textos gerados
    """
    
    approved_texts = models.IntegerField(
        default=0,
        verbose_name="Textos Aprovados",
        help_text="Total de textos aprovados"
    )
    
    denied_texts = models.IntegerField(
        default=0,
        verbose_name="Textos Negados",
        help_text="Total de textos negados"
    )
    
    generated_texts = models.IntegerField(
        default=0,
        verbose_name="Textos Gerados",
        help_text="Total de textos gerados"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    class Meta:
        verbose_name = "Estatística"
        verbose_name_plural = "Estatísticas"
    
    def __str__(self):
        return f"Stats: {self.generated_texts}G / {self.approved_texts}A / {self.denied_texts}D"
    
    @classmethod
    def get_instance(cls):
        """Retorna a instância única das estatísticas, criando se não existir."""
        instance, created = cls.objects.get_or_create(id=1)
        return instance
    
    def increment_generated(self):
        """Incrementa o contador de textos gerados."""
        self.generated_texts += 1
        self.save()
    
    def increment_approved(self):
        """Incrementa o contador de textos aprovados."""
        self.approved_texts += 1
        self.save()
    
    def increment_denied(self):
        """Incrementa o contador de textos negados."""
        self.denied_texts += 1
        self.save()
