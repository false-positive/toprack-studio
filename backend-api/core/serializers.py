from rest_framework import serializers
from .models import Module, ActiveModule, DataCenterSpecs

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class ActiveModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveModule
        fields = '__all__'

class DataCenterSpecsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterSpecs
        fields = '__all__'