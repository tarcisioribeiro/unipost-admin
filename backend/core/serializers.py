from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Text, Statistics


class UserSerializer(serializers.ModelSerializer):
    """Serializer para o modelo User."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class TextSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Text."""
    
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Text
        fields = [
            'id', 'description', 'text_content', 'created_by', 
            'created_at', 'is_approved'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class TextCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de textos."""
    
    class Meta:
        model = Text
        fields = ['description', 'text_content']
    
    def create(self, validated_data):
        """Cria um novo texto associado ao usuário autenticado."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TextApprovalSerializer(serializers.ModelSerializer):
    """Serializer para aprovação/negação de textos."""
    
    class Meta:
        model = Text
        fields = ['is_approved']


class StatisticsSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Statistics."""
    
    class Meta:
        model = Statistics
        fields = [
            'approved_texts', 'denied_texts', 'generated_texts', 'updated_at'
        ]
        read_only_fields = ['updated_at']