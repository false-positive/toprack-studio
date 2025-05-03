from .models import (
    DataCenter, Module, ActiveModule, DataCenterValue, ModuleAttribute,
    DataCenterComponent, DataCenterComponentAttribute
)
from django.db.models import Sum, Q
from django.db import transaction
from backend.settings import DataCenterConstants
import logging

logger = logging.getLogger('django')

class ModuleService:
    """
    Service class for Module-related operations.
    Provides methods to retrieve and manage Module objects.
    """
    
    @staticmethod
    def get_all_modules():
        """
        Get all modules from the database.
        
        Returns:
            QuerySet: All Module objects in the database.
        """
        return Module.objects.all()
    
    @staticmethod
    def get_module(module_id):
        """
        Get a specific module by ID.
        
        Args:
            module_id (int): The ID of the module to retrieve.
            
        Returns:
            Module: The Module object if found, None otherwise.
        """
        try:
            return Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return None

class ActiveModuleService:
    """
    Service class for ActiveModule-related operations.
    Provides methods to create, delete, and manage active modules in the data center.
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
            # Filter by data_center_component's data_center instead of directly by data_center
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
            
        Raises:
            ValueError: If the module or component does not exist.
            Exception: For any other errors during creation.
        """
        try:
            # Extract and validate module
            module_id = data.pop('module').id if isinstance(data.get('module'), Module) else data.pop('module')
            module = Module.objects.get(id=module_id)
            
            # Extract and validate component if provided
            component = None
            if 'data_center_component' in data:
                component_id = data.pop('data_center_component').id if isinstance(data.get('data_center_component'), DataCenterComponent) else data.pop('data_center_component')
                if component_id:
                    component = DataCenterComponent.objects.get(id=component_id)
                    data['data_center_component'] = component
            
            # Get data center from component or use default
            data_center = None
            if component and component.data_center:
                data_center = component.data_center
            else:
                # Use default data center if none provided
                data_center = DataCenter.get_default()
                
            # If component is provided but no data center, update component
            if component and not component.data_center:
                component.data_center = data_center
                component.save()
            
            for field in Module._meta.fields:
                logger.info(f"Module {field.name}: {getattr(module, field.name)}")
            
            active_module = ActiveModule.objects.create(module=module, **data)
            
            component_name = component.name if component else "No component"
            data_center_name = data_center.name if data_center else "No data center"
            logger.info(f"Created active module ID={active_module.id}, Module={module.name}, Component={component_name}, DataCenter={data_center_name}, at ({data.get('x')}, {data.get('y')})")
            
            return active_module
        except Module.DoesNotExist:
            logger.error(f"Module with ID {module_id} does not exist")
            raise ValueError(f"Module with ID {module_id} does not exist")
        except DataCenterComponent.DoesNotExist:
            logger.error(f"DataCenterComponent with ID {component_id} does not exist")
            raise ValueError(f"DataCenterComponent with ID {component_id} does not exist")
        except Exception as e:
            logger.error(f"Error in create_active_module: {str(e)}", exc_info=True)
            raise
    
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
    Provides methods to initialize, recalculate, and manage data center values.
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
    def initialize_values_from_components(data_center=None):
        """
        Initialize DataCenterValue objects from unique units in DataCenterComponentAttributes.
        Sets initial values based on the constraints in the component attributes.
        
        Args:
            data_center (DataCenter, optional): The data center to initialize values for.
                If None, uses the default data center.
        
        Special cases:
        - Space_X: Initialized to 0 (representing used space)
        - Space_Y: Initialized to 0 (representing used space)
        - Price: Initialized to 0
        - Units with above_amount=1: Initialized to 0 to force adding modules
        
        Returns:
            QuerySet: All DataCenterValue objects after initialization.
        """
        # Get or create the default data center if none provided
        if data_center is None:
            data_center = DataCenter.get_default()
        
        # Get all components
        components = DataCenterComponent.objects.all().prefetch_related('attributes')
        logger.info(f"Found {len(components)} components for initialization")
        
        # Create a dictionary to store initial values for each component and unit
        component_values = {}
        
        # Process each component
        for component in components:
            # Associate component with data center if not already
            if hasattr(component, 'data_center') and not component.data_center:
                component.data_center = data_center
                component.save()
                
            component_values[component.id] = {}
            
            # Get all attributes for this component
            attributes = component.attributes.all()
            
            for attr in attributes:
                unit = attr.unit
                
                # Special handling for Space_X and Space_Y - initialize to 0 (used space)
                if unit in ['Space_X', 'Space_Y']:
                    component_values[component.id][unit] = 0
                # For units that need to be above a certain amount, start at 0
                elif attr.above_amount == 1 and attr.amount > 0:
                    component_values[component.id][unit] = 0
                # For Price, start at 0
                elif unit == 'Price':
                    component_values[component.id][unit] = 0
                # For other units, use a default of 0
                else:
                    component_values[component.id][unit] = 0
        
        # Create or update DataCenterValue objects for each component and unit
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
    def recalculate_all_values(data_center=None):
        """
        Recalculate all DataCenterValues based on active modules and their components.
        
        Args:
            data_center (DataCenter, optional): The data center to recalculate values for.
                If None, uses the default data center.
        
        Returns:
            QuerySet: All DataCenterValue objects after recalculation.
        """
        # Get or create the default data center if none provided
        if data_center is None:
            data_center = DataCenter.get_default()
        
        # Get all active modules with their related modules and components for this data center
        active_modules = ActiveModule.objects.filter(
            Q(data_center_component__data_center=data_center) | 
            Q(data_center_component__isnull=True)
        ).select_related('module', 'data_center_component')
        
        # Calculate global totals first
        global_totals = {}
        for am in active_modules:
            # Get all attributes for this module
            attributes = ModuleAttribute.objects.filter(module=am.module)
            
            for attr in attributes:
                unit = attr.unit
                amount = attr.amount
                
                # Special handling for Space_X and Space_Y
                if unit in ['Space_X', 'Space_Y']:
                    if unit not in global_totals:
                        global_totals[unit] = 0
                    global_totals[unit] += amount
                    continue
                    
                # For other units, add or subtract based on is_output
                if unit not in global_totals:
                    global_totals[unit] = 0
                    
                if attr.is_output:
                    global_totals[unit] += amount
                else:
                    global_totals[unit] -= amount
        
        logger.info(f"Global totals: {global_totals}")
        
        # Group active modules by component
        modules_by_component = {}
        for am in active_modules:
            component_id = am.data_center_component_id if am.data_center_component_id else 'global'
            if component_id not in modules_by_component:
                modules_by_component[component_id] = []
            modules_by_component[component_id].append(am)
        
        # Process each component separately
        for component_id, component_modules in modules_by_component.items():
            # Skip if no modules for this component
            if not component_modules:
                continue
                
            # Get the component object if it's not 'global'
            component = None
            if component_id != 'global':
                component = DataCenterComponent.objects.get(id=component_id)
                
                # Get valid units for this component
                valid_units = set(attr.unit for attr in component.attributes.all())
            else:
                # For modules without a component, use all units
                valid_units = set(ModuleAttribute.objects.values_list('unit', flat=True).distinct())
            
            # Create dictionaries to store unit totals and space consumption
            unit_totals = {unit: 0 for unit in valid_units}
            space_consumption = {'Space_X': 0, 'Space_Y': 0}
            
            # Calculate totals for each unit from active modules in this component
            for active_module in component_modules:
                # Get all attributes for this module
                attributes = ModuleAttribute.objects.filter(module=active_module.module)
                
                for attr in attributes:
                    unit = attr.unit
                    amount = attr.amount
                    
                    # Special handling for Space_X and Space_Y - always add as consumption
                    if unit in ['Space_X', 'Space_Y']:
                        space_consumption[unit] += amount
                        continue
                        
                    # Only update totals for units that are defined in this component
                    if unit in valid_units:
                        # For output attributes, add to the total
                        if attr.is_output:
                            unit_totals[unit] += amount
                        else:
                            unit_totals[unit] -= amount
            
            logger.info(f"Component {component_id}: Calculated unit totals: {unit_totals}")
            
            # Update DataCenterValue objects for this component
            with transaction.atomic():
                # First handle Space_X and Space_Y - set to consumed space
                for space_unit in ['Space_X', 'Space_Y']:
                    if space_unit in valid_units:
                        value_obj, created = DataCenterValue.objects.get_or_create(
                            unit=space_unit,
                            component=component,
                            data_center=data_center,
                            defaults={'value': space_consumption.get(space_unit, 0)}
                        )
                        
                        if not created:
                            value_obj.value = space_consumption.get(space_unit, 0)
                            value_obj.save()
                
                # Then handle all other units - use global totals for component values
                for unit in valid_units:
                    if unit not in ['Space_X', 'Space_Y']:
                        value_obj, created = DataCenterValue.objects.get_or_create(
                            unit=unit,
                            component=component,
                            data_center=data_center,
                            defaults={'value': global_totals.get(unit, 0)}
                        )
                        
                        if not created:
                            value_obj.value = global_totals.get(unit, 0)
                            value_obj.save()
        
        # Update global values (not associated with any component)
        for unit, value in global_totals.items():
            value_obj, created = DataCenterValue.objects.get_or_create(
                unit=unit,
                component=None,
                data_center=data_center,
                defaults={'value': value}
            )
            
            if not created:
                value_obj.value = value
                value_obj.save()
        
        return DataCenterValue.objects.filter(data_center=data_center)

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
            data_center (DataCenter, optional): The data center to validate for.
                If None, uses the default data center.
            
        Returns:
            tuple: (validation_result, violations)
                validation_result (bool): True if all validations pass, False otherwise.
                violations (list): List of validation failure messages.
        """
        # Get or create the default data center if none provided
        if data_center is None:
            data_center = DataCenter.get_default()
        
        # Get components to validate
        if component:
            components = [component]
        else:
            components = DataCenterComponent.objects.filter(data_center=data_center)
        
        validation_passed = True
        violations = []
        
        # For each component, validate its attributes against current values
        for comp in components:
            # Get all attributes for this component
            attributes = comp.attributes.all()
            
            # Get all values for this component
            value_objects = DataCenterValue.objects.filter(component=comp, data_center=data_center)
            
            # Create a dictionary of current values by unit
            values = {value.unit: value.value for value in value_objects}
            
            # Log the values for debugging
            logger.info(f"Validating component {comp.name} with values: {values}")
            
            # Validate each attribute
            for attr in attributes:
                unit = attr.unit
                amount = attr.amount
                
                # Get current value, default to 0 if not found
                current_value = values.get(unit, 0)
                
                # Special handling for Space_X and Space_Y - check if used space is less than total space
                if unit in ['Space_X', 'Space_Y']:
                    total_space = data_center.space_x if unit == 'Space_X' else data_center.space_y
                    
                    # Check if used space exceeds total space
                    if current_value > total_space:
                        validation_passed = False
                        message = f"Component {comp.name}: Used {unit} ({current_value}) exceeds total {unit} ({total_space})"
                        violations.append(message)
                        logger.warning(message)
                    continue
                
                # Check below_amount constraint - value should be less than or equal to amount
                if attr.below_amount == 1 and current_value > amount:
                    validation_passed = False
                    message = f"Component {comp.name}: {unit} value ({current_value}) should be less than or equal to {amount}"
                    violations.append(message)
                    logger.warning(message)
                
                # Check above_amount constraint - value should be greater than or equal to amount
                if attr.above_amount == 1 and current_value < amount:
                    validation_passed = False
                    message = f"Component {comp.name}: {unit} value ({current_value}) should be greater than or equal to {amount}"
                    violations.append(message)
                    logger.warning(message)
        
        return validation_passed, violations

class ModuleCalculationService:
    """
    Service class for module calculation operations.
    Provides methods to calculate resource usage and validate constraints.
    """
    
    @staticmethod
    def calculate_resource_usage(active_modules, data_center=None):
        """
        Calculate total resource usage for all active modules.
        
        Args:
            active_modules (QuerySet): ActiveModule objects to calculate resources for.
            data_center (DataCenter, optional): The data center to calculate for.
                If None, uses all active modules.
                
        Returns:
            dict: Dictionary of resource totals by unit.
        """
        # If data_center is provided, filter active_modules by data_center_component__data_center
        if data_center:
            active_modules = active_modules.filter(data_center_component__data_center=data_center)
            
        # Initialize results dictionary
        results = {}
        
        # Calculate total resources for each active module
        for active_module in active_modules:
            module = active_module.module
            
            # Get all attributes for this module
            attributes = ModuleAttribute.objects.filter(module=module)
            
            # Process each attribute
            for attr in attributes:
                unit = attr.unit
                amount = attr.amount
                
                # If it's an output (produced), add to the total
                if attr.is_output:
                    if unit in results:
                        results[unit] = results[unit] + amount
                    else:
                        results[unit] = amount
                # If it's an input (consumed), subtract from the total
                else:
                    if unit in results:
                        results[unit] = results[unit] - amount
                    else:
                        results[unit] = -amount
        
        # Add space calculations if data_center is provided
        if data_center:
            # Calculate space usage
            space_x_used = 0
            space_y_used = 0
            
            for active_module in active_modules:
                module = active_module.module
                # Get Space_X and Space_Y attributes
                space_x_attr = ModuleAttribute.objects.filter(module=module, unit='Space_X').first()
                space_y_attr = ModuleAttribute.objects.filter(module=module, unit='Space_Y').first()
                
                if space_x_attr:
                    space_x_used += space_x_attr.amount
                if space_y_attr:
                    space_y_used += space_y_attr.amount
            
            results['Space_X'] = space_x_used
            results['Space_Y'] = space_y_used
            results['Space_X_Available'] = data_center.space_x - space_x_used
            results['Space_Y_Available'] = data_center.space_y - space_y_used
        
        return results
