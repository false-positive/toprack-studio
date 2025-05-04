from django.db import transaction
from .models import (
    DataCenter, Module, ActiveModule, DataCenterValue, ModuleAttribute,
    DataCenterComponent, Point
)
import logging

logger = logging.getLogger('django')

class ModuleService:
    """
    Service for managing Module objects.
    """
    
    @staticmethod
    def get_all_modules(data_center=None):
        """
        Get all modules, optionally filtered by data center.
        
        Args:
            data_center (DataCenter, optional): The data center to filter by.
                If None, returns all modules.
                
        Returns:
            QuerySet: QuerySet of Module objects.
        """
        if data_center:
            return Module.objects.filter(data_center=data_center)
        return Module.objects.all()
    
    @staticmethod
    def get_module_by_id(module_id):
        """
        Get a module by its ID.
        
        Args:
            module_id (int): The ID of the module to retrieve.
            
        Returns:
            Module: The Module object with the given ID.
            
        Raises:
            Module.DoesNotExist: If the module does not exist.
        """
        return Module.objects.get(id=module_id)
    
    @staticmethod
    def get_module_attributes(module):
        """
        Get all attributes for a module.
        
        Args:
            module (Module): The module to get attributes for.
                
        Returns:
            QuerySet: QuerySet of ModuleAttribute objects.
        """
        return module.attributes.all()
    
    @staticmethod
    def create_module(name, data_center=None):
        """
        Create a new module.
        
        Args:
            name (str): The name of the module.
            data_center (DataCenter, optional): The data center to associate with the module.
                
        Returns:
            Module: The newly created Module object.
        """
        return Module.objects.create(name=name, data_center=data_center)
    
    @staticmethod
    def create_module_attribute(module, unit, amount, is_input=False, is_output=False):
        """
        Create a new module attribute.
        
        Args:
            module (Module): The module to associate with the attribute.
            unit (str): The unit of the attribute.
            amount (int): The amount of the attribute.
            is_input (bool, optional): Whether the attribute is an input.
            is_output (bool, optional): Whether the attribute is an output.
                
        Returns:
            ModuleAttribute: The newly created ModuleAttribute object.
        """
        return ModuleAttribute.objects.create(
            module=module,
            unit=unit,
            amount=amount,
            is_input=is_input,
            is_output=is_output
        )

class ActiveModuleService:
    """
    Service class for active module operations.
    Provides methods to create, retrieve, and manage active modules.
    """
    
    @staticmethod
    def get_all_active_modules(data_center=None):
        """
        Get all active modules from the database, optionally filtered by data center.
        
        Args:
            data_center (DataCenter, optional): The data center to filter by.
                If None, returns all active modules.
        
        Returns:
            QuerySet: ActiveModule objects, optionally filtered by data center.
        """
        if data_center:
            return ActiveModule.objects.filter(data_center_component__data_center=data_center)
        return ActiveModule.objects.all()
    
    @staticmethod
    def get_active_module(active_module_id):
        """
        Get a specific active module by ID.
        
        Args:
            active_module_id (int): The ID of the active module to retrieve.
            
        Returns:
            ActiveModule: The ActiveModule object if found, None otherwise.
            
        Usage:
            active_module = ActiveModuleService.get_active_module(1)
            if active_module:
                # Active module found
            else:
                # Active module not found
        """
        try:
            return ActiveModule.objects.get(id=active_module_id)
        except ActiveModule.DoesNotExist:
            return None
    
    @staticmethod
    def create_active_module(data):
        """
        Create a new active module without validation.
        Places a module at specific coordinates in the data center.
        
        Args:
            data (dict): Dictionary containing module ID/object, component ID/object, and coordinates.
                Required keys:
                - module: Module object or ID
                - x: X-coordinate (int)
                - y: Y-coordinate (int)
                - data_center_component: DataCenterComponent object or ID (optional)
                
        Returns:
            ActiveModule: The created ActiveModule object.
        """
        try:
            module_id = data.get('module')
            if isinstance(module_id, Module):
                module = module_id
            else:
                module = Module.objects.get(id=module_id)
            
            component = None
            component_id = data.get('data_center_component')
            if component_id:
                if isinstance(component_id, DataCenterComponent):
                    component = component_id
                else:
                    component = DataCenterComponent.objects.get(id=component_id)
            
            data_center = None
            data_center_id = data.get('data_center')
            if data_center_id:
                if isinstance(data_center_id, DataCenter):
                    data_center = data_center_id
                else:
                    data_center = DataCenter.objects.get(id=data_center_id)
            elif component and component.data_center:
                data_center = component.data_center
            else:
                data_center = DataCenter.get_default()
            
            x = data.get('x')
            y = data.get('y')
            if x is None or y is None:
                raise ValueError("x and y coordinates are required")
                
            point, created = Point.objects.get_or_create(x=x, y=y)
            
            active_module = ActiveModule.objects.create(
                point=point,
                module=module,
                data_center_component=component,
                data_center=data_center
            )
            
            if component and not component.data_center:
                component.data_center = data_center
                component.save()
                logger.info(f"Associated component {component.name} with data center {data_center.name}")
            
            component_name = component.name if component else "No component"
            data_center_name = data_center.name if data_center else "No data center"
            logger.info(f"Created active module ID={active_module.id}, Module={module.name}, Component={component_name}, DataCenter={data_center_name}, at ({x}, {y})")
            
            from core.services import DataCenterValueService
            DataCenterValueService.force_recalculate_values(data_center)
            
            return active_module
            
        except Module.DoesNotExist:
            raise ValueError(f"Module with ID {module_id} does not exist")
        except DataCenterComponent.DoesNotExist:
            raise ValueError(f"DataCenterComponent with ID {component_id} does not exist")
        except DataCenter.DoesNotExist:
            raise ValueError(f"DataCenter with ID {data_center_id} does not exist")
        except Exception as e:
            logger.error(f"Error creating active module: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create active module: {str(e)}")
    
    @staticmethod
    def update_active_module_position(active_module_id, x, y):
        """
        Update only the position of an active module.
        
        Args:
            active_module_id (int): The ID of the active module to update.
            x (int): New X-coordinate.
            y (int): New Y-coordinate.
            
        Returns:
            ActiveModule: The updated ActiveModule object.
            
        Raises:
            ActiveModule.DoesNotExist: If the active module does not exist.
        """
        try:
            active_module = ActiveModule.objects.get(id=active_module_id)
            
            point, created = Point.objects.get_or_create(x=x, y=y)
            
            old_position = f"({active_module.point.x}, {active_module.point.y})"
            active_module.point = point
            active_module.save()
            
            logger.info(f"Updated active module ID={active_module_id} position from {old_position} to ({x}, {y})")
            return active_module
        except ActiveModule.DoesNotExist:
            logger.error(f"ActiveModule with ID {active_module_id} does not exist")
            raise
        except Exception as e:
            logger.error(f"Error updating active module position: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to update active module position: {str(e)}")
    
    @staticmethod
    def delete_active_module(active_module_id):
        """
        Delete an active module without recalculating values.
        Removes a module from the data center.
        
        Args:
            active_module_id (int): The ID of the active module to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
            
        Raises:
            ActiveModule.DoesNotExist: If the active module does not exist.
        """
        try:
            active_module = ActiveModule.objects.get(id=active_module_id)
            module_name = active_module.module.name
            component_name = active_module.data_center_component.name if active_module.data_center_component else "No component"
            position = f"({active_module.x}, {active_module.y})"
            
            active_module.delete()
            
            logger.info(f"Deleted active module ID={active_module_id}, Module={module_name}, Component={component_name}, at {position}")
            return True
        except ActiveModule.DoesNotExist:
            logger.error(f"ActiveModule with ID {active_module_id} does not exist")
            return False
        except Exception as e:
            logger.error(f"Error in delete_active_module: {str(e)}", exc_info=True)
            return False

class DataCenterValueService:
    """
    Service class for DataCenterValue-related operations.
    Provides methods to calculate and update values based on active modules.
    """
    
    @staticmethod
    def get_or_create_value(unit, component=None, data_center=None):
        """
        Get or create a DataCenterValue for a specific unit, component, and data center.
        
        Args:
            unit (str): The unit name (e.g., 'Space_X', 'Usable_Power').
            component (DataCenterComponent, optional): The component to associate with the value.
            data_center (DataCenter, optional): The data center to associate with the value.
            
        Returns:
            DataCenterValue: The existing or newly created DataCenterValue object.
        """
        if data_center is None:
            data_center = DataCenter.get_default()
            
        value, created = DataCenterValue.objects.get_or_create(
            unit=unit, 
            component=component, 
            data_center=data_center, 
            defaults={'value': 0}
        )
        return value
    
    @staticmethod
    def initialize_values_from_components(data_center):
        """
        Initialize DataCenterValue objects from unique units in DataCenterComponentAttributes.
        Sets initial values based on the constraints in the component attributes.
        
        Args:
            data_center (DataCenter): The data center to initialize values for.
        
        Special cases:
        - Space_X: Initialized to 0 (representing used space)
        - Space_Y: Initialized to 0 (representing used space)
        - Price: Initialized to 0
        - Units with above_amount=1: Initialized to 0 to force adding modules
        
        Returns:
            QuerySet: All DataCenterValue objects after initialization.
        """
        if data_center is None:
            raise ValueError("data_center parameter is required")
        
        components = DataCenterComponent.objects.all().prefetch_related('attributes')
        logger.info(f"Found {len(components)} components for initialization")
        
        component_values = {}
        
        for component in components:
            if hasattr(component, 'data_center') and not component.data_center:
                component.data_center = data_center
                component.save()
                
            component_values[component.id] = {}
            
            attributes = component.attributes.all()
            
            for attr in attributes:
                unit = attr.unit
                
                if unit in ['Space_X', 'Space_Y']:
                    component_values[component.id][unit] = 0
                elif attr.above_amount == 1 and attr.amount > 0:
                    component_values[component.id][unit] = 0
                elif unit == 'Price':
                    component_values[component.id][unit] = 0
                else:
                    component_values[component.id][unit] = 0
        
        with transaction.atomic():
            for component_id, units in component_values.items():
                component = DataCenterComponent.objects.get(id=component_id)
                
                for unit, value in units.items():
                    value_obj, created = DataCenterValue.objects.get_or_create(
                        unit=unit,
                        component=component,
                        data_center=data_center,
                        defaults={'value': value}
                    )
                    
                    if not created:
                        value_obj.value = value
                        value_obj.save()
                    
                    logger.info(f"DataCenter {data_center.name}, Component {component.name}, Unit {unit}: Initialized to {value}")
        
        return DataCenterValue.objects.filter(data_center=data_center)
    
    @staticmethod
    def recalculate_all_values(data_center):
        """
        Recalculate all DataCenterValues based on active modules.
        
        Args:
            data_center (DataCenter): The data center to recalculate for.
            
        Returns:
            dict: Dictionary of calculated values.
        """
        if data_center is None:
            raise ValueError("data_center parameter is required")
        
        from django.db.models import Q
        
        active_modules = ActiveModule.objects.filter(
            Q(data_center=data_center) | 
            Q(data_center_component__data_center=data_center)
        )
        
        return ModuleCalculationService.calculate_resource_usage(active_modules, data_center)
    
    @staticmethod
    def force_recalculate_values(data_center):
        """
        Force recalculation of all DataCenterValues based on active modules.
        
        Args:
            data_center (DataCenter): The data center to recalculate for.
            
        Returns:
            dict: Dictionary of calculated values.
        """
        if data_center is None:
            raise ValueError("data_center parameter is required")
        
        from django.db.models import Q
        
        active_modules = ActiveModule.objects.filter(
            Q(data_center=data_center) | 
            Q(data_center_component__data_center=data_center)
        )
        
        results = ModuleCalculationService.calculate_resource_usage(active_modules, data_center)
        
        # Get all global values
        global_values = {}
        for dcv in DataCenterValue.objects.filter(data_center=data_center, component__isnull=True):
            global_values[dcv.unit] = dcv.value
        
        # Get component-specific values
        component_values = {}
        for dcv in DataCenterValue.objects.filter(data_center=data_center).exclude(component=None):
            comp_id = str(dcv.component.id)
            if comp_id not in component_values:
                component_values[comp_id] = {}
            component_values[comp_id][dcv.unit] = dcv.value
        
        return {
            'global_values': global_values,
            'component_values': component_values
        }

class DataCenterComponentService:
    """
    Service class for DataCenterComponent-related operations.
    Provides methods to validate data center values against component specifications.
    """
    
    @staticmethod
    def validate_component_values(component=None, data_center=None):
        """
        Validate DataCenterValues against component specifications.
        
        Args:
            component (DataCenterComponent, optional): The component to validate.
                If None, validates all components.
            data_center (DataCenter): The data center to validate values for.
                
        Returns:
            tuple: (validation_result, violations)
                - validation_result (bool): True if all validations pass, False otherwise
                - violations (list): List of validation error messages
        """
        if data_center is None:
            raise ValueError("data_center parameter is required")
        
        from django.db.models import Q
        active_modules = ActiveModule.objects.filter(
            Q(data_center=data_center) | 
            Q(data_center_component__data_center=data_center)
        )
        ModuleCalculationService.calculate_resource_usage(active_modules, data_center)
        
        calculated_values = DataCenterValueService.force_recalculate_values(data_center)
        
        validation_passed = True
        
        unique_violations_dict = {}
        
        if component:
            components = [component]
        else:
            components = DataCenterComponent.objects.filter(data_center=data_center)
            
            if not components.exists():
                components = DataCenterComponent.objects.all()
        
        logger.info(f"Validating {components.count()} components in data center {data_center.name}")
        
        global_values = calculated_values.get('global_values', {})
        component_values = calculated_values.get('component_values', {})
                
        for comp in components:
            logger.info(f"Validating component: {comp.name} (ID: {comp.id})")
            
            attributes = comp.attributes.all()
            
            comp_values = {}
            comp_id = str(comp.id)
            if comp_id in component_values:
                comp_values = component_values[comp_id]
            
            logger.info(f"Component values: {comp_values}")
            
            for attr in attributes:
                # Skip validation if unconstrained is true or amount is -1
                if attr.unconstrained or attr.amount == -1:
                    logger.info(f"Skipping validation for {comp.name}, {attr.unit} (unconstrained or amount is -1)")
                    continue
                
                unit = attr.unit
                amount = attr.amount
                
                # Only use the component's actual values, don't fall back to global
                current_value = comp_values.get(unit, 0)
                
                if unit in ['Space_X', 'Space_Y']:
                    total_space = data_center.space_x if unit == 'Space_X' else data_center.space_y
                    
                    if current_value > total_space:
                        validation_passed = False
                        message = f"Component {comp.name}: Used {unit} ({current_value}) exceeds total {unit} ({total_space})"
                        key = (comp.name, unit, "exceeds")
                        unique_violations_dict[key] = message
                        logger.warning(message)
                    continue
                
                if attr.below_amount:
                    if current_value > amount:
                        validation_passed = False
                        message = f"Component {comp.name}: {unit} value ({current_value}) should be less than or equal to {amount}"
                        key = (comp.name, unit, "below")
                        unique_violations_dict[key] = message
                        logger.warning(message)

                if attr.above_amount:
                    if current_value < amount:
                        validation_passed = False
                        message = f"Component {comp.name}: {unit} value ({current_value}) should be greater than or equal to {amount}"
                        key = (comp.name, unit, "above")
                        unique_violations_dict[key] = message
                        logger.warning(message)
        
        violations = list(unique_violations_dict.values())
        
        return validation_passed, violations

class ModuleCalculationService:
    """
    Service class for module calculation operations.
    Provides methods to calculate resource usage and validate constraints.
    """
    
    @staticmethod
    def calculate_resource_usage(active_modules, data_center):
        """
        Calculate resource usage based on active modules.
        
        Args:
            active_modules (QuerySet): QuerySet of ActiveModule objects.
            data_center (DataCenter): The data center to calculate for.
                
        Returns:
            dict: Dictionary of calculated values.
        """
        if data_center is None:
            raise ValueError("data_center parameter is required")
        
        global_results = {}
        component_results = {}
        
        logger.info(f"Calculating resource usage for {active_modules.count()} active modules in data center {data_center.name}")
        
        for active_module in active_modules:
            module = active_module.module
            component = active_module.data_center_component
            
            # Initialize component in results if it has a component
            if component and component.id not in component_results:
                component_results[component.id] = {}
            
            attributes = module.attributes.all()
            
            for attr in attributes:
                unit = attr.unit
                amount = attr.amount
                
                # Initialize unit in global results if not present
                if unit not in global_results:
                    global_results[unit] = 0
                
                # Initialize unit in component results if applicable
                if component and unit not in component_results[component.id]:
                    component_results[component.id][unit] = 0
                
                # Update values based on input/output
                if attr.is_input:
                    global_results[unit] -= amount
                    if component:
                        component_results[component.id][unit] -= amount
                elif attr.is_output:
                    global_results[unit] += amount
                    if component:
                        component_results[component.id][unit] += amount
                
                # Log the calculation for debugging
                if component:
                    logger.debug(f"Module {module.name} in component {component.name}: {unit} {'consumed' if attr.is_input else 'produced'} {amount}")
                else:
                    logger.debug(f"Module {module.name} (no component): {unit} {'consumed' if attr.is_input else 'produced'} {amount}")
        
        # Log the calculated results
        logger.info(f"Global results: {global_results}")
        logger.info(f"Component results: {component_results}")
        
        # Update global DataCenterValues
        with transaction.atomic():
            for unit, value in global_results.items():
                values = DataCenterValue.objects.filter(
                    data_center=data_center,
                    unit=unit,
                    component__isnull=True
                )
                
                if values.exists():
                    # If multiple values exist, keep only one and delete the rest
                    if values.count() > 1:
                        primary_value = values.first()
                        primary_value.value = value
                        primary_value.save()
                        
                        # Delete duplicates
                        values.exclude(id=primary_value.id).delete()
                        logger.warning(f"Removed {values.count()-1} duplicate global DataCenterValue entries for {unit}")
                    else:
                        # Just update the single value
                        values.update(value=value)
                else:
                    # Create a new value if none exists
                    DataCenterValue.objects.create(
                        data_center=data_center,
                        unit=unit,
                        value=value,
                        component=None  # Explicitly set component to None for global values
                    )
            
            # Update component-specific DataCenterValues
            for component_id, units in component_results.items():
                try:
                    component = DataCenterComponent.objects.get(id=component_id)
                    
                    for unit, value in units.items():
                        values = DataCenterValue.objects.filter(
                            data_center=data_center,
                            unit=unit,
                            component=component
                        )
                        
                        if values.exists():
                            # If multiple values exist, keep only one and delete the rest
                            if values.count() > 1:
                                primary_value = values.first()
                                primary_value.value = value
                                primary_value.save()
                                
                                # Delete duplicates
                                values.exclude(id=primary_value.id).delete()
                                logger.warning(f"Removed {values.count()-1} duplicate component DataCenterValue entries for {component.name}, {unit}")
                            else:
                                # Just update the single value
                                values.update(value=value)
                        else:
                            # Create a new value if none exists
                            DataCenterValue.objects.create(
                                data_center=data_center,
                                unit=unit,
                                value=value,
                                component=component
                            )
                        
                        # Log the update for debugging
                        logger.debug(f"Updated component {component.name} {unit} value to {value}")
                except DataCenterComponent.DoesNotExist:
                    logger.error(f"Component with ID {component_id} does not exist")
        
        return {
            'global_values': global_results,
            'component_values': component_results
        }
