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
from io import StringIO
import sys

logger = logging.getLogger('django')

def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler
    
    response = exception_handler(exc, context)
    
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
        
        data_center = None
        if data_center_id:
            try:
                data_center = DataCenter.objects.get(id=data_center_id)
            except DataCenter.DoesNotExist:
                data_center = DataCenter.get_default()
        else:
            data_center = DataCenter.get_default()
            
        data_center_info = {
            "id": data_center.id,
            "name": data_center.name,
            "width": data_center.space_x,
            "height": data_center.space_y,
            "x": 0,
            "y": 0
        }

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
            x = request.data.get('x')
            y = request.data.get('y')
            
            if x is None or y is None:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "x and y coordinates are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = request.data.copy()
            active_module = ActiveModuleService.create_active_module(data)
            
            data_center = None
            if active_module.data_center_component and active_module.data_center_component.data_center:
                data_center = active_module.data_center_component.data_center
            else:
                data_center = DataCenter.get_default()
            
            DataCenterValueService.recalculate_all_values(data_center)
            
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
            instance = self.get_object()
            
            x = request.data.get('x')
            y = request.data.get('y')
            
            if x is None or y is None:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "x and y coordinates are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            for field in request.data:
                if field not in ['x', 'y']:
                    return Response({
                        "status": "error",
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": f"Cannot update field '{field}'. Only position (x, y) can be updated."
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            point, created = Point.objects.get_or_create(x=x, y=y)
            
            instance.point = point
            instance.save()
            
            data_center = None
            if instance.data_center_component and instance.data_center_component.data_center:
                data_center = instance.data_center_component.data_center
            else:
                data_center = DataCenter.get_default()
            
            DataCenterValueService.recalculate_all_values(data_center)
            
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
    data_center = DataCenter.get_default()
    
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
    """API endpoint to create a new data center and initialize DataCenterValues with uploaded CSV files"""
    try:
        # Get parameters from request
        name = request.data.get('name', 'Default Data Center')
        clean_db = request.data.get('clean_db', 'false').lower() == 'true'
        
        # Get uploaded files
        modules_file = request.FILES.get('modules_csv')
        components_file = request.FILES.get('components_csv')
        
        # Capture command output
        stdout = StringIO()
        stderr = StringIO()
        sys.stdout = stdout
        sys.stderr = stderr
        
        # Import directly from memory - remove DataCenter from this import
        from core.models import Module, ModuleAttribute, DataCenterComponent, DataCenterComponentAttribute
        from core.services import DataCenterValueService
        import csv
        
        # Clean database if requested
        if clean_db:
            print("Cleaning database before import...")
            ModuleAttribute.objects.all().delete()
            Module.objects.all().delete()
            DataCenterComponentAttribute.objects.all().delete()
            DataCenterComponent.objects.all().delete()
            DataCenterValue.objects.all().delete()
        
        # Process modules file if provided
        if modules_file:
            print(f"Processing uploaded modules file")
            
            # Read file content and detect delimiter
            content = modules_file.read().decode('utf-8')
            
            # Detect delimiter by counting occurrences
            delimiters = [',', ';', '\t', '|']
            counts = {d: content.count(d) for d in delimiters}
            delimiter = max(counts.items(), key=lambda x: x[1])[0]
            print(f"Detected delimiter: '{delimiter}'")
            
            # Parse CSV with detected delimiter
            reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
            
            # Create modules and attributes
            modules = {}
            for row in reader:
                module_name = row['Name']
                
                # Create module if it doesn't exist
                if module_name not in modules:
                    module, created = Module.objects.get_or_create(name=module_name)
                    modules[module_name] = module
                    
                    if created:
                        print(f"Created module: {module_name}")
                
                # Create module attribute
                ModuleAttribute.objects.create(
                    module=modules[module_name],
                    unit=row['Unit'],
                    amount=int(row['Amount']),
                    is_input=int(row['Is_Input']) == 1,
                    is_output=int(row['Is_Output']) == 1
                )
            
            print(f"Imported {len(modules)} modules")
        
        # Process components file if provided
        if components_file:
            print(f"Processing uploaded components file")
            
            # Read file content and detect delimiter
            content = components_file.read().decode('utf-8')
            
            # Detect delimiter by counting occurrences
            delimiters = [',', ';', '\t', '|']
            counts = {d: content.count(d) for d in delimiters}
            delimiter = max(counts.items(), key=lambda x: x[1])[0]
            print(f"Detected delimiter: '{delimiter}'")
            
            # Parse CSV with detected delimiter
            reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
            
            # Create components and attributes
            components = {}
            for row in reader:
                component_name = row['Name']
                
                # Create component if it doesn't exist
                if component_name not in components:
                    component, created = DataCenterComponent.objects.get_or_create(name=component_name)
                    components[component_name] = component
                    
                    if created:
                        print(f"Created component: {component_name}")
                
                # Create component attribute
                DataCenterComponentAttribute.objects.create(
                    component=components[component_name],
                    unit=row['Unit'],
                    amount=int(row['Amount']),
                    below_amount=int(row['Below_Amount']),
                    above_amount=int(row['Above_Amount']),
                    minimize=int(row['Minimize']),
                    maximize=int(row['Maximize']),
                    unconstrained=int(row['Unconstrained'])
                )
            
            print(f"Imported {len(components)} components")
        
        # Initialize values
        print("Initializing DataCenterValues...")
        from backend.settings import DataCenterConstants
        
        # Get or create the data center with the specified name
        data_center, created = DataCenter.objects.get_or_create(
            name=name,
            defaults={
                'space_x': DataCenterConstants.SPACE_X_INITIAL,
                'space_y': DataCenterConstants.SPACE_Y_INITIAL
            }
        )
        
        if created:
            from core.models import Point
            # Create default rectangle points
            points = [
                Point.objects.get_or_create(x=0, y=0)[0],
                Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=0)[0],
                Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=DataCenterConstants.SPACE_Y_INITIAL)[0],
                Point.objects.get_or_create(x=0, y=DataCenterConstants.SPACE_Y_INITIAL)[0]
            ]
            data_center.points.add(*points)
            print(f"Created new data center: {name}")
        
        # Initialize values with the data center
        values = DataCenterValueService.initialize_values_from_components(data_center)
        print(f"Initialized {len(values)} DataCenterValues for {data_center.name}")
        
        # Reset stdout/stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        # Serialize the data center to return it in the response
        serializer = DataCenterSerializer(data_center)
        
        # Add data center info to the response
        data_center_info = serializer.data
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": f"Data center '{name}' created successfully with imported data",
            "command_output": stdout.getvalue(),
            "data": data_center_info
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        
        # Reset stdout/stderr
        if 'stdout' in locals() and 'stderr' in locals():
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": str(e),
            "error_details": stderr.getvalue() if 'stderr' in locals() else "",
            "traceback": traceback_str
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
