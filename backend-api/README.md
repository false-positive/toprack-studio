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

### Usage workflow:

- Get available modules: `GET /api/modules/`
- Choose modules and place in the data center by activating them: `POST /api/active-modules/`
- Calculate resource usage: `GET /api/calculate-resources/`
  - This will just add them to the db, but won't fact check anything and won't place them on the datacenter.
- Validate constraints: `GET /api/recalculate-values/`
  - This will place them on the datacenter and do checks.

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
        "is_input": true,
        "is_output": false,
        "attributes": {
          "Grid_Connection": 1,
          "Space_X": 40,
          "Space_Y": 45,
          "Price": 1000,
          "Usable_Power": 100
        }
      },
      ...
    ]
    ```

### Active Modules

- `POST /api/active-modules/` - Place a module at specific coordinates

  - Required data:
    ```json
    {
      "x": 10,
      "y": 20,
      "module": 1 // ID of an existing module
    }
    ```
  - Returns: Created active module details

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

### Validation

- GET /api/calculate-resources/
  Logic: Calculates total resource usage based on all active modules
  Service: Calls ModuleCalculationService.calculate_resource_usage(active_modules)
  Process:
  Gets all active modules
  Calculates total resource usage for each unit (Space_X, Space_Y, Price, etc.)
  Response: Returns calculated totals for each resource type
  Use case: Shows the user current resource consumption
- `POST /api/recalculate-values/` - Recalculate all data center values and validate

  - Returns: Recalculation status and validation result
  - Example response:
    ```json
    {
      "status": "success",
      "status_code": 200,
      "message": "Values recalculated successfully",
      "validation_passed": true
    }
    ```

- `GET /api/validate-values/` - Validate current data center values against specifications

  - **You don't need to call this probably, recalculate-values calls it internally.**

  - Returns: Validation status, specifications, and current values
  - Example success response:
    ```json
    {
      "status": "All specifications validated successfully",
      "specs": [
        {
          "name": "Server_Square",
          "unit": "Space_X",
          "amount": 1000,
          "constraints": ["below 1000"]
        },
        {
          "name": "Server_Square",
          "unit": "Space_Y",
          "amount": 500,
          "constraints": ["below 500"]
        },
        {
          "name": "Dense_Storage",
          "unit": "Data_Storage",
          "amount": 1000,
          "constraints": ["above 1000"]
        }
      ],
      "current_values": {
        "Space_X": 850,
        "Space_Y": 400,
        "Data_Storage": 1200,
        "Price": 50000
      }
    }
    ```
  - Example failure response:
    ```json
    {
      "status": "Validation failed, see logs for details",
      "specs": [
        {
          "name": "Server_Square",
          "unit": "Space_X",
          "amount": 1000,
          "constraints": ["below 1000"]
        },
        {
          "name": "Server_Square",
          "unit": "Space_Y",
          "amount": 500,
          "constraints": ["below 500"]
        },
        {
          "name": "Dense_Storage",
          "unit": "Data_Storage",
          "amount": 1000,
          "constraints": ["above 1000"]
        }
      ],
      "current_values": {
        "Space_X": -50,
        "Space_Y": 400,
        "Data_Storage": 800,
        "Price": 50000
      }
    }
    ```
  - Status code: 200 OK for success, 400 Bad Request for validation failures
