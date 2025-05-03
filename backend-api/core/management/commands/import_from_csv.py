from django.core.management.base import BaseCommand
from core.models import Module, ModuleAttribute, DataCenterValue, DataCenterComponent, DataCenterComponentAttribute
import csv
import io
from django.db import transaction
import logging
from backend.settings import DataCenterConstants

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import Modules and DataCenterComponents from CSV files with auto delimiter detection'

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
        self.import_components("Data_Center_Spec.csv")
        
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
            
            self.stdout.write("Deleting all DataCenterComponentAttribute records...")
            DataCenterComponentAttribute.objects.all().delete()
            
            self.stdout.write("Deleting all DataCenterComponent records...")
            DataCenterComponent.objects.all().delete()
            
            self.stdout.write("Deleting all DataCenterValue records...")
            DataCenterValue.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS("Database cleaned successfully"))
        except Exception as e:
            self.stderr.write(f"Error cleaning database: {e}")

    def detect_delimiter_and_read(self, file_obj):
        """Detect delimiter in CSV file and return a DictReader"""
        # Read a sample of the file to detect the delimiter
        sample = file_obj.read(4096)
        
        # Try to decode the sample
        try:
            sample_text = sample.decode('utf-8')
        except UnicodeDecodeError:
            # If UTF-8 fails, try another common encoding
            sample_text = sample.decode('latin-1')
        
        # Count occurrences of common delimiters
        delimiters = [',', ';', '\t', '|']
        counts = {d: sample_text.count(d) for d in delimiters}
        
        # Choose the delimiter with the highest count
        delimiter = max(counts.items(), key=lambda x: x[1])[0]
        
        # Reset file pointer to the beginning
        file_obj.seek(0)
        
        # Try to decode the entire file
        try:
            text = file_obj.read().decode('utf-8')
        except UnicodeDecodeError:
            # If UTF-8 fails, try another common encoding
            file_obj.seek(0)
            text = file_obj.read().decode('latin-1')
        
        # Create a CSV reader with the detected delimiter
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        
        self.stdout.write(f"Detected delimiter: '{delimiter}'")
        return reader

    @transaction.atomic
    def import_modules(self, path):
        try:
            with open(path, 'rb') as f:
                reader = self.detect_delimiter_and_read(f)
                
                # Create a dictionary to store modules
                modules = {}
                
                # First pass: Create all modules
                for row in reader:
                    module_name = row['Name']
                    
                    # Create module if it doesn't exist
                    if module_name not in modules:
                        module, created = Module.objects.get_or_create(name=module_name)
                        modules[module_name] = module
                        
                        if created:
                            self.stdout.write(f"Created module: {module_name}")
                
                # Reset file and reader for second pass
                f.seek(0)
                reader = self.detect_delimiter_and_read(f)
                
                # Second pass: Create all module attributes
                count = 0
                for row in reader:
                    module_name = row['Name']
                    module = modules[module_name]
                    
                    # Create module attribute
                    ModuleAttribute.objects.create(
                        module=module,
                        unit=row['Unit'],
                        amount=int(row['Amount']),
                        is_input=int(row['Is_Input']) == 1,
                        is_output=int(row['Is_Output']) == 1
                    )
                    count += 1
                
                self.stdout.write(self.style.SUCCESS(f"Imported {len(modules)} modules with {count} attributes from {path}"))
        except Exception as e:
            self.stderr.write(f"Failed to import modules: {e}")
            raise

    @transaction.atomic
    def import_components(self, path):
        try:
            with open(path, 'rb') as f:
                reader = self.detect_delimiter_and_read(f)

                # Create a dictionary to store components
                components = {}
                
                # First pass: Create all components
                for row in reader:
                    component_name = row['Name']
                    
                    # Create component if it doesn't exist
                    if component_name not in components:
                        component, created = DataCenterComponent.objects.get_or_create(name=component_name)
                        components[component_name] = component
                        
                        if created:
                            self.stdout.write(f"Created component: {component_name}")
                
                # Reset file and reader for second pass
                f.seek(0)
                reader = self.detect_delimiter_and_read(f)
                
                # Second pass: Create all component attributes
                count = 0
                for row in reader:
                    component_name = row['Name']
                    component = components[component_name]
                    
                    # Create component attribute
                    DataCenterComponentAttribute.objects.create(
                        component=component,
                        unit=row['Unit'],
                        amount=int(row['Amount']),
                        below_amount=int(row['Below_Amount']),
                        above_amount=int(row['Above_Amount']),
                        minimize=int(row['Minimize']),
                        maximize=int(row['Maximize']),
                        unconstrained=int(row['Unconstrained'])
                    )
                    count += 1

                self.stdout.write(self.style.SUCCESS(f"Imported {len(components)} components with {count} attributes from {path}"))
        except Exception as e:
            self.stderr.write(f"Failed to import components: {e}")
            raise

    @transaction.atomic
    def initialize_values(self):
        """Initialize DataCenterValue objects from DataCenterComponentAttributes"""
        try:
            from core.services import DataCenterValueService
            from core.models import DataCenter
            
            # Get or create the default data center
            data_center = DataCenter.get_default()
            
            # Initialize values with the data center
            values = DataCenterValueService.initialize_values_from_components(data_center)
            
            self.stdout.write(self.style.SUCCESS(f"Initialized {len(values)} DataCenterValues for {data_center.name}"))
        except Exception as e:
            self.stderr.write(f"Failed to initialize values: {e}")
            raise
