from rest_framework import serializers
from .models import (
    Module, ActiveModule, ModuleAttribute,
    DataCenterComponent, DataCenterComponentAttribute, DataCenter, Point
)

class ModuleAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleAttribute
        fields = ['unit', 'amount', 'is_input', 'is_output']

class ModuleSerializer(serializers.ModelSerializer):
    """
    Serializer for Module model.
    Includes all attributes of the module.
    """
    attributes = serializers.SerializerMethodField()
    data_center_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'name', 'attributes', 'data_center', 'data_center_name']
    
    def get_attributes(self, obj):
        """Get all attributes for this module"""
        attributes = obj.attributes.all()
        return ModuleAttributeSerializer(attributes, many=True).data
    
    def get_data_center_name(self, obj):
        """Get the name of the data center"""
        if obj.data_center:
            return obj.data_center.name
        return None

class DataCenterSerializer(serializers.ModelSerializer):
    """
    Serializer for DataCenter model.
    Includes points that define the polygon shape of the data center.
    """
    points = serializers.SerializerMethodField()
    width = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()
    
    class Meta:
        model = DataCenter
        fields = ['id', 'name', 'width', 'height', 'points']
    
    def get_points(self, obj):
        """Get all points associated with this data center"""
        points = obj.points.all().order_by('id')
        return PointSerializer(points, many=True).data
    
    def get_width(self, obj):
        """Get the width (space_x) of the data center"""
        return obj.space_x
    
    def get_height(self, obj):
        """Get the height (space_y) of the data center"""
        return obj.space_y
    
    def create(self, validated_data):
        """Create a new data center with default rectangular shape"""
        data_center = DataCenter.objects.create(**validated_data)
        
        return data_center

class PointSerializer(serializers.ModelSerializer):
    """Internal serializer for Point model - not exposed via API"""
    class Meta:
        model = Point
        fields = ['id', 'x', 'y']

class ActiveModuleSerializer(serializers.ModelSerializer):
    """
    Serializer for ActiveModule model.
    
    When creating: Requires module, data_center_component, x, and y.
    When updating: Only allows changing x and y (the point).
    """
    module_details = serializers.SerializerMethodField()
    component_name = serializers.SerializerMethodField()
    x = serializers.IntegerField(write_only=True, required=True)
    y = serializers.IntegerField(write_only=True, required=True)
    width = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()
    
    class Meta:
        model = ActiveModule
        fields = ['id', 'x', 'y', 'width', 'height', 'module', 'data_center_component', 
                 'module_details', 'component_name', 'data_center']
        read_only_fields = ['id', 'module_details', 'component_name', 'width', 'height']
        extra_kwargs = {
            'module': {'required': True, 'write_only': False},
            'data_center_component': {'required': False, 'write_only': False},
            'data_center': {'required': False, 'write_only': True}
        }
    
    def get_module_details(self, obj):
        """Get detailed information about the module"""
        if obj.module:
            return ModuleSerializer(obj.module).data
        return None
    
    def get_component_name(self, obj):
        """Get the name of the data center component"""
        if obj.data_center_component:
            return obj.data_center_component.name
        return "No component"
    
    def get_width(self, obj):
        """Get the width (Space_X) of the module"""
        if obj.module:
            attr = ModuleAttribute.objects.filter(module=obj.module, unit='Space_X').first()
            if attr:
                return attr.amount
        return 0
    
    def get_height(self, obj):
        """Get the height (Space_Y) of the module"""
        if obj.module:
            attr = ModuleAttribute.objects.filter(module=obj.module, unit='Space_Y').first()
            if attr:
                return attr.amount
        return 0
    
    def to_representation(self, instance):
        """Add x and y coordinates to the output representation"""
        representation = super().to_representation(instance)
        if instance.point:
            representation['x'] = instance.point.x
            representation['y'] = instance.point.y
        return representation
    
    def validate(self, data):
        """
        Validate the data based on whether this is a create or update operation.
        For create: Ensure module and coordinates are provided.
        For update: Only allow changing coordinates.
        """
        if self.instance:  # This is an update
            # Only allow x and y to be changed
            if 'module' in self.initial_data:
                raise serializers.ValidationError("Cannot change module after creation")
            if 'data_center_component' in self.initial_data:
                raise serializers.ValidationError("Cannot change data_center_component after creation")
            if 'data_center' in self.initial_data:
                raise serializers.ValidationError("Cannot change data_center after creation")
            
            # Ensure x and y are provided
            if 'x' not in data or 'y' not in data:
                raise serializers.ValidationError("Must provide both x and y coordinates")
        else:  # This is a create
            # Ensure module is provided
            if 'module' not in data:
                raise serializers.ValidationError("Module is required")
            
            # Ensure x and y are provided
            if 'x' not in data or 'y' not in data:
                raise serializers.ValidationError("Must provide both x and y coordinates")
        
        return data
    
    def create(self, validated_data):
        """Create a new active module with a point"""
        x = validated_data.pop('x')
        y = validated_data.pop('y')
        
        point, created = Point.objects.get_or_create(x=x, y=y)
        
        active_module = ActiveModule.objects.create(
            point=point,
            **validated_data
        )
        
        return active_module
    
    def update(self, instance, validated_data):
        """Update only the point of an active module"""
        x = validated_data.pop('x')
        y = validated_data.pop('y')
        
        point, created = Point.objects.get_or_create(x=x, y=y)
        
        instance.point = point
        instance.save()
        
        return instance

class DataCenterComponentAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCenterComponentAttribute
        fields = ['unit', 'amount', 'below_amount', 'above_amount', 'minimize', 'maximize', 'unconstrained']

class DataCenterComponentSerializer(serializers.ModelSerializer):
    """
    Serializer for DataCenterComponent model.
    Includes all attributes of the component.
    """
    attributes = serializers.SerializerMethodField()
    data_center_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DataCenterComponent
        fields = ['id', 'name', 'attributes', 'data_center', 'data_center_name']
    
    def get_attributes(self, obj):
        """Get all attributes for this component"""
        attributes = obj.attributes.all()
        return DataCenterComponentAttributeSerializer(attributes, many=True).data
    
    def get_data_center_name(self, obj):
        """Get the name of the data center"""
        if obj.data_center:
            return obj.data_center.name
        return None

class DataCenterPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Point
        fields = '__all__'
