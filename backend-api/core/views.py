from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Module, ActiveModule, DataCenterValue, DataCenterPoints, DataCenterComponent, DataCenter
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
    """API endpoint for managing active modules"""
    queryset = ActiveModule.objects.all()
    serializer_class = ActiveModuleSerializer

    def list(self, request, *args, **kwargs):
        """List all active modules with detailed information"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get data center parameter if provided
        data_center_id = request.query_params.get('data_center', None)
        if data_center_id:
            try:
                data_center = DataCenter.objects.get(id=data_center_id)
                queryset = queryset.filter(
                    models.Q(data_center=data_center) | 
                    models.Q(data_center_component__data_center=data_center)
                )
            except DataCenter.DoesNotExist:
                pass
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Get the data center for additional info
        data_center = None
        if data_center_id:
            try:
                data_center = DataCenter.objects.get(id=data_center_id)
            except DataCenter.DoesNotExist:
                data_center = DataCenter.get_default()
        else:
            data_center = DataCenter.get_default()
            
        # Get resource calculations for this data center
        active_modules = ActiveModuleService.get_all_active_modules(data_center)
        resources = ModuleCalculationService.calculate_resource_usage(active_modules, data_center)
        
        # Add data center info to the response
        data_center_info = {
            "id": data_center.id,
            "name": data_center.name,
            "space_x": data_center.space_x,
            "space_y": data_center.space_y,
            "space_x_used": resources.get('Space_X', 0),
            "space_y_used": resources.get('Space_Y', 0),
            "space_x_available": resources.get('Space_X_Available', data_center.space_x),
            "space_y_available": resources.get('Space_Y_Available', data_center.space_y)
        }
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Active modules retrieved successfully",
            "data": serializer.data,
            "data_center": data_center_info,
            "resources": resources
        })

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific active module with detailed information"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Active module retrieved successfully",
            "data": serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create a new active module"""
        try:
            # Create the active module using the service
            active_module = ActiveModuleService.create_active_module(request.data.copy())
            
            # Get the data center for recalculation
            data_center = None
            if active_module.data_center_component and active_module.data_center_component.data_center:
                data_center = active_module.data_center_component.data_center
            else:
                data_center = DataCenter.get_default()
            
            # Recalculate values after adding a module
            DataCenterValueService.recalculate_all_values(data_center)
            
            # Serialize the result
            serializer = self.get_serializer(active_module)
            headers = self.get_success_headers(serializer.data)
            
            return Response({
                "status": "success",
                "status_code": status.HTTP_201_CREATED,
                "message": "Active module created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
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
    # Get the data center (use default if not specified)
    from core.models import DataCenter  # Add local import to ensure it's available
    
    data_center = DataCenter.get_default()
    
    # First recalculate all values
    DataCenterValueService.recalculate_all_values(data_center)
    
    # Then get active modules and calculate resources
    active_modules = ActiveModuleService.get_all_active_modules(data_center)
    results = ModuleCalculationService.calculate_resource_usage(active_modules, data_center)
    
    # Check validation status
    validation_result, violations = DataCenterComponentService.validate_component_values(None, data_center)
    
    # Add data center info to the response
    data_center_info = {
        "id": data_center.id,
        "name": data_center.name,
        "space_x": data_center.space_x,
        "space_y": data_center.space_y,
        "space_x_used": results.get('Space_X', 0),
        "space_y_used": results.get('Space_Y', 0),
        "space_x_available": results.get('Space_X_Available', data_center.space_x),
        "space_y_available": results.get('Space_Y_Available', data_center.space_y)
    }
    
    return Response({
        'status': 'success',
        'status_code': status.HTTP_200_OK,
        'message': 'Resources calculated successfully',
        'data': results,
        'data_center': data_center_info,
        'validation_passed': validation_result,
        'violations': violations if not validation_result else []
    })

@api_view(['POST'])
def recalculate_values(request):
    """API endpoint to recalculate all DataCenterValues and validate"""
    # Get the data center (use default if not specified)
    from core.models import DataCenter  # Add local import to ensure it's available
    
    data_center = DataCenter.get_default()
    
    # Recalculate values
    DataCenterValueService.recalculate_all_values(data_center)
    
    # Validate after recalculation
    validation_result, violations = DataCenterComponentService.validate_component_values(None, data_center)
    
    # Add data center info to the response
    data_center_info = {
        "id": data_center.id,
        "name": data_center.name,
        "space_x": data_center.space_x,
        "space_y": data_center.space_y
    }
    
    # Return a more structured response
    return Response({
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Values recalculated successfully",
        "data_center": data_center_info,
        "validation_passed": validation_result,
        "violations": violations if not validation_result else []
    })

@api_view(['POST'])
def initialize_values(request):
    """API endpoint to initialize DataCenterValues from components"""
    # Get the data center (use default if not specified)
    from core.models import DataCenter  # Add local import to ensure it's available
    
    data_center = DataCenter.get_default()
    
    values = DataCenterValueService.initialize_values_from_components(data_center)
    
    # Add data center info to the response
    data_center_info = {
        "id": data_center.id,
        "name": data_center.name,
        "space_x": data_center.space_x,
        "space_y": data_center.space_y
    }
    
    return Response({
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Values initialized successfully",
        "count": len(values),
        "data_center": data_center_info
    })

@api_view(['POST'])
def initialize_values_from_components(request):
    """API endpoint to initialize DataCenterValues from DataCenterComponentAttributes"""
    # Get or create the default data center
    from core.models import DataCenter  # Add local import to ensure it's available
    
    data_center = DataCenter.get_default()
    
    # Initialize values with the data center
    values = DataCenterValueService.initialize_values_from_components(data_center)
    
    # Serialize the values to return them in the response
    value_data = {}
    for value in values:
        component_name = value.component.name if value.component else "Global"
        if component_name not in value_data:
            value_data[component_name] = {}
        value_data[component_name][value.unit] = value.value
    
    # Add data center info to the response
    data_center_info = {
        "id": data_center.id,
        "name": data_center.name,
        "space_x": data_center.space_x,
        "space_y": data_center.space_y
    }
    
    return Response({
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Values initialized successfully from components",
        "count": len(values),
        "data": value_data,
        "data_center": data_center_info
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

@api_view(['GET', 'POST'])
def validate_component_values(request, component_id=None):
    """API endpoint to validate DataCenterValues against component specifications"""
    # Get the data center (use default if not specified)
    from core.models import DataCenter  # Add local import to ensure it's available
    
    data_center = DataCenter.get_default()
    
    # Get the component if specified
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
    validation_result, violations = DataCenterComponentService.validate_component_values(component, data_center)
    
    # Get all components for the response
    if component:
        components = [component]
    else:
        components = DataCenterComponent.objects.filter(data_center=data_center)
    
    # Serialize components
    component_serializer = DataCenterComponentSerializer(components, many=True)
    
    # Get current values for the response
    current_values = {}
    for value in DataCenterValue.objects.filter(data_center=data_center):
        component_name = value.component.name if value.component else "Global"
        if component_name not in current_values:
            current_values[component_name] = {}
        current_values[component_name][value.unit] = value.value
    
    # Add data center info to the response
    data_center_info = {
        "id": data_center.id,
        "name": data_center.name,
        "space_x": data_center.space_x,
        "space_y": data_center.space_y
    }
    
    # Return response
    if validation_result:
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "All specifications validated successfully",
            "components": component_serializer.data,
            "current_values": current_values,
            "data_center": data_center_info
        })
    else:
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Some specifications are not met",
            "components": component_serializer.data,
            "current_values": current_values,
            "violations": violations,
            "data_center": data_center_info
        }, status=status.HTTP_400_BAD_REQUEST)
