from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModuleViewSet, ActiveModuleViewSet, DataCenterPointsViewSet, calculate_resources, recalculate_values, initialize_values

router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'active-modules', ActiveModuleViewSet)
router.register(r'datacenter-points', DataCenterPointsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calculate-resources/', calculate_resources, name='calculate-resources'),
    path('recalculate-values/', recalculate_values, name='recalculate-values'),
    path('initialize-values/', initialize_values, name='initialize-values'),
]
