from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Module, ActiveModule, DataCenterPoints
from .serializers import ModuleSerializer, ActiveModuleSerializer, DataCenterPointsSerializer
from .services import ModuleService, ActiveModuleService, ModuleCalculationService, DataCenterValueService, DataCenterSpecsService
import logging

logger = logging.getLogger(__name__)

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
        
        try:
            data = serializer.validated_data
            logger.info(f"Creating active module with data: {data}")
            active_module = ActiveModuleService.create_active_module(data)
            
            serializer = self.get_serializer(active_module)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            logger.error(f"Failed to create active module: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error creating active module: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        success = ActiveModuleService.delete_active_module(instance.id)
        
        if success:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Failed to delete active module"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def calculate_resources(request):
    """API endpoint to calculate resource usage"""
    active_modules = ActiveModuleService.get_all_active_modules()
    results = ModuleCalculationService.calculate_resource_usage(active_modules)
    return Response(results)

@api_view(['POST'])
def recalculate_values(request):
    """API endpoint to recalculate all DataCenterValues"""
    DataCenterValueService.recalculate_all_values()
    
    # Optionally validate after recalculation
    validation_result = DataCenterSpecsService.validate_current_values()
    
    return Response({
        "status": "Values recalculated successfully",
        "validation_passed": validation_result
    })

@api_view(['GET'])
def validate_values(request):
    """API endpoint to validate current DataCenterValues against specs"""
    validation_result = DataCenterSpecsService.validate_current_values()
    
    if validation_result:
        return Response({"status": "All specifications validated successfully"})
    else:
        return Response(
            {"status": "Validation failed, see logs for details"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def initialize_values(request):
    """API endpoint to initialize DataCenterValues from DataCenterSpecs"""
    values = DataCenterValueService.initialize_values_from_specs()
    return Response({
        "status": "Values initialized successfully",
        "count": len(values)
    })

class DataCenterPointsViewSet(viewsets.ModelViewSet):
    queryset = DataCenterPoints.objects.all()
    serializer_class = DataCenterPointsSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            data = serializer.validated_data
            logger.info(f"Creating data center point with data: {data}")
            point = self.perform_create(serializer)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Unexpected error creating data center point: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def perform_create(self, serializer):
        return serializer.save()
