from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Text, Statistics
from .serializers import (
    TextSerializer, TextCreateSerializer, TextApprovalSerializer,
    StatisticsSerializer, UserSerializer
)
from .services import TextGenerationService, TextVectorizationService


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista customizada para obtenção de tokens JWT."""
    
    def post(self, request, *args, **kwargs):
        """Retorna tokens JWT e informações do usuário."""
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Adicionar informações do usuário à resposta
            user = User.objects.get(username=request.data.get('username'))
            user_data = UserSerializer(user).data
            response.data['user'] = user_data
            
        return response


class TextViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de textos."""
    
    queryset = Text.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        if self.action == 'create':
            return TextCreateSerializer
        elif self.action == 'approve':
            return TextApprovalSerializer
        return TextSerializer
    
    def get_queryset(self):
        """Filtra textos baseado nos parâmetros da query."""
        queryset = Text.objects.all()
        
        # Filtro por status de aprovação
        is_approved = self.request.query_params.get('is_approved')
        if is_approved is not None:
            if is_approved.lower() == 'true':
                queryset = queryset.filter(is_approved=True)
            elif is_approved.lower() == 'false':
                queryset = queryset.filter(is_approved=False)
        
        # Filtro por usuário (meus textos)
        my_texts = self.request.query_params.get('my_texts')
        if my_texts and my_texts.lower() == 'true':
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Cria um novo texto e atualiza estatísticas."""
        text = serializer.save(created_by=self.request.user)
        
        # Atualizar estatísticas
        stats = Statistics.get_instance()
        stats.increment_generated()
    
    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """Aprova ou nega um texto (webhook endpoint)."""
        text = get_object_or_404(Text, pk=pk)
        
        # Verificar se o usuário tem permissão
        if not request.user.has_perm('core.change_text'):
            return Response(
                {'error': 'Sem permissão para alterar textos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TextApprovalSerializer(text, data=request.data, partial=True)
        if serializer.is_valid():
            old_status = text.is_approved
            serializer.save()
            
            # Atualizar estatísticas se o status mudou
            if old_status != text.is_approved:
                stats = Statistics.get_instance()
                if text.is_approved:
                    stats.increment_approved()
                else:
                    stats.increment_denied()
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StatisticsView(APIView):
    """View para obter estatísticas da aplicação."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retorna as estatísticas atuais."""
        stats = Statistics.get_instance()
        serializer = StatisticsSerializer(stats)
        return Response(serializer.data)


class WebhookView(APIView):
    """
    Endpoint de webhook para atualização de status de aprovação.
    Conforme especificado na proposta, deve receber id do texto e status.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Processa webhook de aprovação/negação de texto.
        
        Expected payload:
        {
            "text_id": int,
            "is_approved": bool
        }
        """
        text_id = request.data.get('text_id')
        is_approved = request.data.get('is_approved')
        
        if text_id is None or is_approved is None:
            return Response(
                {'error': 'text_id e is_approved são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            text = Text.objects.get(id=text_id)
            old_status = text.is_approved
            text.is_approved = bool(is_approved)
            text.save()
            
            # Atualizar estatísticas se o status mudou
            if old_status != text.is_approved:
                stats = Statistics.get_instance()
                if text.is_approved:
                    stats.increment_approved()
                else:
                    stats.increment_denied()
            
            return Response({
                'message': 'Status atualizado com sucesso',
                'text_id': text.id,
                'is_approved': text.is_approved
            })
        
        except Text.DoesNotExist:
            return Response(
                {'error': 'Texto não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TextGenerationView(APIView):
    """
    View para geração de texto com contexto do Elasticsearch.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Gera texto usando contexto relevante do Elasticsearch.
        
        Expected payload:
        {
            "theme": str,
            "model": str (opcional, default: "gpt-4o-mini")
        }
        """
        theme = request.data.get('theme')
        model = request.data.get('model', 'gpt-4o-mini')
        
        if not theme:
            return Response(
                {'error': 'Theme é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Usar o serviço de geração de texto
            text_gen_service = TextGenerationService()
            result = text_gen_service.generate_text_with_context(theme, model)
            
            if result['success']:
                # Criar registro na base de dados
                text_instance = Text.objects.create(
                    description=theme,
                    text_content=result['generated_text'],
                    created_by=request.user
                )
                
                # Retornar resultado com dados do texto criado
                text_data = TextSerializer(text_instance).data
                result['text_data'] = text_data
                
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VectorizeApprovedTextView(APIView):
    """
    View para vetorizar texto aprovado e armazenar no banco de vetores.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, text_id):
        """
        Vetoriza um texto aprovado.
        
        Args:
            text_id (int): ID do texto aprovado
        """
        try:
            text = get_object_or_404(Text, id=text_id, is_approved=True)
            
            # Usar o serviço de vetorização
            vector_service = TextVectorizationService()
            vector = vector_service.vectorize_text(text.text_content)
            
            if len(vector) > 0:
                # TODO: Armazenar vetor no banco de dados vetorizado
                # Por agora, apenas simular o armazenamento
                
                return Response({
                    'message': 'Texto vetorizado com sucesso',
                    'text_id': text.id,
                    'vector_dimensions': len(vector)
                })
            else:
                return Response(
                    {'error': 'Falha na vetorização do texto'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Text.DoesNotExist:
            return Response(
                {'error': 'Texto não encontrado ou não aprovado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
