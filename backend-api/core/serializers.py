from rest_framework import serializers
from .models import Module, ActiveModule, DataCenterSpecs, DataCenterPoints, ModuleAttribute

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

class DataCenterSpecsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterSpecs
        fields = '__all__'

class DataCenterPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterPoints
        fields = '__all__'
