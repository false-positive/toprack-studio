## API Endpoints

The backend API provides the following endpoints:

### Modules

- `GET /api/modules/` - List all available modules

  - Returns: List of all modules with their properties (name, is_input, is_output, unit, amount)

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
