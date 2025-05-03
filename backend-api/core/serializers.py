from rest_framework import serializers
from .models import Module, ActiveModule, DataCenterSpecs, DataCenterPoints, ModuleAttribute

class ModuleAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleAttribute
        fields = ['unit', 'amount']

class ModuleSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'name', 'is_input', 'is_output', 'attributes']
    
    def get_attributes(self, obj):
        """Convert attributes from list of objects to dictionary with unit as key"""
        attributes = ModuleAttribute.objects.filter(module=obj)
        return {attr.unit: attr.amount for attr in attributes}

class ActiveModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveModule
        fields = '__all__'

class DataCenterSpecsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterSpecs
        fields = '__all__'

class DataCenterPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterPoints
        fields = '__all__'
