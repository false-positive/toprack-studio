from django.db import models

class Module(models.Model):
    name = models.CharField(max_length=255)
    is_input = models.BooleanField()
    is_output = models.BooleanField()

class ModuleAttribute(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='attributes')
    unit = models.CharField(max_length=255)
    amount = models.IntegerField()

class ActiveModule(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="instances")

    def __str__(self):
        return f"{self.module.name} at ({self.x}, {self.y})"


class DataCenterSpecs(models.Model):
    name = models.CharField(max_length=255)
    below_amount = models.IntegerField()
    above_amount = models.IntegerField()
    minimize = models.IntegerField()
    maximize = models.IntegerField()
    unconstrained = models.IntegerField()
    unit = models.CharField(max_length=255)
    amount = models.IntegerField()

    def __str__(self):
        return f"Spec {self.name}"


class DataCenterValue(models.Model):
    unit = models.CharField(max_length=255)
    value = models.IntegerField()

    spec = models.ForeignKey(DataCenterSpecs, on_delete=models.CASCADE, related_name="values", null=True, blank=True)

    def __str__(self):
        return f"{self.unit}: {self.value}"


class DataCenterPoints(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()

    def __str__(self):
        return f"Point at ({self.x}, {self.y})"
