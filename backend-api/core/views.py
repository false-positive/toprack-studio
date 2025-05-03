from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Module, ActiveModule, DataCenterSpecs, DataCenterValue, DataCenterPoints
from .serializers import ModuleSerializer, ActiveModuleSerializer, DataCenterPointsSerializer
from .services import ActiveModuleService, ModuleCalculationService, DataCenterValueService, DataCenterSpecsService, ModuleService
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
    return Response({
        'status': 'success',
        'status_code': status.HTTP_200_OK,
        'message': 'Resources calculated successfully',
        'data': results
    })

@api_view(['POST'])
def recalculate_values(request):
    """API endpoint to recalculate all DataCenterValues"""
    # Recalculate values
    DataCenterValueService.recalculate_all_values()
    
    # Validate after recalculation
    validation_result = DataCenterSpecsService.validate_current_values()
    
    # Return a more structured response
    return Response({
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Values recalculated successfully",
        "validation_passed": validation_result
    })

@api_view(['GET'])
def validate_values(request):
    """API endpoint to validate current DataCenterValues against specs"""
    # Get all specs for logging
    all_specs = DataCenterSpecs.objects.all()
    specs_info = []
    
    for spec in all_specs:
        constraint_type = []
        if spec.below_amount == 1:
            constraint_type.append(f"below {spec.amount}")
        if spec.above_amount == 1:
            constraint_type.append(f"above {spec.amount}")
        if spec.minimize == 1:
            constraint_type.append("minimize")
        if spec.maximize == 1:
            constraint_type.append("maximize")
        if spec.unconstrained == 1:
            constraint_type.append("unconstrained")
            
        specs_info.append({
            "name": spec.name,
            "unit": spec.unit,
            "amount": spec.amount,
            "constraints": constraint_type
        })
    
    # Get all current values
    all_values = {value.unit: value.value for value in DataCenterValue.objects.all()}
    
    # Perform validation
    validation_result = DataCenterSpecsService.validate_current_values()
    
    if validation_result:
        return Response({
            "status": "All specifications validated successfully",
            "specs": specs_info,
            "current_values": all_values
        })
    else:
        return Response({
            "status": "Validation failed, see logs for details",
            "specs": specs_info,
            "current_values": all_values
        }, status=status.HTTP_400_BAD_REQUEST)

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
