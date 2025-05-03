from django.core.management.base import BaseCommand
from core.models import Module, DataCenterSpecs, ModuleAttribute, DataCenterValue
import csv
import io
from django.db import transaction
import logging
from backend.settings import DataCenterConstants

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import Modules and DataCenterSpecs from CSV files with auto delimiter detection'

    def add_arguments(self, parser):
        parser.add_argument('--no-clean', action='store_true', help='Do not clean database before import')
        parser.add_argument('--init-values', action='store_true', help='Initialize DataCenterValues after import')

    def handle(self, *args, **kwargs):
        clean_db = not kwargs.get('no_clean', False)
        init_values = kwargs.get('init_values', False)
        
        if clean_db:
            self.stdout.write("Cleaning database before import...")
            self.clean_database()
        
        self.import_modules("Modules.csv")
        self.import_specs("Data_Center_Spec.csv")
        
        if init_values:
            self.stdout.write("Initializing DataCenterValues...")
            self.initialize_values()

    def clean_database(self):
        """Clean relevant database tables before import"""
        try:
            self.stdout.write("Deleting all ModuleAttribute records...")
            ModuleAttribute.objects.all().delete()
            
            self.stdout.write("Deleting all Module records...")
            Module.objects.all().delete()
            
            self.stdout.write("Deleting all DataCenterSpecs records...")
            DataCenterSpecs.objects.all().delete()
            
            self.stdout.write("Deleting all DataCenterValue records...")
            DataCenterValue.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS("Database cleaned successfully"))
        except Exception as e:
            self.stderr.write(f"Error cleaning database: {e}")

    def detect_delimiter_and_read(self, file_obj):
        """
        Detect whether delimiter is semicolon or tab, return a csv.DictReader.
        """
        sample = file_obj.read().decode('utf-8-sig')
        file_obj.seek(0)

        header_line = sample.splitlines()[0]
        delimiter = ';' if header_line.count(';') > header_line.count('\t') else '\t'

        return csv.DictReader(io.StringIO(sample), delimiter=delimiter)

    @transaction.atomic
    def import_modules(self, path):
        try:
            with open(path, 'rb') as f:
                reader = self.detect_delimiter_and_read(f)
                
                modules_by_id = {}
                for row in reader:
                    module_id = int(row['ID'])
                    if module_id not in modules_by_id:
                        modules_by_id[module_id] = {
                            'name': row['Name'],
                            'attributes': []
                        }
                    
                    modules_by_id[module_id]['attributes'].append({
                        'unit': row['Unit'],
                        'amount': int(row['Amount']),
                        'is_input': bool(int(row['Is_Input'])),
                        'is_output': bool(int(row['Is_Output']))
                    })
                
                # Create modules and their attributes
                for module_id, module_data in modules_by_id.items():
                    # Create the module
                    module = Module.objects.create(
                        name=module_data['name']
                    )
                    
                    # Create all attributes for this module
                    for attr in module_data['attributes']:
                        ModuleAttribute.objects.create(
                            module=module,
                            unit=attr['unit'],
                            amount=attr['amount'],
                            is_input=attr['is_input'],
                            is_output=attr['is_output']
                        )
                    
                    self.stdout.write(f"Created module {module.name} with {len(module_data['attributes'])} attributes")

                self.stdout.write(self.style.SUCCESS(f"Imported {len(modules_by_id)} modules from {path}"))
        except Exception as e:
            self.stderr.write(f"Failed to import Modules: {e}")
            raise

    @transaction.atomic
    def import_specs(self, path):
        try:
            with open(path, 'rb') as f:
                reader = self.detect_delimiter_and_read(f)

                count = 0
                for row in reader:
                    DataCenterSpecs.objects.create(
                        name=row['Name'],
                        below_amount=int(row['Below_Amount']),
                        above_amount=int(row['Above_Amount']),
                        minimize=int(row['Minimize']),
                        maximize=int(row['Maximize']),
                        unconstrained=int(row['Unconstrained']),
                        unit=row['Unit'],
                        amount=int(row['Amount'])
                    )
                    count += 1

                self.stdout.write(self.style.SUCCESS(f"Imported {count} DataCenterSpecs from {path}"))
        except Exception as e:
            self.stderr.write(f"Failed to import DataCenterSpecs: {e}")
            raise

    @transaction.atomic
    def initialize_values(self):
        """Initialize DataCenterValue objects from DataCenterSpecs"""
        try:
            # Get unique units from DataCenterSpecs
            unique_units = set(DataCenterSpecs.objects.values_list('unit', flat=True).distinct())
            self.stdout.write(f"Found {len(unique_units)} unique units in specs")
            
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
                value_obj, created = DataCenterValue.objects.get_or_create(
                    unit=unit,
                    defaults={'value': value}
                )
                
                if not created:
                    value_obj.value = value
                    value_obj.save()
                
                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} DataCenterValue for {unit}: {value}")
            
            self.stdout.write(self.style.SUCCESS(f"Initialized {len(initial_values)} DataCenterValues"))
            
            return DataCenterValue.objects.all()
        except Exception as e:
            self.stderr.write(f"Failed to initialize DataCenterValues: {e}")
            raise
