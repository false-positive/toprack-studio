## Development Setup

### Dependencies

This project uses `uv` for Python dependency management. To set up the project:

1. Install dependencies:

   ```
   uv sync
   ```

2. Run the development server:

   ```
   uv run python manage.py runserver
   ```

3. Import initial data (optional):

   ```
   uv run python manage.py import_from_csv --init-values
   ```

## Data Models

The backend is built around these core data models:

- **Module**: Base building blocks (transformers, servers, storage units, etc.)

  - Has attributes (inputs/outputs like power, storage, processing)

- **ActiveModule**: Placed modules in the data center

  - References a Module
  - Has x,y coordinates
  - Belongs to a DataCenterComponent

- **DataCenterComponent**: Logical sections of the data center (Server_Square, Dense_Storage, etc.)

  - Has constraints/specifications

- **DataCenterComponentAttribute**: Constraints for components

  - below_amount: Must be below this value
  - above_amount: Must be above this value
  - minimize/maximize: Optimization goals

- **DataCenterValue**: Current values for each unit in each component
  - Tracks current totals (Space_X, Space_Y, Data_Storage, etc.)

## API Workflow

The typical workflow for using this API is:

1. Initialize values from component specifications
2. List available modules and components
3. Place modules in components at specific coordinates
4. Recalculate values based on placed modules
5. Validate that all constraints are met
6. Adjust module placement as needed
7. Recalculate and validate again

## API Endpoints

The backend API provides the following endpoints:

### Modules

- `GET /api/modules/` - List all available modules

  - Returns: List of all modules with their properties and attributes
  - Example response:
    ```json
    [
      {
        "id": 1,
        "name": "Transformer_100",
        "attributes": [
          {
            "unit": "Grid_Connection",
            "amount": 1,
            "is_input": true,
            "is_output": false
          },
          {
            "unit": "Space_X",
            "amount": 40,
            "is_input": false,
            "is_output": false
          },
          {
            "unit": "Space_Y",
            "amount": 45,
            "is_input": false,
            "is_output": false
          },
          {
            "unit": "Price",
            "amount": 1000,
            "is_input": false,
            "is_output": false
          },
          {
            "unit": "Usable_Power",
            "amount": 100,
            "is_input": false,
            "is_output": true
          }
        ]
      }
    ]
    ```

### Data Center Components

- `GET /api/datacenter-components/` - List all data center components

  - Returns: List of all components with their constraints
  - Example response:
    ```json
    [
      {
        "id": 1,
        "name": "Server_Square",
        "attributes": [
          {
            "unit": "Space_X",
            "amount": 1000,
            "below_amount": 1,
            "above_amount": 0,
            "minimize": 0,
            "maximize": 0,
            "unconstrained": 0
          },
          {
            "unit": "Space_Y",
            "amount": 500,
            "below_amount": 1,
            "above_amount": 0,
            "minimize": 0,
            "maximize": 0,
            "unconstrained": 0
          },
          {
            "unit": "Data_Storage",
            "amount": 1000,
            "below_amount": 0,
            "above_amount": 1,
            "minimize": 0,
            "maximize": 0,
            "unconstrained": 0
          }
        ]
      }
    ]
    ```

### Active Modules

- `POST /api/active-modules/` - Place a module at specific coordinates

  - Required data:
    ```json
    {
      "x": 10,
      "y": 20,
      "module": 1,
      "data_center_component": 1
    }
    ```
  - Returns: Created active module details

- `GET /api/active-modules/` - List all placed modules

  - Returns: List of all active modules with their positions and related data

- `DELETE /api/active-modules/{id}/` - Remove a placed module

  - Returns: Success/failure status

### Data Center Points

- `POST /api/datacenter-points/` - Add a data center point at specific coordinates

  - Required data:
    ```json
    {
      "x": 100,
      "y": 200
    }
    ```
  - Returns: Created data center point details

### Calculation and Validation

- `GET /api/calculate-resources/` - Calculate total resource usage

  - Returns: Calculated totals for each resource type
  - Does not update database values
  - Example response:
    ```json
    {
      "status": "success",
      "status_code": 200,
      "message": "Resources calculated successfully",
      "data": {
        "Space_X": 850,
        "Space_Y": 400,
        "Data_Storage": 1200,
        "Price": 50000
      }
    }
    ```

- `POST /api/recalculate-values/` - Recalculate all data center values and validate

  - Updates DataCenterValue objects based on placed modules
  - Validates updated values against constraints
  - Returns: Recalculation status and validation result
  - Example response:
    ```json
    {
      "status": "success",
      "status_code": 200,
      "message": "Values recalculated successfully",
      "validation_passed": true,
      "violations": []
    }
    ```

- `GET /api/validate-component-values/` - Validate current data center values

  - Returns: Validation status, specifications, and current values
  - Example success response:
    ```json
    {
      "status": "success",
      "status_code": 200,
      "message": "All specifications validated successfully",
      "components": [
        {
          "id": 1,
          "name": "Server_Square",
          "attributes": [
            {
              "unit": "Space_X",
              "amount": 1000,
              "below_amount": 1,
              "above_amount": 0
            }
          ]
        }
      ],
      "current_values": {
        "Server_Square": {
          "Space_X": 850,
          "Space_Y": 400,
          "Data_Storage": 1200
        }
      }
    }
    ```

- `GET /api/validate-component-values/{component_id}/` - Validate specific component

  - Returns: Validation status for the specified component only

### Initialization

- `POST /api/initialize-values-from-components/` - Initialize values from components

  - Creates DataCenterValue objects based on component specifications
  - Returns: Initialization status and count of created values
  - Example response:
    ```json
    {
      "status": "success",
      "status_code": 200,
      "message": "Values initialized successfully from components",
      "count": 12
    }
    ```

## Constraint Types

The system supports several types of constraints:

1. **Below Amount**: Value must be below threshold (e.g., Space_X < 1000)
2. **Above Amount**: Value must be above threshold (e.g., Data_Storage > 1000)
3. **Minimize**: Try to minimize this value (optimization goal)
4. **Maximize**: Try to maximize this value (optimization goal)
5. **Unconstrained**: No specific constraint on this value

## Special Units

The system tracks several types of units:

1. **Space_X/Space_Y**: Represent available space (decreases as modules are added)
2. **Price**: Total cost (increases as modules are added)
3. **Data_Storage/Processing**: Capacity (increases as modules are added)
4. **Grid_Connection/Water_Connection**: Resource connections (must meet minimum requirements)
