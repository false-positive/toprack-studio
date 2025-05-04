import random
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .models import Module, ActiveModule, DataCenterValue, Point, DataCenterComponent, DataCenter, ModuleAttribute
from .serializers import (
    ModuleSerializer, ActiveModuleSerializer, 
    DataCenterComponentSerializer, DataCenterSerializer
)
from .services import (
    ActiveModuleService, 
    DataCenterValueService, DataCenterComponentService, 
    ModuleService
)
import logging
from django.db import models
from io import StringIO
import sys
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger('django')

warmth_image = {
    'content': None,
    'content_type': None
}

display_control = {
    'current_display': 'website'
}

active_data_center = {
    'id': None  # Will store the ID of the currently active data center
}

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
        queryset = ModuleService.get_all_modules()
        
        # Filter by data_center if provided
        data_center_id = self.request.query_params.get('data_center', None)
        if data_center_id:
            try:
                data_center = DataCenter.objects.get(id=data_center_id)
                queryset = queryset.filter(data_center=data_center)
            except DataCenter.DoesNotExist:
                pass
        
        return queryset
    
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
            if active_module.data_center:
                data_center = active_module.data_center
            elif active_module.data_center_component and active_module.data_center_component.data_center:
                data_center = active_module.data_center_component.data_center
            else:
                data_center = DataCenter.get_default()
            
            logger.info(f"Recalculating values after creating active module {active_module.id}")
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
            logger.error(f"Error creating active module: {str(e)}", exc_info=True)
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
    data_center_id = request.query_params.get('data_center', None)
    
    if not data_center_id:
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "data_center parameter is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        data_center = DataCenter.objects.get(id=data_center_id)
    except DataCenter.DoesNotExist:
        return Response({
            "status": "error",
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": f"Data center with ID {data_center_id} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    calculated_values = DataCenterValueService.force_recalculate_values(data_center)
    
    results = calculated_values['global_values']
    

    space_x_used = results.get('Space_X', 0)
    space_y_used = results.get('Space_Y', 0)
    
    results['Space_X_Available'] = data_center.space_x - space_x_used
    results['Space_Y_Available'] = data_center.space_y - space_y_used
    
    validation_result, violations = DataCenterComponentService.validate_component_values(None, data_center)
    
    data_center_info = {
        "id": data_center.id,
        "name": data_center.name,
        "width": data_center.space_x,
        "height": data_center.space_y,
        "points": []
    }

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
    data_center_id = request.data.get('data_center', None)
    
    if not data_center_id:
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "data_center parameter is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        data_center = DataCenter.objects.get(id=data_center_id)
    except DataCenter.DoesNotExist:
        return Response({
            "status": "error",
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": f"Data center with ID {data_center_id} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    calculated_values = DataCenterValueService.force_recalculate_values(data_center)
    
    validation_result, violations = DataCenterComponentService.validate_component_values(None, data_center)
    
    data_center_info = {
        "id": data_center.id,
        "name": data_center.name,
        "width": data_center.space_x,
        "height": data_center.space_y,
        "points": []
    }

    points = data_center.points.all().order_by('id')
    data_center_info["points"] = [{"x": point.x, "y": point.y} for point in points]
    
    return Response({
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Values recalculated successfully",
        "data": calculated_values['global_values'],
        "data_center": data_center_info,
        "validation_passed": validation_result,
        "violations": violations if not validation_result else []
    })

@api_view(['POST'])
def create_data_center(request):
    """API endpoint to create a new data center and initialize DataCenterValues with uploaded CSV files"""
    try:
        name = request.data.get('name', 'Default Data Center')
        clean_db = request.data.get('clean_db', 'false').lower() == 'true'
        
        if DataCenter.objects.filter(name=name).exists():
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": f"A data center with the name '{name}' already exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from backend.settings import DataCenterConstants
        
        data_center, created = DataCenter.objects.get_or_create(
            name=name,
            defaults={
                'space_x': DataCenterConstants.SPACE_X_INITIAL,
                'space_y': DataCenterConstants.SPACE_Y_INITIAL
            }
        )
        
        if created:
            from core.models import Point
            points = [
                Point.objects.get_or_create(x=0, y=0)[0],
                Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=0)[0],
                Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=DataCenterConstants.SPACE_Y_INITIAL)[0],
                Point.objects.get_or_create(x=0, y=DataCenterConstants.SPACE_Y_INITIAL)[0]
            ]
            data_center.points.add(*points)
            print(f"Created new data center: {name}")
        
        modules_file = request.FILES.get('modules_csv')
        components_file = request.FILES.get('components_csv')
        
        if not modules_file or not components_file:
            logger.info("No CSV files uploaded, using default files from the project")
            
            import os
            from django.conf import settings
            
            base_dir = settings.BASE_DIR
            
            default_modules_path = os.path.join(base_dir, 'Modules.csv')
            default_components_path = os.path.join(base_dir, 'Data_Center_Spec.csv')
            
            logger.info(f"Using default modules file: {default_modules_path}")
            logger.info(f"Using default components file: {default_components_path}")
            
            if not os.path.exists(default_modules_path):
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": f"Default modules file not found at {default_modules_path}"
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if not os.path.exists(default_components_path):
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": f"Default components file not found at {default_components_path}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        stdout = StringIO()
        stderr = StringIO()
        sys.stdout = stdout
        sys.stderr = stderr
        
        from core.models import DataCenterComponent, DataCenterComponentAttribute, ActiveModule
        from core.services import DataCenterValueService
        import csv
        
        if clean_db:
            print("Cleaning database before import...")
            ActiveModule.objects.all().delete()
            DataCenterComponentAttribute.objects.all().delete()
            DataCenterComponent.objects.all().delete()
            DataCenterValue.objects.all().delete()
            print("Database cleaned successfully (components only)")
        
        print("Processing modules file...")
        
        if modules_file:
            content = modules_file.read().decode('utf-8')
            
            delimiters = [',', ';', '\t', '|']
            counts = {d: content.count(d) for d in delimiters}
            delimiter = max(counts.items(), key=lambda x: x[1])[0]
            print(f"Detected delimiter: '{delimiter}'")
            
            reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
            
            modules = {}
            for row in reader:
                module_name = row['Name']
                
                if module_name not in modules:
                    module = Module.objects.create(
                        name=module_name,
                        data_center=data_center
                    )
                    modules[module_name] = module
                    print(f"Created module: {module_name} for data center: {data_center.name}")
                
                ModuleAttribute.objects.create(
                    module=modules[module_name],
                    unit=row['Unit'],
                    amount=int(row['Amount']),
                    is_input=int(row['Is_Input']) == 1,
                    is_output=int(row['Is_Output']) == 1
                )
            
            print(f"Imported {len(modules)} modules")
        else:
            with open(default_modules_path, 'r') as f:
                first_line = f.readline()
                delimiters = [',', ';', '\t', '|']
                counts = {d: first_line.count(d) for d in delimiters}
                delimiter = max(counts.items(), key=lambda x: x[1])[0]
                print(f"Detected delimiter: '{delimiter}'")
                
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                modules = {}
                for row in reader:
                    module_name = row['Name']
                    
                    if module_name not in modules:
                        module = Module.objects.create(
                            name=module_name,
                            data_center=data_center
                        )
                        modules[module_name] = module
                        print(f"Created module: {module_name} for data center: {data_center.name}")
                    
                    ModuleAttribute.objects.create(
                        module=modules[module_name],
                        unit=row['Unit'],
                        amount=int(row['Amount']),
                        is_input=int(row['Is_Input']) == 1,
                        is_output=int(row['Is_Output']) == 1
                    )
                
                print(f"Imported {len(modules)} modules from default file")
        
        print("Processing components file...")
        
        if components_file:
            content = components_file.read().decode('utf-8')
            
            delimiters = [',', ';', '\t', '|']
            counts = {d: content.count(d) for d in delimiters}
            delimiter = max(counts.items(), key=lambda x: x[1])[0]
            print(f"Detected delimiter: '{delimiter}'")
            
            reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
            
            components = {}
            for row in reader:
                component_name = row['Name']
                
                if component_name not in components:
                    component = DataCenterComponent.objects.create(
                        name=component_name,
                        data_center=data_center
                    )
                    components[component_name] = component
                    print(f"Created component: {component_name} for data center: {data_center.name}")
                
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
        else:
            with open(default_components_path, 'r') as f:
                first_line = f.readline()
                delimiters = [',', ';', '\t', '|']
                counts = {d: first_line.count(d) for d in delimiters}
                delimiter = max(counts.items(), key=lambda x: x[1])[0]
                print(f"Detected delimiter: '{delimiter}'")
                
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                components = {}
                for row in reader:
                    component_name = row['Name']
                    
                    if component_name not in components:
                        component = DataCenterComponent.objects.create(
                            name=component_name,
                            data_center=data_center
                        )
                        components[component_name] = component
                        print(f"Created component: {component_name} for data center: {data_center.name}")
                    
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
                
                print(f"Imported {len(components)} components from default file")
        
        values = DataCenterValueService.initialize_values_from_components(data_center)

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        serializer = DataCenterSerializer(data_center)
        
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
            data_center.points.clear()
            
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
    
    def get_queryset(self):
        queryset = DataCenterComponent.objects.all()
        
        data_center_id = self.request.query_params.get('data_center', None)
        if data_center_id:
            try:
                data_center = DataCenter.objects.get(id=data_center_id)
                queryset = queryset.filter(data_center=data_center)
            except DataCenter.DoesNotExist:
                pass
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'status_code': status.HTTP_200_OK,
            'message': 'Data center components retrieved successfully',
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
    logger.info(f"validate_component_values called with component_id={component_id}")
    data_center_id = request.query_params.get('data_center') or request.data.get('data_center')
    
    logger.info(f"Validating for data_center_id={data_center_id}")
    
    if not data_center_id:
        logger.warning("No data_center parameter provided")
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "data_center parameter is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        data_center = DataCenter.objects.get(id=data_center_id)
        logger.info(f"Found data center: {data_center.name} (ID: {data_center.id})")
    except DataCenter.DoesNotExist:
        logger.error(f"Data center with ID {data_center_id} not found")
        return Response({
            "status": "error",
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": f"Data center with ID {data_center_id} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    component = None
    if component_id:
        try:
            component = DataCenterComponent.objects.get(id=component_id)
            logger.info(f"Found component: {component.name} (ID: {component.id})")
        except DataCenterComponent.DoesNotExist:
            logger.error(f"Component with ID {component_id} not found")
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": f"Component with ID {component_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
    logger.info(f"Calling DataCenterComponentService.validate_component_values with component={component}, data_center={data_center}")
    try:
        validation_result, violations = DataCenterComponentService.validate_component_values(component, data_center)
        logger.info(f"Validation result: {validation_result}, Violations count: {len(violations)}")
        if violations:
            logger.info(f"Violations: {violations}")
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}", exc_info=True)
        return Response({
            "status": "error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"Error during validation: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if component:
        components = [component]
        logger.info(f"Using single component: {component.name}")
    else:
        logger.info("Getting component IDs from DataCenterValues")
        try:
            # Use filter() instead of values_list() followed by get() to avoid MultipleObjectsReturned
            component_ids = DataCenterValue.objects.filter(
                data_center=data_center
            ).exclude(
                component=None
            ).values_list('component_id', flat=True).distinct()
            
            logger.info(f"Found {len(component_ids)} distinct component IDs: {list(component_ids)}")
            
            components = DataCenterComponent.objects.filter(id__in=component_ids)
            logger.info(f"Found {components.count()} components")
            
            if not components.exists():
                logger.info(f"No components found for data center {data_center.id}, using all components for this data center")
                components = DataCenterComponent.objects.filter(data_center=data_center)
                logger.info(f"Found {components.count()} components for data center {data_center.id}")
        except Exception as e:
            logger.error(f"Error getting components: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error getting components: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    logger.info(f"Serializing {len(components)} components")
    component_serializer = DataCenterComponentSerializer(components, many=True)
    
    logger.info("Processing violations")
    violation_set = set()
    for v in violations:
        parts = v.split(':')
        if len(parts) >= 2:
            component_name = parts[0].replace('Component ', '')
            unit_parts = parts[1].split(' value')
            if len(unit_parts) >= 1:
                unit = unit_parts[0].strip()
                violation_set.add((component_name, unit))
    
    logger.info(f"Found {len(violation_set)} unique violations: {violation_set}")
    
    logger.info("Getting current values")
    current_values = {}
    try:
        values_count = DataCenterValue.objects.filter(data_center=data_center).count()
        logger.info(f"Found {values_count} DataCenterValue objects for data center {data_center.id}")
        
        for value in DataCenterValue.objects.filter(data_center=data_center):
            component_name = value.component.name if value.component else "Global"
            if component_name not in current_values:
                current_values[component_name] = {}
            
            is_violating = False
            for violation_comp, violation_unit in violation_set:
                if component_name in violation_comp and value.unit == violation_unit:
                    is_violating = True
                    logger.info(f"Violation found: Component={component_name}, Unit={value.unit}, Value={value.value}")
                    break
            
            current_values[component_name][value.unit] = {
                "value": value.value,
                "violates_constraint": is_violating
            }
    except Exception as e:
        logger.error(f"Error getting current values: {str(e)}", exc_info=True)
        return Response({
            "status": "error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"Error getting current values: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    logger.info("Getting data center points")
    data_center_info = {
        "id": data_center.id,
        "name": data_center.name,
        "width": data_center.space_x,
        "height": data_center.space_y,
        "points": []
    }

    try:
        points = data_center.points.all().order_by('id')
        data_center_info["points"] = [{"x": point.x, "y": point.y} for point in points]
        logger.info(f"Found {len(data_center_info['points'])} points for data center {data_center.id}")
    except Exception as e:
        logger.error(f"Error getting data center points: {str(e)}", exc_info=True)
    
    logger.info(f"Preparing response with validation_result={validation_result}")
    if validation_result:
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "All specifications validated successfully",
            "components": component_serializer.data,
            "current_values": current_values,
            "data_center": data_center_info,
            "validation_passed": True,
            "violations": []
        })
    else:
        return Response({
            "status": "error",
            "status_code": status.HTTP_200_OK,
            "message": "Some specifications are not met",
            "components": component_serializer.data,
            "current_values": current_values,
            "violations": violations,
            "data_center": data_center_info,
            "validation_passed": False
        })

@api_view(['POST'])
def upload_warmth_image(request):
    """API endpoint to upload and store a single warmth image in memory"""
    if 'image' not in request.FILES:
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "No image file provided"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    image_file = request.FILES['image']
    
    warmth_image['content'] = image_file.read()
    warmth_image['content_type'] = image_file.content_type
    
    return Response({
        "status": "success",
        "status_code": status.HTTP_201_CREATED,
        "message": "Warmth image uploaded successfully"
    })

@api_view(['GET'])
def get_warmth_image(request):
    """API endpoint to retrieve the warmth image stored in memory"""
    if warmth_image['content'] is None:
        return Response({
            "status": "error",
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": "No warmth image has been uploaded"
        }, status=status.HTTP_404_NOT_FOUND)
    
    return HttpResponse(
        warmth_image['content'],
        content_type=warmth_image['content_type']
    )

@api_view(['POST'])
def initialize_values_from_components(request):
    """API endpoint to initialize DataCenterValues from existing components"""
    try:
        data_center_name = request.data.get('name')
        if not data_center_name:
            random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(3)])
            data_center_name = f"DataCenter{random_suffix}"
        
        if DataCenter.objects.filter(name=data_center_name).exists():
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": f"A data center with the name '{data_center_name}' already exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from backend.settings import DataCenterConstants
        
        data_center, created = DataCenter.objects.get_or_create(
            name=data_center_name,
            defaults={
                'space_x': DataCenterConstants.SPACE_X_INITIAL,
                'space_y': DataCenterConstants.SPACE_Y_INITIAL
            }
        )
        
        if created:
            points = [
                Point.objects.get_or_create(x=0, y=0)[0],
                Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=0)[0],
                Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=DataCenterConstants.SPACE_Y_INITIAL)[0],
                Point.objects.get_or_create(x=0, y=DataCenterConstants.SPACE_Y_INITIAL)[0]
            ]
            data_center.points.add(*points)
        
        from core.services import DataCenterValueService
        values = DataCenterValueService.initialize_values_from_components(data_center)
        
        serializer = DataCenterSerializer(data_center)
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": f"DataCenterValues initialized successfully for '{data_center_name}'",
            "data": serializer.data,
            "values_count": len(values)
        })
    except Exception as e:
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def debug_active_modules(request):
    """Debug endpoint to list all active modules with their details"""
    active_modules = ActiveModule.objects.all().select_related(
        'module', 'data_center_component', 'data_center', 'point'
    )
    
    data = []
    for am in active_modules:
        attributes = []
        if am.module:
            for attr in ModuleAttribute.objects.filter(module=am.module):
                attributes.append({
                    'unit': attr.unit,
                    'amount': attr.amount,
                    'is_input': attr.is_input,
                    'is_output': attr.is_output
                })
        
        data.append({
            'id': am.id,
            'module': {
                'id': am.module.id if am.module else None,
                'name': am.module.name if am.module else None,
                'attributes': attributes
            },
            'component': {
                'id': am.data_center_component.id if am.data_center_component else None,
                'name': am.data_center_component.name if am.data_center_component else None
            },
            'data_center': {
                'id': am.data_center.id if am.data_center else None,
                'name': am.data_center.name if am.data_center else None
            },
            'position': {
                'x': am.point.x if am.point else None,
                'y': am.point.y if am.point else None
            }
        })
    
    return Response({
        'status': 'success',
        'status_code': status.HTTP_200_OK,
        'message': 'Active modules retrieved successfully',
        'count': len(data),
        'data': data
    })

@api_view(['GET'])
def toggle_display_control(request):
    """API endpoint to toggle who should be showing info (VR or website)"""
    # Toggle the current display
    if display_control['current_display'] == 'website':
        display_control['current_display'] = 'vr'
    else:
        display_control['current_display'] = 'website'
    
    return Response({
        'status': 'success',
        'status_code': status.HTTP_200_OK,
        'message': f"Display control switched to {display_control['current_display']}",
        'data': {
            'current_display': display_control['current_display']
        }
    })

@api_view(['GET'])
def get_display_control(request):
    """API endpoint to check who's currently showing info (VR or website)"""
    return Response({
        'status': 'success',
        'status_code': status.HTTP_200_OK,
        'message': f"Current display is {display_control['current_display']}",
        'data': {
            'current_display': display_control['current_display']
        }
    })

@api_view(['GET', 'POST'])
def get_set_active_data_center(request):
    """API endpoint to get or set the currently active data center"""
    if request.method == 'POST':
        data_center_id = request.data.get('data_center_id')
        if not data_center_id:
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "data_center_id parameter is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify the data center exists
            data_center = DataCenter.objects.get(id=data_center_id)
            active_data_center['id'] = data_center_id
            
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": f"Active data center set to {data_center.name} (ID: {data_center_id})",
                "data": {
                    "id": data_center_id,
                    "name": data_center.name
                }
            })
        except DataCenter.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": f"Data center with ID {data_center_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)
    else:  # GET request
        data_center_id = active_data_center['id']
        
        # If no active data center is set, use the default
        if not data_center_id:
            try:
                default_data_center = DataCenter.get_default()
                active_data_center['id'] = default_data_center.id
                data_center_id = default_data_center.id
                data_center_name = default_data_center.name
            except Exception as e:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": "No active data center set and no default data center found"
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                data_center = DataCenter.objects.get(id=data_center_id)
                data_center_name = data_center.name
            except DataCenter.DoesNotExist:
                return Response({
                    "status": "error",
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": f"Previously active data center with ID {data_center_id} no longer exists"
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Active data center retrieved successfully",
            "data": {
                "id": data_center_id,
                "name": data_center_name
            }
        })
