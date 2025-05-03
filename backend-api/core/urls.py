from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ModuleViewSet, ActiveModuleViewSet, calculate_resources, 
    recalculate_values, validate_component_values,
    DataCenterComponentViewSet,
    DataCenterViewSet, create_data_center,
    upload_warmth_image, get_warmth_image,
    initialize_values_from_components
)

router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'active-modules', ActiveModuleViewSet)
router.register(r'datacenter-components', DataCenterComponentViewSet)
router.register(r'datacenters', DataCenterViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calculate-resources/', calculate_resources, name='calculate-resources'), 
    path('recalculate-values/', recalculate_values, name='recalculate-values'),
    path('create-data-center/', create_data_center, name='create-data-center'),
    path('initialize-values-from-components/', initialize_values_from_components, name='initialize-values-from-components'),
    path('validate-component-values/', validate_component_values, name='validate-component-values'),
    path('validate-component-values/<int:component_id>/', validate_component_values, name='validate-component-values-detail'),
    path('warmth-image/upload/', upload_warmth_image, name='upload-warmth-image'),
    path('warmth-image/', get_warmth_image, name='get-warmth-image'),
]
