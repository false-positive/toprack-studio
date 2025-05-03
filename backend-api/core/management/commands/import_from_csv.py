from django.core.management.base import BaseCommand
from core.models import Module, DataCenterSpecs, ModuleAttribute
import csv
import io
from django.db import transaction

class Command(BaseCommand):
    help = 'Import Modules and DataCenterSpecs from CSV files with auto delimiter detection'

    def add_arguments(self, parser):
        parser.add_argument('--no-clean', action='store_true', help='Do not clean database before import')

    def handle(self, *args, **kwargs):
        clean_db = not kwargs.get('no_clean', False)
        
        if clean_db:
            self.stdout.write("Cleaning database before import...")
            self.clean_database()
        
        self.import_modules("Modules.csv")
        self.import_specs("Data_Center_Spec.csv")

    def clean_database(self):
        """Clean relevant database tables before import"""
        try:
            self.stdout.write("Deleting all ModuleAttribute records...")
            ModuleAttribute.objects.all().delete()
            
            self.stdout.write("Deleting all Module records...")
            Module.objects.all().delete()
            
            self.stdout.write("Deleting all DataCenterSpecs records...")
            DataCenterSpecs.objects.all().delete()
            
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
                
                # Group rows by ID to handle multiple attributes per module
                modules_by_id = {}
                for row in reader:
                    module_id = int(row['ID'])
                    if module_id not in modules_by_id:
                        modules_by_id[module_id] = {
                            'name': row['Name'],
                            'is_input': bool(int(row['Is_Input'])),
                            'is_output': bool(int(row['Is_Output'])),
                            'attributes': []
                        }
                    
                    # Add this attribute to the module
                    modules_by_id[module_id]['attributes'].append({
                        'unit': row['Unit'],
                        'amount': int(row['Amount'])
                    })
                
                # Create modules and their attributes
                for module_id, module_data in modules_by_id.items():
                    # Create the module
                    module = Module.objects.create(
                        name=module_data['name'],
                        is_input=module_data['is_input'],
                        is_output=module_data['is_output']
                    )
                    
                    # Create all attributes for this module
                    for attr in module_data['attributes']:
                        ModuleAttribute.objects.create(
                            module=module,
                            unit=attr['unit'],
                            amount=attr['amount']
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
