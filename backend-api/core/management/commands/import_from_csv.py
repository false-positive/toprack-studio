from django.core.management.base import BaseCommand
from core.models import Module, DataCenterSpecs
import csv
import io

class Command(BaseCommand):
    help = 'Import Modules and DataCenterSpecs from CSV files with auto delimiter detection'

    def handle(self, *args, **kwargs):
        self.import_modules("Modules.csv")
        self.import_specs("Data_Center_Spec.csv")

    def detect_delimiter_and_read(self, file_obj):
        """
        Detect whether delimiter is semicolon or tab, return a csv.DictReader.
        """
        sample = file_obj.read().decode('utf-8-sig')
        file_obj.seek(0)

        header_line = sample.splitlines()[0]
        delimiter = ';' if header_line.count(';') > header_line.count('\t') else '\t'

        return csv.DictReader(io.StringIO(sample), delimiter=delimiter)

    def import_modules(self, path):
        try:
            with open(path, 'rb') as f:
                reader = self.detect_delimiter_and_read(f)

                for row in reader:
                    Module.objects.create(
                        name=row['Name'],
                        is_input=bool(int(row['Is_Input'])),
                        is_output=bool(int(row['Is_Output'])),
                        unit=row['Unit'],
                        amount=int(row['Amount'])
                    )

                self.stdout.write(self.style.SUCCESS(f"Imported Modules from {path}"))
        except Exception as e:
            self.stderr.write(f"Failed to import Modules: {e}")

    def import_specs(self, path):
        try:
            with open(path, 'rb') as f:
                reader = self.detect_delimiter_and_read(f)

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

                self.stdout.write(self.style.SUCCESS(f"Imported DataCenterSpecs from {path}"))
        except Exception as e:
            self.stderr.write(f"Failed to import DataCenterSpecs: {e}")
