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
