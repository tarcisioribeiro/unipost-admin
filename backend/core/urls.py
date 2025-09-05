from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, TextViewSet, StatisticsView, WebhookView,
    TextGenerationView, VectorizeApprovedTextView
)

# Configurar router para ViewSets
router = DefaultRouter()
router.register(r'texts', TextViewSet)

urlpatterns = [
    # Autenticação JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoints da API
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    path('webhook/', WebhookView.as_view(), name='webhook'),
    path('generate/', TextGenerationView.as_view(), name='text_generation'),
    path('vectorize/<int:text_id>/', VectorizeApprovedTextView.as_view(), name='vectorize_text'),
    
    # Incluir URLs dos ViewSets
    path('', include(router.urls)),
]