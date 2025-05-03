from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ModuleViewSet, ActiveModuleViewSet, calculate_resources, 
    recalculate_values, initialize_values, validate_component_values,
    DataCenterPointsViewSet, DataCenterComponentViewSet,
    initialize_values_from_components
)

router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'active-modules', ActiveModuleViewSet)
router.register(r'datacenter-points', DataCenterPointsViewSet)
router.register(r'datacenter-components', DataCenterComponentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calculate-resources/', calculate_resources, name='calculate-resources'),
    path('recalculate-values/', recalculate_values, name='recalculate-values'),
    path('initialize-values/', initialize_values, name='initialize-values'),
    path('initialize-values-from-components/', initialize_values_from_components, name='initialize-values-from-components'),
    path('validate-component-values/', validate_component_values, name='validate-component-values'),
    path('validate-component-values/<int:component_id>/', validate_component_values, name='validate-component-values-detail'),
]
