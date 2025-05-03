from rest_framework import serializers
from .models import (
    Module, ActiveModule, DataCenterPoints, ModuleAttribute,
    DataCenterComponent, DataCenterComponentAttribute
)

class ModuleAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleAttribute
        fields = ['unit', 'amount', 'is_input', 'is_output']

class ModuleSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'name', 'attributes']
    
    def get_attributes(self, obj):
        """Convert attributes from list of objects to dictionary with unit as key"""
        attributes = ModuleAttribute.objects.filter(module=obj)
        result = {}
        for attr in attributes:
            result[attr.unit] = {
                'amount': attr.amount,
                'is_input': attr.is_input,
                'is_output': attr.is_output
            }
        return result

class ActiveModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveModule
        fields = '__all__'

class DataCenterComponentAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterComponentAttribute
        fields = ['unit', 'amount', 'below_amount', 'above_amount', 'minimize', 'maximize', 'unconstrained']

class DataCenterComponentSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = DataCenterComponent
        fields = ['id', 'name', 'attributes']
    
    def get_attributes(self, obj):
        """Convert attributes from list of objects to dictionary with unit as key"""
        attributes = DataCenterComponentAttribute.objects.filter(component=obj)
        result = {}
        for attr in attributes:
            constraint_type = []
            if attr.below_amount == 1:
                constraint_type.append(f"below {attr.amount}")
            if attr.above_amount == 1:
                constraint_type.append(f"above {attr.amount}")
            if attr.minimize == 1:
                constraint_type.append("minimize")
            if attr.maximize == 1:
                constraint_type.append("maximize")
            if attr.unconstrained == 1:
                constraint_type.append("unconstrained")
                
            result[attr.unit] = {
                'amount': attr.amount,
                'constraints': constraint_type
            }
        return result

class DataCenterPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterPoints
        fields = '__all__'
