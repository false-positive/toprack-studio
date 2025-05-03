#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import DataCenterSpecs, DataCenterValue, ActiveModule, ModuleAttribute

def show_specs():
    """Display all DataCenterSpecs"""
    specs = DataCenterSpecs.objects.all()
    print(f"\n=== DATA CENTER SPECIFICATIONS ({len(specs)}) ===")
    
    # Group specs by unit
    specs_by_unit = {}
    for spec in specs:
        if spec.unit not in specs_by_unit:
            specs_by_unit[spec.unit] = []
        specs_by_unit[spec.unit].append(spec)
    
    for unit, unit_specs in specs_by_unit.items():
        print(f"\nUnit: {unit}")
        for spec in unit_specs:
            constraints = []
            if spec.below_amount == 1:
                constraints.append(f"below {spec.amount}")
            if spec.above_amount == 1:
                constraints.append(f"above {spec.amount}")
            if spec.minimize == 1:
                constraints.append("minimize")
            if spec.maximize == 1:
                constraints.append("maximize")
            if spec.unconstrained == 1:
                constraints.append("unconstrained")
                
            print(f"  - {spec.name}: {', '.join(constraints)}")

def show_values():
    """Display all DataCenterValues"""
    values = DataCenterValue.objects.all()
    print(f"\n=== CURRENT DATA CENTER VALUES ({len(values)}) ===")
    for value in values:
        print(f"  {value.unit}: {value.value}")

def show_active_modules():
    """Display all active modules and their attributes"""
    active_modules = ActiveModule.objects.all().select_related('module')
    print(f"\n=== ACTIVE MODULES ({len(active_modules)}) ===")
    
    for am in active_modules:
        print(f"\n{am.module.name} at ({am.x}, {am.y})")
        attributes = ModuleAttribute.objects.filter(module=am.module)
        for attr in attributes:
            print(f"  {attr.unit}: {attr.amount}")

if __name__ == "__main__":
    show_specs()
    show_values()
    show_active_modules()