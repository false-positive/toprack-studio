from .models import Module, ActiveModule

class ModuleService:
    @staticmethod
    def get_all_modules():
        """Get all modules from the database"""
        return Module.objects.all()
    
    @staticmethod
    def get_module(module_id):
        """Get a specific module by ID"""
        try:
            return Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return None

class ActiveModuleService:
    @staticmethod
    def get_all_active_modules():
        """Get all active modules from the database"""
        return ActiveModule.objects.all()
    
    @staticmethod
    def get_active_module(active_module_id):
        """Get a specific active module by ID"""
        try:
            return ActiveModule.objects.get(id=active_module_id)
        except ActiveModule.DoesNotExist:
            return None
    
    @staticmethod
    def create_active_module(data):
        """Create a new active module"""
        module_id = data.pop('module').id if isinstance(data.get('module'), Module) else data.pop('module')
        module = Module.objects.get(id=module_id)
        return ActiveModule.objects.create(module=module, **data)

class ModuleCalculationService:
    @staticmethod
    def calculate_resource_usage(active_modules=None):
        """
        Calculate total resource usage based on active modules
        """
        if active_modules is None:
            active_modules = ActiveModule.objects.all()
            
        return {
            'total_power': sum(am.module.amount for am in active_modules if am.module.unit == 'Usable_Power'),
            # Add other calculations as needed
        }
