from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModuleViewSet, ActiveModuleViewSet, calculate_resources

router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'active-modules', ActiveModuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calculate-resources/', calculate_resources, name='calculate-resources'),
]
