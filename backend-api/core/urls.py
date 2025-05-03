from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ModuleViewSet, ActiveModuleViewSet, calculate_resources, 
    recalculate_values, initialize_values, validate_values
)

router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'active-modules', ActiveModuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calculate-resources/', calculate_resources, name='calculate-resources'),
    path('recalculate-values/', recalculate_values, name='recalculate-values'),
    path('initialize-values/', initialize_values, name='initialize-values'),
    path('validate-values/', validate_values, name='validate-values'),
]
