from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .models import Module, ActiveModule, DataCenterValue, Point, DataCenterComponent, DataCenter
from .serializers import (
    ModuleSerializer, ActiveModuleSerializer, 
    DataCenterComponentSerializer, DataCenterSerializer
)
from .services import (
    ActiveModuleService, ModuleCalculationService, 
    DataCenterValueService, DataCenterComponentService, 
    ModuleService
)
import logging
from django.db import models
from backend.settings import DataCenterConstants

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
            
        # Add data center info to the response
        data_center_info = {
            "id": data_center.id,
            "name": data_center.name,
            "width": data_center.space_x,
            "height": data_center.space_y,
            "x": 0,  # Default to origin
            "y": 0   # Default to origin
        }

        # Try to get the first point for coordinates
        first_point = data_center.points.first()
        if first_point:
            data_center_info["x"] = first_point.x
            data_center_info["y"] = first_point.y
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Active modules retrieved successfully",
            "data": serializer.data,
            "data_center": data_center_info
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
            # Extract x and y from request data
            x = request.data.get('x')
            y = request.data.get('y')
            
            if x is None or y is None:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "x and y coordinates are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the active module using the service
            data = request.data.copy()
            active_module = ActiveModuleService.create_active_module(data)
            
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
    
    def update(self, request, *args, **kwargs):
        """Update the position of an active module"""
        try:
            # Get the active module
            instance = self.get_object()
            
            # Extract x and y from request data
            x = request.data.get('x')
            y = request.data.get('y')
            
            if x is None or y is None:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "x and y coordinates are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if other fields are being updated
            for field in request.data:
                if field not in ['x', 'y']:
                    return Response({
                        "status": "error",
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": f"Cannot update field '{field}'. Only position (x, y) can be updated."
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or get a Point object
            point, created = Point.objects.get_or_create(x=x, y=y)
            
            # Update the active module's point
            instance.point = point
            instance.save()
            
            # Get the data center for recalculation
            data_center = None
            if instance.data_center_component and instance.data_center_component.data_center:
                data_center = instance.data_center_component.data_center
            else:
                data_center = DataCenter.get_default()
            
            # Recalculate values after moving a module
            DataCenterValueService.recalculate_all_values(data_center)
            
            # Serialize the result
            serializer = self.get_serializer(instance)
            
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Active module position updated successfully",
                "data": serializer.data
            })
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
        "width": data_center.space_x,
        "height": data_center.space_y,
        "points": []
    }

    # Get all points for the data center
    points = data_center.points.all().order_by('id')
    data_center_info["points"] = [{"x": point.x, "y": point.y} for point in points]
    
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
        "width": data_center.space_x,
        "height": data_center.space_y,
        "points": []
    }

    # Get all points for the data center
    points = data_center.points.all().order_by('id')
    data_center_info["points"] = [{"x": point.x, "y": point.y} for point in points]
    
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
def create_data_center(request):
    """API endpoint to create a new data center and initialize DataCenterValues"""
    # Get the data center name from request or use default
    name = request.data.get('name', 'Default Data Center')
    
    # Create a new data center with the provided name
    from core.models import DataCenter  # Add local import to ensure it's available
    
    try:
        # Create the data center with default dimensions
        data_center = DataCenter.objects.create(
            name=name,
            space_x=DataCenterConstants.SPACE_X_INITIAL,
            space_y=DataCenterConstants.SPACE_Y_INITIAL
        )
        
        # Create default rectangle points
        points = [
            Point.objects.get_or_create(x=0, y=0)[0],                                # Bottom-left
            Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=0)[0],  # Bottom-right
            Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=DataCenterConstants.SPACE_Y_INITIAL)[0],  # Top-right
            Point.objects.get_or_create(x=0, y=DataCenterConstants.SPACE_Y_INITIAL)[0]   # Top-left
        ]
        data_center.points.add(*points)
        
        # Initialize values with the data center
        values = DataCenterValueService.initialize_values_from_components(data_center)
        
        # Serialize the data center to return it in the response
        serializer = DataCenterSerializer(data_center)
        
        # Add data center info to the response
        data_center_info = serializer.data
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": f"Data center '{name}' created successfully with {len(values)} initialized values",
            "data": data_center_info
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

class DataCenterViewSet(viewsets.ModelViewSet):
    """API endpoint for managing data centers"""
    queryset = DataCenter.objects.all()
    serializer_class = DataCenterSerializer
    
    def list(self, request, *args, **kwargs):
        """List all data centers"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Data centers retrieved successfully",
            "data": serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get a specific data center"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Data center retrieved successfully",
            "data": serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def update_points(self, request, pk=None):
        """Update the points of a data center"""
        data_center = self.get_object()
        points_data = request.data.get('points', [])
        
        if not points_data:
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Points data is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Clear existing points
            data_center.points.clear()
            
            # Add new points
            for point_data in points_data:
                x = point_data.get('x')
                y = point_data.get('y')
                
                if x is None or y is None:
                    return Response({
                        "status": "error",
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Each point must have x and y coordinates"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                point, created = Point.objects.get_or_create(x=x, y=y)
                data_center.points.add(point)
            
            # Re-fetch the data center to get updated points
            data_center = DataCenter.objects.get(pk=data_center.pk)
            serializer = self.get_serializer(data_center)
            
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Data center points updated successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

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
        "width": data_center.space_x,
        "height": data_center.space_y,
        "points": []
    }

    # Get all points for the data center
    points = data_center.points.all().order_by('id')
    data_center_info["points"] = [{"x": point.x, "y": point.y} for point in points]
    
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
