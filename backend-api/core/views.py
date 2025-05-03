from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Module, ActiveModule
from .serializers import ModuleSerializer, ActiveModuleSerializer
from .services import ModuleService, ActiveModuleService, ModuleCalculationService

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    
    def get_queryset(self):
        return ModuleService.get_all_modules()

class ActiveModuleViewSet(viewsets.ModelViewSet):
    queryset = ActiveModule.objects.all()
    serializer_class = ActiveModuleSerializer
    
    def get_queryset(self):
        return ActiveModuleService.get_all_active_modules()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        active_module = ActiveModuleService.create_active_module(data)
        
        serializer = self.get_serializer(active_module)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def calculate_resources(request):
    """API endpoint to calculate resource usage"""
    active_modules = ActiveModuleService.get_all_active_modules()
    results = ModuleCalculationService.calculate_resource_usage(active_modules)
    return Response(results)
