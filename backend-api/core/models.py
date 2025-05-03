from django.db import models

class Module(models.Model):
    name = models.CharField(max_length=255)
    
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

class ActiveModule(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="instances")
    data_center_component = models.ForeignKey(DataCenterComponent, on_delete=models.CASCADE, 
                                             related_name="active_modules", null=True, blank=True)

    def __str__(self):
        component_name = self.data_center_component.name if self.data_center_component else "No component"
        return f"{self.module.name} at ({self.x}, {self.y}) in {component_name}"


class DataCenterValue(models.Model):
    unit = models.CharField(max_length=255)
    value = models.IntegerField()
    component = models.ForeignKey(DataCenterComponent, on_delete=models.CASCADE, 
                                 related_name="values", null=True, blank=True)

    def __str__(self):
        component_name = self.component.name if self.component else "Global"
        return f"{component_name} - {self.unit}: {self.value}"


class DataCenterPoints(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()

    def __str__(self):
        return f"Point at ({self.x}, {self.y})"
