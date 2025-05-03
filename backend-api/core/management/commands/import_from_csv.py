from django.core.management.base import BaseCommand
from core.models import Module, ModuleAttribute, DataCenterValue, DataCenterComponent, DataCenterComponentAttribute
import csv
import io
from django.db import transaction
import logging
from backend.settings import DataCenterConstants
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import Modules and DataCenterComponents from CSV files with auto delimiter detection'

    def add_arguments(self, parser):
        parser.add_argument('--no-clean', action='store_true', help='Do not clean database before import')
        parser.add_argument('--init-values', action='store_true', help='Initialize DataCenterValues after import')
        parser.add_argument('--modules-csv', type=str, default="Modules.csv", help='CSV file containing modules data')
        parser.add_argument('--components-csv', type=str, default="Data_Center_Spec.csv", help='CSV file containing data center components')
        parser.add_argument('--data-center-name', type=str, default="Default Data Center", help='Name for the data center')

    def handle(self, *args, **kwargs):
        clean_db = not kwargs.get('no_clean', False)
        init_values = kwargs.get('init_values', False)
        modules_csv = kwargs.get('modules_csv', "Modules.csv")
        components_csv = kwargs.get('components_csv', "Data_Center_Spec.csv")
        data_center_name = kwargs.get('data_center_name', "Default Data Center")
        
        if clean_db:
            self.stdout.write("Cleaning database before import...")
            self.clean_database()
        
        self.import_modules(modules_csv)
        self.import_components(components_csv)
        
        if init_values:
            self.stdout.write("Initializing DataCenterValues...")
            self.initialize_values(data_center_name)

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
        sample = file_obj.read(4096)
        
        try:
            sample_text = sample.decode('utf-8')
        except UnicodeDecodeError:
            sample_text = sample.decode('latin-1')
        
        delimiters = [',', ';', '\t', '|']
        counts = {d: sample_text.count(d) for d in delimiters}
        
        delimiter = max(counts.items(), key=lambda x: x[1])[0]
        
        file_obj.seek(0)
        
        try:
            text = file_obj.read().decode('utf-8')
        except UnicodeDecodeError:
            file_obj.seek(0)
            text = file_obj.read().decode('latin-1')
        
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        
        self.stdout.write(f"Detected delimiter: '{delimiter}'")
        return reader

    @transaction.atomic
    def import_modules(self, path):
        try:
            self.stdout.write(f"Attempting to open modules file: {path}")
            self.stdout.write(f"Current working directory: {os.getcwd()}")
            self.stdout.write(f"File exists: {os.path.exists(path)}")
            self.stdout.write(f"Absolute path: {os.path.abspath(path)}")
            
            with open(path, 'rb') as f:
                reader = self.detect_delimiter_and_read(f)
                
                modules = {}
                
                for row in reader:
                    module_name = row['Name']
                    if module_name not in modules:
                        module, created = Module.objects.get_or_create(name=module_name)
                        modules[module_name] = module
                        
                        if created:
                            self.stdout.write(f"Created module: {module_name}")
                
                f.seek(0)
                reader = self.detect_delimiter_and_read(f)
                
                count = 0
                for row in reader:
                    module_name = row['Name']
                    module = modules[module_name]
                    
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
            self.stdout.write(f"Attempting to open components file: {path}")
            self.stdout.write(f"Current working directory: {os.getcwd()}")
            self.stdout.write(f"File exists: {os.path.exists(path)}")
            self.stdout.write(f"Absolute path: {os.path.abspath(path)}")
            
            with open(path, 'rb') as f:
                reader = self.detect_delimiter_and_read(f)

                components = {}
                
                for row in reader:
                    component_name = row['Name']
                    
                    if component_name not in components:
                        component, created = DataCenterComponent.objects.get_or_create(name=component_name)
                        components[component_name] = component
                        
                        if created:
                            self.stdout.write(f"Created component: {component_name}")
                
                f.seek(0)
                reader = self.detect_delimiter_and_read(f)
                
                count = 0
                for row in reader:
                    component_name = row['Name']
                    component = components[component_name]
                    
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
    def initialize_values(self, data_center_name="Default Data Center"):
        """Initialize DataCenterValue objects from DataCenterComponentAttributes"""
        try:
            from core.services import DataCenterValueService
            from core.models import DataCenter
        
            data_center, created = DataCenter.objects.get_or_create(
                name=data_center_name,
                defaults={
                    'space_x': DataCenterConstants.SPACE_X_INITIAL,
                    'space_y': DataCenterConstants.SPACE_Y_INITIAL
                }
            )
        
            if created:
                from core.models import Point
                points = [
                    Point.objects.get_or_create(x=0, y=0)[0],
                    Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=0)[0],
                    Point.objects.get_or_create(x=DataCenterConstants.SPACE_X_INITIAL, y=DataCenterConstants.SPACE_Y_INITIAL)[0],
                    Point.objects.get_or_create(x=0, y=DataCenterConstants.SPACE_Y_INITIAL)[0]
                ]
                data_center.points.add(*points)
                self.stdout.write(f"Created new data center: {data_center_name}")
        
            values = DataCenterValueService.initialize_values_from_components(data_center)
        
            self.stdout.write(self.style.SUCCESS(f"Initialized {len(values)} DataCenterValues for {data_center.name}"))
        except Exception as e:
            self.stderr.write(f"Failed to initialize values: {e}")
            raise
