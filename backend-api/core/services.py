from .models import (
    Module, ActiveModule, DataCenterValue, ModuleAttribute,
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
    def get_all_active_modules():
        """
        Get all active modules from the database.
        
        Returns:
            QuerySet: All ActiveModule objects in the database.
            
        Usage:
            active_modules = ActiveModuleService.get_all_active_modules()
        """
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
            
            for field in Module._meta.fields:
                logger.info(f"Module {field.name}: {getattr(module, field.name)}")
            
            active_module = ActiveModule.objects.create(module=module, **data)
            
            component_name = component.name if component else "No component"
            logger.info(f"Created active module ID={active_module.id}, Module={module.name}, Component={component_name}, at ({data.get('x')}, {data.get('y')})")
            
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
            
            # Just delete the module without recalculating values or validating
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
    def get_or_create_value(unit):
        """
        Get or create a DataCenterValue for a specific unit.
        
        Args:
            unit (str): The unit name (e.g., 'Space_X', 'Usable_Power').
            
        Returns:
            DataCenterValue: The existing or newly created DataCenterValue object.
        """
        value, created = DataCenterValue.objects.get_or_create(unit=unit, defaults={'value': 0})
        return value
    
    @staticmethod
    def initialize_values_from_components():
        """
        Initialize DataCenterValue objects from unique units in DataCenterComponentAttributes.
        Sets initial values based on the constraints in the component attributes.
        
        Special cases:
        - Space_X: Initialized to SPACE_X_INITIAL (total available space in X dimension)
        - Space_Y: Initialized to SPACE_Y_INITIAL (total available space in Y dimension)
        - Price: Initialized to 0
        - Units with above_amount=1: Initialized to 0 to force adding modules
        
        Returns:
            QuerySet: All DataCenterValue objects after initialization.
        """
        # Get all components
        components = DataCenterComponent.objects.all().prefetch_related('attributes')
        logger.info(f"Found {len(components)} components for initialization")
        
        # Create a dictionary to store initial values for each component and unit
        component_values = {}
        
        # Process each component
        for component in components:
            component_values[component.id] = {}
            
            # Get all attributes for this component
            attributes = component.attributes.all()
            
            for attr in attributes:
                unit = attr.unit
                
                # Special handling for Space_X and Space_Y
                if unit == 'Space_X':
                    component_values[component.id][unit] = DataCenterConstants.SPACE_X_INITIAL
                elif unit == 'Space_Y':
                    component_values[component.id][unit] = DataCenterConstants.SPACE_Y_INITIAL
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
                        defaults={'value': value}
                    )
                    
                    if not created:
                        value_obj.value = value
                        value_obj.save()
                    
                    logger.info(f"Component {component.name}, Unit {unit}: Initialized to {value}")
        
        return DataCenterValue.objects.all()
    
    @staticmethod
    def recalculate_all_values():
        """
        Recalculate all DataCenterValues based on active modules and their components.
        
        This method:
        1. Gets all active modules and their attributes
        2. Groups them by component
        3. Calculates the total for each unit across all modules in each component
        4. Updates the DataCenterValue objects accordingly
        
        Special cases:
        - Space_X and Space_Y: Calculated as (initial value - total used)
        - Other units: Set directly to the calculated total
        
        Returns:
            QuerySet: All DataCenterValue objects after recalculation.
        """
        # Get all active modules with their related modules and components
        active_modules = ActiveModule.objects.all().select_related('module', 'data_center_component')
        
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
                valid_units = set(DataCenterComponentAttribute.objects.values_list('unit', flat=True).distinct())
            
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
            logger.info(f"Component {component_id}: Space consumption: {space_consumption}")
            
            # Update DataCenterValue objects for this component
            with transaction.atomic():
                # First handle Space_X and Space_Y
                for space_unit in ['Space_X', 'Space_Y']:
                    if space_unit in valid_units:
                        value_obj, created = DataCenterValue.objects.get_or_create(
                            unit=space_unit,
                            component=component,
                            defaults={'value': 0}
                        )
                        
                        old_value = value_obj.value
                        consumed = space_consumption[space_unit]
                        
                        # Calculate remaining space
                        if space_unit == 'Space_X':
                            value_obj.value = DataCenterConstants.SPACE_X_INITIAL - consumed
                            logger.info(f"Component {component_id}, Unit {space_unit}: {DataCenterConstants.SPACE_X_INITIAL} - {consumed} = {value_obj.value} (was {old_value})")
                        else:  # Space_Y
                            value_obj.value = DataCenterConstants.SPACE_Y_INITIAL - consumed
                            logger.info(f"Component {component_id}, Unit {space_unit}: {DataCenterConstants.SPACE_Y_INITIAL} - {consumed} = {value_obj.value} (was {old_value})")
                        
                        value_obj.save()
                
                # Then handle all other units
                for unit in valid_units:
                    if unit not in ['Space_X', 'Space_Y']:
                        value_obj, created = DataCenterValue.objects.get_or_create(
                            unit=unit,
                            component=component,
                            defaults={'value': 0}
                        )
                        
                        old_value = value_obj.value
                        total = unit_totals[unit]
                        
                        # For other units, we just use the total
                        value_obj.value = total
                        logger.info(f"Component {component_id}, Unit {unit}: Updated to {total} (was {old_value})")
                        
                        value_obj.save()
        
        return DataCenterValue.objects.all()

class DataCenterComponentService:
    """
    Service class for DataCenterComponent-related operations.
    Provides methods to validate data center values against component specifications.
    """
    
    @staticmethod
    def validate_component_values(component=None):
        """
        Validate that all current DataCenterValues meet the specifications for a component.
        
        This method:
        1. Gets all DataCenterComponentAttributes for the specified component (or all components)
        2. Gets all DataCenterValues for the component
        3. Checks each value against its specifications
        4. Logs any violations
        
        Args:
            component (DataCenterComponent, optional): The component to validate.
                If None, all components will be validated.
        
        Returns:
            tuple: (bool, list) - Success flag and list of violation messages.
            
        Usage:
            is_valid, violations = DataCenterComponentService.validate_component_values(component)
            if is_valid:
                # All specifications are met
            else:
                # Some specifications are not met, see violations list
        """
        logger.info(f"Validating data center component: {component.name if component else 'All components'}")
        
        # Get components to validate
        if component:
            components = [component]
        else:
            components = DataCenterComponent.objects.all()
        
        # Track all violations
        all_violations = []
        
        # Validate each component
        for comp in components:
            logger.info(f"Validating component: {comp.name}")
            
            # Get all attributes for this component
            attributes = comp.attributes.all()
            
            # Get all current values for this component
            values = {value.unit: value.value for value in DataCenterValue.objects.filter(component=comp)}
            
            # Log current state for debugging
            logger.info(f"Found {len(attributes)} specifications to validate for component {comp.name}")
            logger.info(f"Current values for component {comp.name}: {values}")
            
            # Check each attribute against current values
            for attr in attributes:
                unit = attr.unit
                current_value = values.get(unit, 0)
                
                # Log what we're checking
                logger.info(f"Validating {comp.name} - {unit}: Current Value: {current_value}, Spec Amount: {attr.amount}")
                
                # Check below constraint
                if attr.below_amount == 1 and current_value > attr.amount:
                    violation_msg = f"Component {comp.name}, Unit {unit} value ({current_value}) exceeds maximum allowed ({attr.amount})"
                    logger.error(violation_msg)
                    all_violations.append(violation_msg)
                
                # Check above constraint
                if attr.above_amount == 1 and current_value < attr.amount:
                    violation_msg = f"Component {comp.name}, Unit {unit} value ({current_value}) is below minimum required ({attr.amount})"
                    logger.error(violation_msg)
                    all_violations.append(violation_msg)
        
        # Return success flag and violations list
        return len(all_violations) == 0, all_violations

class ModuleCalculationService:
    """
    Service class for module calculation operations.
    Provides methods to calculate resource usage based on active modules.
    """
    
    @staticmethod
    def calculate_resource_usage(active_modules=None):
        """
        Calculate total resource usage based on active modules.
        
        This method:
        1. Gets all active modules if not provided
        2. Calculates the total amount for each unit across all modules
        3. Combines with current DataCenterValues
        
        Args:
            active_modules (QuerySet, optional): ActiveModule objects to calculate from.
                If None, all active modules will be used.
                
        Returns:
            dict: Dictionary mapping unit names to their total values.
                Includes both calculated totals from modules and current DataCenterValues.
        """
        if active_modules is None:
            active_modules = ActiveModule.objects.all().select_related('module')
        
        # Group by unit and sum amounts
        unit_totals = {}
        # Track space consumption separately
        space_consumption = {'Space_X': 0, 'Space_Y': 0}
        
        for am in active_modules:
            attributes = ModuleAttribute.objects.filter(module=am.module)
            
            for attr in attributes:
                unit = attr.unit
                amount = attr.amount
                
                if unit in ['Space_X', 'Space_Y']:
                    space_consumption[unit] += amount
                    continue
                
                # Initialize if not exists
                if unit not in unit_totals:
                    unit_totals[unit] = 0
                
                # For output attributes, add to the total (resources produced)
                if attr.is_output:
                    unit_totals[unit] += amount
                # For input attributes, subtract from the total (resources consumed)
                else:
                    unit_totals[unit] -= amount
    
        # Get current DataCenterValues
        all_values = {value.unit: value.value for value in DataCenterValue.objects.all()}
        
        # Prepare result
        result = {}
        
        # Add space values with proper calculation
        result['Space_X'] = DataCenterConstants.SPACE_X_INITIAL - space_consumption['Space_X']
        result['Space_Y'] = DataCenterConstants.SPACE_Y_INITIAL - space_consumption['Space_Y']
        
        # Add other calculated values
        for unit, total in unit_totals.items():
            result[unit] = total
        
        # Add any values from DataCenterValues that aren't in the result yet
        for unit, value in all_values.items():
            if unit not in result:
                result[unit] = value
        
        return result
