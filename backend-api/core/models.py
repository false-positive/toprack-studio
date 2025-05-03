from django.db import models
from backend.settings import DataCenterConstants


class Point(models.Model):
    """
    Model representing a point in 2D space.
    Can be associated with various objects in the data center.
    """
    x = models.IntegerField()
    y = models.IntegerField()
    
    def __str__(self):
        return f"Point at ({self.x}, {self.y})"

class DataCenter(models.Model):
    """
    Model representing a data center with its name and space dimensions.
    Points define the polygon shape of the data center.
    """
    name = models.CharField(max_length=255)
    space_x = models.IntegerField(default=1000)  # Width
    space_y = models.IntegerField(default=500)   # Height
    points = models.ManyToManyField(Point, related_name='data_centers', blank=True)
    
    def __str__(self):
        return f"DataCenter: {self.name} ({self.space_x}x{self.space_y})"
    
    @classmethod
    def get_default(cls):
        """Get or create the default data center"""
        data_center, created = cls.objects.get_or_create(
            name="Default Data Center",
            defaults={
                'space_x': DataCenterConstants.SPACE_X_INITIAL,
                'space_y': DataCenterConstants.SPACE_Y_INITIAL
            }
        )
        
        # Ensure the default data center has at least the origin point
        if created:
            # Create a rectangle by default
            points = [
                Point.objects.get_or_create(x=0, y=0)[0],                                # Bottom-left
                Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=0)[0],  # Bottom-right
                Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=DataCenterConstants.SPACE_Y_INITIAL)[0],  # Top-right
                Point.objects.get_or_create(x=0, y=DataCenterConstants.SPACE_Y_INITIAL)[0]   # Top-left
            ]
            data_center.points.add(*points)
            
        return data_center
    
    def save(self, *args, **kwargs):
        """Override save to ensure at least one point exists"""
        super().save(*args, **kwargs)
        
        # Ensure at least the origin point exists
        if not self.points.exists():
            # Create a rectangle by default
            points = [
                Point.objects.get_or_create(x=0, y=0)[0],                # Bottom-left
                Point.objects.get_or_create(x=self.space_x, y=0)[0],     # Bottom-right
                Point.objects.get_or_create(x=self.space_x, y=self.space_y)[0],  # Top-right
                Point.objects.get_or_create(x=0, y=self.space_y)[0]      # Top-left
            ]
            self.points.add(*points)
            
class Module(models.Model):
    name = models.CharField(max_length=255)
    data_center = models.ForeignKey(DataCenter, on_delete=models.CASCADE, related_name='modules', null=True, blank=True)
    
    def __str__(self):
        return f"Module: {self.name}"

class ModuleAttribute(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='attributes')
    is_input = models.BooleanField(default=False)
    is_output = models.BooleanField(default=False)
    unit = models.CharField(max_length=255)
    amount = models.IntegerField()
    
    def __str__(self):
        return f"{self.module.name} - {self.unit}: {self.amount}"
    
class DataCenterComponent(models.Model):
    name = models.CharField(max_length=255)
    data_center = models.ForeignKey(DataCenter, on_delete=models.CASCADE, 
                                   related_name="components", null=True, blank=True)
    
    def __str__(self):
        return f"Component: {self.name}"

class DataCenterComponentAttribute(models.Model):
    component = models.ForeignKey(DataCenterComponent, on_delete=models.CASCADE, related_name='attributes')
    below_amount = models.IntegerField()
    above_amount = models.IntegerField()
    minimize = models.IntegerField()
    maximize = models.IntegerField()
    unconstrained = models.IntegerField()
    unit = models.CharField(max_length=255)
    amount = models.IntegerField()
    
    def __str__(self):
        return f"{self.component.name} - {self.unit}: {self.amount}"
    
class DataCenterValue(models.Model):
    unit = models.CharField(max_length=255)
    value = models.IntegerField()
    component = models.ForeignKey(DataCenterComponent, on_delete=models.CASCADE, 
                                 related_name="values", null=True, blank=True)
    data_center = models.ForeignKey(DataCenter, on_delete=models.CASCADE, 
                                   related_name="values", null=True, blank=True)

    def __str__(self):
        component_name = self.component.name if self.component else "Global"
        data_center_name = self.data_center.name if self.data_center else "No Data Center"
        return f"{data_center_name} - {component_name} - {self.unit}: {self.value}"

class ActiveModule(models.Model):
    """
    Model representing a module placed at a specific point in the data center.
    Once created, only the point (location) can be changed.
    """
    point = models.ForeignKey(Point, on_delete=models.CASCADE, related_name="active_modules")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="instances")
    data_center_component = models.ForeignKey(DataCenterComponent, on_delete=models.CASCADE, 
                                             related_name="active_modules", null=True, blank=True)
    data_center = models.ForeignKey(DataCenter, on_delete=models.CASCADE,
                                   related_name="active_modules", null=True, blank=True)

    def __str__(self):
        component_name = self.data_center_component.name if self.data_center_component else "No component"
        return f"{self.module.name} at ({self.point.x}, {self.point.y}) in {component_name}"
    
    @property
    def x(self):
        """Get the x-coordinate from the associated point"""
        return self.point.x if self.point else None
        
    @property
    def y(self):
        """Get the y-coordinate from the associated point"""
        return self.point.y if self.point else None
        
    def save(self, *args, **kwargs):
        """Override save to ensure point is always set"""
        if not self.point:
            raise ValueError("ActiveModule must have a point")
        super().save(*args, **kwargs)
