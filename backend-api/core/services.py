from .models import Module, ActiveModule, DataCenterSpecs, DataCenterValue, ModuleAttribute
from django.db.models import Sum
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
    An active module is a module that has been placed in the data center.

    Provides methods to retrieve, create, and delete ActiveModule objects.
    ActiveModules represent modules placed in the data center.
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
            data (dict): Dictionary containing module ID/object and coordinates.
                Required keys:
                - module: Module object or ID
                - x: X-coordinate (int)
                - y: Y-coordinate (int)
            
        Returns:
            ActiveModule: The created ActiveModule object.
            
        Raises:
            ValueError: If the module does not exist.
            Exception: For any other errors during creation.
            
        Usage:
            data = {
                'module': 1,  # or Module object
                'x': 100,
                'y': 200
            }
            active_module = ActiveModuleService.create_active_module(data)
        """
        try:
            module_id = data.pop('module').id if isinstance(data.get('module'), Module) else data.pop('module')
            module = Module.objects.get(id=module_id)
            
            for field in Module._meta.fields:
                logger.info(f"Module {field.name}: {getattr(module, field.name)}")
            
            active_module = ActiveModule.objects.create(module=module, **data)
            logger.info(f"Created active module ID={active_module.id}, Module={module.name}, at ({data.get('x')}, {data.get('y')})")
            
            return active_module
        except Module.DoesNotExist:
            logger.error(f"Module with ID {module_id} does not exist")
            raise ValueError(f"Module with ID {module_id} does not exist")
        except Exception as e:
            logger.error(f"Error in create_active_module: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def delete_active_module(active_module_id):
        """
        Delete an active module without recalculation.
        Removes a module from the data center.
        
        Args:
            active_module_id (int): The ID of the active module to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            active_module = ActiveModule.objects.get(id=active_module_id)
            logger.info(f"Deleting active module ID={active_module_id}, Module={active_module.module.name}")
            
            active_module.delete()
            logger.info(f"Successfully deleted active module ID={active_module_id}")
                
            return True
        except ActiveModule.DoesNotExist:
            logger.error(f"Active module with ID {active_module_id} does not exist")
            return False
        except Exception as e:
            logger.error(f"Error deleting active module: {str(e)}", exc_info=True)
            return False

class DataCenterValueService:
    """
    Service class for DataCenterValue-related operations.
    Provides methods to manage and calculate values for different units in the data center.
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
    def initialize_values_from_specs():
        """
        Initialize DataCenterValue objects from unique units in DataCenterSpecs.
        Sets initial values based on the constraints in the specs.
        
        Special cases:
        - Space_X: Initialized to SPACE_X_INITIAL (total available space in X dimension)
        - Space_Y: Initialized to SPACE_Y_INITIAL (total available space in Y dimension)
        - Price: Initialized to 0
        - Units with above_amount=1: Initialized to 0 to force adding modules
        
        Returns:
            QuerySet: All DataCenterValue objects after initialization.
            
        Usage:
            values = DataCenterValueService.initialize_values_from_specs()
        """
        # Get unique units from DataCenterSpecs
        unique_units = set(DataCenterSpecs.objects.values_list('unit', flat=True).distinct())
        logger.info(f"Found {len(unique_units)} unique units in specs")
        
        # Get all specs to determine initial values
        all_specs = DataCenterSpecs.objects.all()
        
        # Create a dictionary to store initial values for each unit
        initial_values = {}
        
        # Special handling for Space_X and Space_Y if they exist in specs
        if 'Space_X' in unique_units:
            initial_values['Space_X'] = DataCenterConstants.SPACE_X_INITIAL
        if 'Space_Y' in unique_units:
            initial_values['Space_Y'] = DataCenterConstants.SPACE_Y_INITIAL
        
        # Determine initial values based on constraints
        for unit in unique_units:
            # Default to 0 if not already set
            if unit not in initial_values:
                initial_values[unit] = 0
            
            # Find specs for this unit
            unit_specs = all_specs.filter(unit=unit)
            
            for spec in unit_specs:
                # For Price, set to 0 initially
                if unit == 'Price':
                    initial_values[unit] = 0
                    continue
                
                # If there's an above_amount constraint, set value to 0 (needs to be increased)
                if spec.above_amount == 1 and spec.amount > 0 and unit not in ['Space_X', 'Space_Y']:
                    # For "above" constraints, start at 0 to force adding modules
                    initial_values[unit] = 0
        
        # Create or update DataCenterValue for each unit
        for unit, value in initial_values.items():
            try:
                value_obj = DataCenterValue.objects.get(unit=unit)
                value_obj.value = value
                value_obj.save()
                logger.info(f"Updated DataCenterValue for {unit}: {value}")
            except DataCenterValue.DoesNotExist:
                value_obj = DataCenterValue.objects.create(unit=unit, value=value)
                logger.info(f"Created DataCenterValue for {unit}: {value}")
        
        return DataCenterValue.objects.all()
    
    @staticmethod
    def recalculate_all_values():
        """
        Recalculate all DataCenterValues based on active modules.
        
        This method:
        1. Gets all active modules and their attributes
        2. Calculates the total for each unit across all modules
        3. Updates the DataCenterValue objects accordingly
        
        Special cases:
        - Space_X and Space_Y: Calculated as (initial value - total used)
        - Other units: Set directly to the calculated total
        
        Returns:
            QuerySet: All DataCenterValue objects after recalculation.
        """
        # Get all active modules with their related modules
        active_modules = ActiveModule.objects.all().select_related('module')
        
        # Get all valid units from DataCenterSpecs
        valid_units = set(DataCenterSpecs.objects.values_list('unit', flat=True).distinct())
        logger.info(f"Recalculating values for {len(valid_units)} units")
        
        # Create a dictionary to store unit totals (initialize with 0 for all valid units)
        unit_totals = {unit: 0 for unit in valid_units}
        
        # Track space consumption separately
        space_consumption = {'Space_X': 0, 'Space_Y': 0}
        
        # Calculate totals for each unit from active modules
        for active_module in active_modules:
            # Get all attributes for this module (prefetch to reduce queries)
            attributes = ModuleAttribute.objects.filter(module=active_module.module)
            
            for attr in attributes:
                unit = attr.unit
                amount = attr.amount
                
                # Special handling for Space_X and Space_Y - always add as consumption
                if unit in ['Space_X', 'Space_Y']:
                    space_consumption[unit] += amount
                    continue
                
                # Only update totals for units that are defined in DataCenterSpecs
                if unit in valid_units:
                    # For output attributes, add to the total
                    if attr.is_output:
                        unit_totals[unit] += amount
                    else:
                        unit_totals[unit] -= amount
        
        logger.info(f"Calculated unit totals: {unit_totals}")
        logger.info(f"Space consumption: {space_consumption}")
        
        # Update DataCenterValue objects in a single transaction
        with transaction.atomic():
            # First handle Space_X and Space_Y
            for space_unit in ['Space_X', 'Space_Y']:
                if space_unit in valid_units:
                    value_obj, created = DataCenterValue.objects.get_or_create(
                        unit=space_unit, 
                        defaults={'value': 0}
                    )
                    
                    old_value = value_obj.value
                    consumed = space_consumption[space_unit]
                    
                    # Calculate remaining space
                    if space_unit == 'Space_X':
                        value_obj.value = DataCenterConstants.SPACE_X_INITIAL - consumed
                        logger.info(f"Unit {space_unit}: {DataCenterConstants.SPACE_X_INITIAL} - {consumed} = {value_obj.value} (was {old_value})")
                    else:  # Space_Y
                        value_obj.value = DataCenterConstants.SPACE_Y_INITIAL - consumed
                        logger.info(f"Unit {space_unit}: {DataCenterConstants.SPACE_Y_INITIAL} - {consumed} = {value_obj.value} (was {old_value})")
                    
                    value_obj.save()
            
            # Then handle all other units
            for unit in valid_units:
                if unit not in ['Space_X', 'Space_Y']:
                    value_obj, created = DataCenterValue.objects.get_or_create(
                        unit=unit, 
                        defaults={'value': 0}
                    )
                    
                    old_value = value_obj.value
                    total = unit_totals[unit]
                    
                    # For other units, we just use the total
                    value_obj.value = total
                    logger.info(f"Unit {unit}: Updated to {total} (was {old_value})")
                    
                    value_obj.save()
        
        return DataCenterValue.objects.all()

class DataCenterSpecsService:
    """
    Service class for DataCenterSpecs-related operations.
    Provides methods to validate data center values against specifications.
    """
    
    @staticmethod
    def validate_current_values():
        """
        Validate that all current DataCenterValues meet the specifications.
        
        This method:
        1. Gets all DataCenterSpecs and DataCenterValues
        2. Checks each value against its specifications
        3. Logs any violations
        
        Validation rules:
        - below_amount=1: Current value must be <= spec amount
        - above_amount=1: Current value must be >= spec amount
        
        Returns:
            bool: True if all specs are met, False otherwise.
            
        Usage:
            is_valid = DataCenterSpecsService.validate_current_values()
            if is_valid:
                # All specifications are met
            else:
                # Some specifications are not met
        """
        logger.info("Validating data center specifications")
        
        # Get all specs
        all_specs = DataCenterSpecs.objects.all()
        
        # Get all current values in one query
        all_values = {value.unit: value.value for value in DataCenterValue.objects.all()}
        
        # Log current state for debugging
        logger.info(f"Found {len(all_specs)} specifications to validate")
        logger.info(f"Current values: {all_values}")
        
        # Track all violations
        violations = []
        
        # Check each spec against current values
        for spec in all_specs:
            unit = spec.unit
            current_value = all_values.get(unit, 0)
            
            # Log what we're checking
            logger.info(f"Validating {spec.name}: Unit: {unit}, Current Value: {current_value}, Spec Amount: {spec.amount}")
            
            # Check below constraint
            if spec.below_amount == 1 and current_value > spec.amount:
                violation_msg = f"Unit {unit} value ({current_value}) exceeds maximum allowed ({spec.amount})"
                logger.error(violation_msg)
                violations.append(violation_msg)
            
            # Check above constraint
            if spec.above_amount == 1 and current_value < spec.amount:
                violation_msg = f"Unit {unit} value ({current_value}) is below minimum required ({spec.amount})"
                logger.error(violation_msg)
                violations.append(violation_msg)
        
        # Log validation result
        if violations:
            logger.error(f"Validation failed with {len(violations)} violations")
            for violation in violations:
                logger.error(f"- {violation}")
            return False
        
        logger.info("All specifications validated successfully")
        return True

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
