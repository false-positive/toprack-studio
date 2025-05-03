from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Module, ActiveModule, DataCenterValue, DataCenterPoints, DataCenterComponent
from .serializers import (
    ModuleSerializer, ActiveModuleSerializer, DataCenterPointsSerializer,
    DataCenterComponentSerializer
)
from .services import (
    ActiveModuleService, ModuleCalculationService, 
    DataCenterValueService, DataCenterComponentService, 
    ModuleService
)
import logging

logger = logging.getLogger('django')

def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Now add the HTTP status code to the response
    if response is not None:
        response.data = {
            'status': 'error',
            'status_code': response.status_code,
            'message': str(exc),
            'data': response.data
        }
    
    return response

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    
    def get_queryset(self):
        return ModuleService.get_all_modules()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'status_code': status.HTTP_200_OK,
            'message': 'Modules retrieved successfully',
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'status_code': status.HTTP_200_OK,
            'message': 'Module retrieved successfully',
            'data': serializer.data
        })

class ActiveModuleViewSet(viewsets.ModelViewSet):
    queryset = ActiveModule.objects.all()
    serializer_class = ActiveModuleSerializer
    
    def get_queryset(self):
        return ActiveModuleService.get_all_active_modules()
    
    def list(self, request, *args, **kwargs):
        """
        List all active modules without validation.
        """
        # Get all active modules
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            "active_modules": serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            data = serializer.validated_data
            logger.info(f"Creating active module with data: {data}")
            active_module = ActiveModuleService.create_active_module(data)
            
            serializer = self.get_serializer(active_module)
            return Response({
                "active_module": serializer.data
            }, status=status.HTTP_201_CREATED)
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
            return Response({
                "status": "success",
                "message": "Active module deleted successfully"
            }, status=status.HTTP_200_OK)
        
        return Response({"error": "Failed to delete active module"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def calculate_resources(request):
    """API endpoint to calculate resource usage and validate"""
    # First recalculate all values
    DataCenterValueService.recalculate_all_values()
    
    # Then get active modules and calculate resources
    active_modules = ActiveModuleService.get_all_active_modules()
    results = ModuleCalculationService.calculate_resource_usage(active_modules)
    
    # Check validation status
    validation_result, violations = DataCenterComponentService.validate_component_values()
    
    return Response({
        'status': 'success',
        'status_code': status.HTTP_200_OK,
        'message': 'Resources calculated successfully',
        'data': results,
        'validation_passed': validation_result,
        'violations': violations if not validation_result else []
    })

@api_view(['POST'])
def recalculate_values(request):
    """API endpoint to recalculate all DataCenterValues and validate"""
    # Recalculate values
    DataCenterValueService.recalculate_all_values()
    
    # Validate after recalculation
    validation_result, violations = DataCenterComponentService.validate_component_values()
    
    # Return a more structured response
    return Response({
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Values recalculated successfully",
        "validation_passed": validation_result,
        "violations": violations if not validation_result else []
    })

@api_view(['POST'])
def initialize_values(request):
    """API endpoint to initialize DataCenterValues from components"""
    values = DataCenterValueService.initialize_values_from_components()
    return Response({
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Values initialized successfully",
        "count": len(values)
    })

@api_view(['POST'])
def initialize_values_from_components(request):
    """API endpoint to initialize DataCenterValues from DataCenterComponentAttributes"""
    values = DataCenterValueService.initialize_values_from_components()
    return Response({
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Values initialized successfully from components",
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

class DataCenterComponentViewSet(viewsets.ModelViewSet):
    queryset = DataCenterComponent.objects.all()
    serializer_class = DataCenterComponentSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'status_code': status.HTTP_200_OK,
            'message': 'Components retrieved successfully',
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'status_code': status.HTTP_200_OK,
            'message': 'Component retrieved successfully',
            'data': serializer.data
        })

@api_view(['GET'])
def validate_component_values(request, component_id=None):
    """
    API endpoint to validate data center values against component specifications.
    
    If component_id is provided, only that component's values will be validated.
    Otherwise, all components will be validated.
    
    Returns:
        Response: Validation status, component specifications, and current values.
    """
    # Get the component if ID is provided
    component = None
    if component_id:
        try:
            component = DataCenterComponent.objects.get(id=component_id)
        except DataCenterComponent.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": f"Component with ID {component_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Validate component values
    validation_result, violations = DataCenterComponentService.validate_component_values(component)
    
    # Get component data for response
    if component:
        components = [component]
    else:
        components = DataCenterComponent.objects.all()
    
    component_serializer = DataCenterComponentSerializer(components, many=True)
    
    # Get current values for response
    current_values = {}
    for comp in components:
        values = DataCenterValue.objects.filter(component=comp)
        current_values[comp.name] = {value.unit: value.value for value in values}
    
    # Return response
    if validation_result:
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "All specifications validated successfully",
            "components": component_serializer.data,
            "current_values": current_values
        })
    else:
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Some specifications are not met",
            "components": component_serializer.data,
            "current_values": current_values,
            "violations": violations
        }, status=status.HTTP_400_BAD_REQUEST)
