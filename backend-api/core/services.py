from .models import Module, ActiveModule, DataCenterSpecs, DataCenterValue, ModuleAttribute
from django.db.models import Sum
from django.db import transaction
import logging

logger = logging.getLogger('django')

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
        """
        Create a new active module without validation
        """
        try:
            module_id = data.pop('module').id if isinstance(data.get('module'), Module) else data.pop('module')
            module = Module.objects.get(id=module_id)
            
            for field in Module._meta.fields:
                logger.info(f"Module {field.name}: {getattr(module, field.name)}")
            
            # Create the active module
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
        """Delete an active module without recalculation"""
        try:
            active_module = ActiveModule.objects.get(id=active_module_id)
            logger.info(f"Deleting active module ID={active_module_id}, Module={active_module.module.name}, Unit={active_module.module.unit}")
            
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
    @staticmethod
    def get_or_create_value(unit):
        """Get or create a DataCenterValue for a specific unit"""
        value, created = DataCenterValue.objects.get_or_create(unit=unit, defaults={'value': 0})
        return value
    
    @staticmethod
    def initialize_values_from_specs():
        """
        Initialize DataCenterValue objects from unique units in DataCenterSpecs
        Sets initial values based on the constraints in the specs
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
            initial_values['Space_X'] = 3000  # Total available space in X dimension
        if 'Space_Y' in unique_units:
            initial_values['Space_Y'] = 2000  # Total available space in Y dimension
        
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
        """Recalculate all values based on active modules"""
        # Get all active modules
        active_modules = ActiveModule.objects.all().select_related('module')
        
        # Get all valid units from DataCenterSpecs
        valid_units = set(DataCenterSpecs.objects.values_list('unit', flat=True).distinct())
        logger.info(f"Valid units from DataCenterSpecs: {valid_units}")
        
        # Create a dictionary to store unit totals (initialize with 0 for all valid units)
        unit_totals = {unit: 0 for unit in valid_units}
        
        # Calculate totals for each unit from active modules
        for am in active_modules:
            # Get all attributes for this module
            attributes = ModuleAttribute.objects.filter(module=am.module)
            
            for attr in attributes:
                unit = attr.unit
                amount = attr.amount
                
                # Only update totals for units that are defined in DataCenterSpecs
                if unit in valid_units:
                    unit_totals[unit] += amount
                    logger.debug(f"Adding {amount} to total for {unit}, new total: {unit_totals[unit]}")
        
        logger.info(f"Calculated unit totals for valid units: {unit_totals}")
        
        # Ensure all DataCenterValue objects exist for valid units
        for unit in valid_units:
            # Get or create the DataCenterValue object
            value_obj, created = DataCenterValue.objects.get_or_create(
                unit=unit, 
                defaults={'value': 0}
            )
            
            old_value = value_obj.value
            total = unit_totals[unit]
            
            # For Space_X and Space_Y, we subtract from the initial value
            if unit in ['Space_X', 'Space_Y']:
                # Get the initial value
                initial_value = 3000 if unit == 'Space_X' else 2000
                value_obj.value = initial_value - total
                logger.info(f"Unit {unit}: {initial_value} - {total} = {value_obj.value} (was {old_value})")
            else:
                # For other units, we just use the total
                value_obj.value = total
                logger.info(f"Unit {unit}: Updated to {total} (was {old_value})")
                
            value_obj.save()

class DataCenterSpecsService:
    @staticmethod
    def validate_current_values():
        """
        Validate that all current DataCenterValues meet the specifications
        Returns True if all specs are met, False otherwise
        """
        logger.info("Validating data center specifications")
        
        # Get all specs
        all_specs = DataCenterSpecs.objects.all()
        logger.debug(f"Found {len(all_specs)} specifications to validate")
        
        # Track all violations to report them all
        violations = []
        
        # Check each spec against current values
        for spec in all_specs:
            # Get current value for this unit
            try:
                current_value = DataCenterValue.objects.get(unit=spec.unit).value
                logger.info(f"Unit: {spec.unit}, Current Value: {current_value}, Spec Amount: {spec.amount}")
                
                # Log constraint types with more detail
                constraint_type = []
                if spec.below_amount == 1:
                    constraint_type.append("below or equal")
                    logger.info(f"Constraint: Unit {spec.unit} should be BELOW OR EQUAL TO {spec.amount}")
                if spec.above_amount == 1:
                    constraint_type.append("above")
                    logger.info(f"Constraint: Unit {spec.unit} should be ABOVE {spec.amount}")
                if spec.minimize == 1:
                    constraint_type.append("minimize")
                    logger.info(f"Constraint: Unit {spec.unit} should be MINIMIZED")
                if spec.maximize == 1:
                    constraint_type.append("maximize")
                    logger.info(f"Constraint: Unit {spec.unit} should be MAXIMIZED")
                if spec.unconstrained == 1:
                    constraint_type.append("unconstrained")
                    logger.info(f"Constraint: Unit {spec.unit} is UNCONSTRAINED")
                
                logger.debug(f"Unit {spec.unit} has constraints: {', '.join(constraint_type)}")
                
            except DataCenterValue.DoesNotExist:
                current_value = 0 if spec.unit not in ['Space_X', 'Space_Y'] else spec.amount
                logger.info(f"No value found for unit {spec.unit}, using default: {current_value}")
                
            # Check constraints based on spec type with detailed logging
            if spec.below_amount == 1:
                logger.debug(f"Checking if {current_value} <= {spec.amount} for {spec.unit}")
                if current_value > spec.amount:
                    # Value should be below or equal to amount but isn't
                    violation_msg = f"VALIDATION FAILED: Unit {spec.unit} value ({current_value}) exceeds maximum allowed ({spec.amount})"
                    logger.error(violation_msg)
                    logger.error(f"Difference: {current_value - spec.amount} over limit")
                    violations.append(violation_msg)
                else:
                    logger.debug(f"PASSED: {spec.unit} value {current_value} is below or equal to limit {spec.amount}")
            
            if spec.above_amount == 1:
                logger.debug(f"Checking if {current_value} >= {spec.amount} for {spec.unit}")
                if current_value < spec.amount:
                    # Value should be above amount but isn't
                    violation_msg = f"VALIDATION FAILED: Unit {spec.unit} value ({current_value}) is below minimum required ({spec.amount})"
                    logger.error(violation_msg)
                    logger.error(f"Difference: {spec.amount - current_value} below requirement")
                    violations.append(violation_msg)
                else:
                    logger.debug(f"PASSED: {spec.unit} value {current_value} is above minimum {spec.amount}")
        
        if violations:
            logger.error(f"Validation failed with {len(violations)} violations: {'; '.join(violations)}")
            return False
        
        logger.info("All specifications validated successfully")
        return True

class ModuleCalculationService:
    @staticmethod
    def calculate_resource_usage(active_modules=None):
        """
        Calculate total resource usage based on active modules
        """
        if active_modules is None:
            active_modules = ActiveModule.objects.all().select_related('module')
            
        # Group by unit and sum amounts
        unit_totals = {}
        for am in active_modules:
            # Get all attributes for this module
            attributes = ModuleAttribute.objects.filter(module=am.module)
            
            for attr in attributes:
                unit = attr.unit
                amount = attr.amount
                
                if unit in unit_totals:
                    unit_totals[unit] += amount
                else:
                    unit_totals[unit] = amount
                    
        # Add all DataCenterValues to the result
        all_values = {value.unit: value.value for value in DataCenterValue.objects.all()}
        
        # Combine the dictionaries
        return {**unit_totals, **all_values}
