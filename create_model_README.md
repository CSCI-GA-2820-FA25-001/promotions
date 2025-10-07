# promotion_model

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

This is a skeleton you can use to start your projects.

**Note:** _Feel free to overwrite this `README.md` file with the one that describes your project._

## Feature

- CRUD operations for Promotion entities
- Discounted price calculated at runtime
- Status transitions: draft → active → expired/deactivated | deleted
- Soft delete support
- Logging per module

## Tech Stack

- Python 3.11
- Flask
- SQLAlchemy
- MySQL 8.0 (Dockerized)
- Docker & Docker Compose
- Factory Boy (for testing)

## Manual Setup

1. **Clone the repository**

You can also clone this repository and then copy and paste the starter code into your project repo folder on your local computer. Be careful not to copy over your own `README.md` file so be selective in what you copy.

There are 4 hidden files that you will need to copy manually if you use the Mac Finder or Windows Explorer to copy files from this folder into your repo folder.

These should be copied using a bash shell as follows:

```bash
    cp .gitignore  ../<your_repo_folder>/
    cp .flaskenv ../<your_repo_folder>/
    cp .gitattributes ../<your_repo_folder>/
```

2. **Build and start services with Docker Compose**

```shell
cd .devcontainer
docker-compose up -d --build
```

3. **activate the container bash**

```shell
docker exec -it nyu-project bash #the container's name is nyu-project
```

4. **initialize the Database**

```bash
flask db migrate  
flask db upgrade   
```

5. **Run the Flask app**

```bash
gunicorn wsgi:app -b 0.0.0.0:8080 --reload
```




## Promotion Model Fields
- `product_name` (str): Name of the product
- `original_price` (Decimal): Original price of the product
- `discount_value` (Decimal, optional): Discount amount or percent
- `discount_type` (Enum, optional): 'amount' or 'percent'
- `promotion_type` (Enum): 'discount' or 'other'
- `start_date` (datetime, optional): Start of the promotion
- `expiration_date` (datetime): End of the promotion
- `status` (Enum): draft, active, expired, deactivated, deleted

## Promotion Methods

- `create()`: Adds the promotion to the database
- `update()`: Updates the promotion
- `delete()`: Deletes the promotion
- `serialize()`: Returns a dictionary representation
- `deserialize(data)`: Populates a Promotion from a dictionary
- `discounted_price`: Computes the final price after discount
- Class methods:
  - `all()`: Returns all promotions
  - `find(id)`: Find promotion by ID
  - `find_by_name(name)`: Find promotions by product name


## Testing
```shell
docker exec -it nyu-project bash #the container's name is nyu-project
pytest tests/test_models.py
```

The tests cover:

- Creating, updating, deleting promotions
- Validating data types
- Checking `discounted_price` calculation
- Handling `discount` and `other` promotion types
- Rollback behavior on database errors

## Contents

The project contains the following:

```text
.gitignore          - this will ignore vagrant and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to gix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
pyproject.toml      - Poetry list of Python libraries required by your code

service/                   - service python package
├── __init__.py            - package initializer
├── config.py              - configuration parameters
├── models.py              - module with business models
├── routes.py              - module with service routes
└── common                 - common code package
    ├── cli_commands.py    - Flask command to recreate all tables
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for business models
└── test_routes.py         - test suite for service routes
```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
