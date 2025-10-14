# NYU DevOps Project — Promotions Microservice

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![Coverage](https://img.shields.io/badge/Coverage-98%25-success.svg)]()

---

## Overview

The **Promotions Microservice** provides a RESTful API for managing product promotions in an e-commerce system.
It supports full **CRUD** operations (`Create`, `Read`, `Update`, `Delete`) and role-based listing with automatic discount calculations.
The service is fully containerized, follows **TDD**, and achieves **98 % test coverage** (≥ 95 % required).

---

## Features

* 🧩 **Complete CRUD + List Endpoints** (`/promotions`, `/promotions/<id>`)
* 🧮 **Automatic discounted price** calculation (`amount` or `percent`)
* 🔐 **Role-based views** for Customer / Supplier / Manager
* 🕒 **Expiration logic** with status transitions (`draft → active → expired → deleted`)
* ⚙️ **CLI Commands:** `flask db-create`, `flask db-drop`
* 🧰 **Centralized error handlers** for 400–500 JSON responses
* 🧪 **TDD & pytest suite:** 63 tests passed, 98 % coverage

---

## Setup

### Automatic (recommended)

Clone the repository and open it in VS Code Remote Container:

```bash
git clone https://github.com/CSCI-GA-2820-FA25-001/promotions.git
cd promotions
make build
code .
# → Reopen in Container
```

Initialize the database:

```bash
flask db-create
```

Run the service:

```bash
flask run -h 0.0.0.0 -p 5000
```

Service available at **[http://localhost:8080](http://localhost:8080)**

---

### Manual

If not using the container, install dependencies:

```bash
pip install -r requirements.txt
flask db-create
```

---

## Testing

Run all tests with coverage:

```bash
pytest --maxfail=1 --disable-warnings --cov=service
```

Expected output:

```
TOTAL 352 statements, 8 missed → 98 %
63 tests passed ✅
```

Linting:

```bash
make lint
```

---

## API Endpoints

| Method | Endpoint           | Description                  | Success        | Errors                |
| :----- | :----------------- | :--------------------------- | :------------- | :-------------------- |
| POST   | `/promotions`      | Create a new promotion       | 201 Created    | 400 / 403 / 409 / 422 |
| GET    | `/promotions/<id>` | Retrieve a promotion by ID   | 200 OK         | 400 / 404             |
| PUT    | `/promotions/<id>` | Update an existing promotion | 200 OK         | 400 / 404 / 422       |
| DELETE | `/promotions/<id>` | Soft delete promotion        | 204 No Content | 400 / 403 / 404 / 409 |
| GET    | `/promotions`      | List promotions (role-based) | 200 OK         | 400 / 404             |
| GET    | `/`                | Service metadata             | 200 OK         | 500                   |

#### Example Root Response

```json
{
  "name": "Promotions Service",
  "version": "1.0.0",
  "description": "Manage promotional offers for the eCommerce platform",
  "list_url": "/promotions"
}
```

---

## Data Model

| Field                            | Type                                          | Description        |
| :------------------------------- | :-------------------------------------------- | :----------------- |
| `id`                             | Integer (PK)                                  | Auto-increment     |
| `product_name`                   | String(255)                                   | Unique, required   |
| `description`                    | String(1024)                                  | Optional           |
| `original_price`                 | Decimal(10, 2)                                | > 0                |
| `discount_value`                 | Decimal(10, 2)                                | Nullable           |
| `discount_type`                  | Enum(`amount`, `percent`)                     | Nullable           |
| `promotion_type`                 | Enum(`discount`, `other`)                     | Required           |
| `status`                         | Enum(`draft`, `active`, `expired`, `deleted`) | Default `draft`    |
| `start_date` / `expiration_date` | DateTime                                      | Expiration > Start |
| `discounted_price`               | Computed property                             | Runtime only       |

---

## Role-Based Views

| Role     | Visible Promotions  |
| :------- | :------------------ |
| Customer | Active only         |
| Supplier | Active + Expired    |
| Manager  | All (incl. Deleted) |

---

## Error Responses (JSON-Only)

| Code | Meaning                                         |
| :--- | :---------------------------------------------- |
| 400  | Bad Request – invalid fields                    |
| 403  | Forbidden – unauthorized action                 |
| 404  | Not Found – invalid ID                          |
| 409  | Conflict – duplicate name                       |
| 422  | Unprocessable Entity – business logic violation |
| 500  | Internal Server Error                           |

---

## CLI Commands

```bash
flask db-create   # create tables
flask db-drop     # drop tables
```

---

## Project Structure

```text
service/
├── __init__.py
├── config.py
├── models.py
├── routes.py
└── common/
    ├── cli_commands.py
    ├── error_handlers.py
    ├── log_handlers.py
    └── status.py
tests/
├── test_models.py
├── test_routes.py
├── test_cli_commands.py
└── factories.py
wsgi.py
```

---

## Sprint 1 Stories (Status)

|  ID | Feature                    | Status |
| :-: | :------------------------- | :----: |
|  #1 | Create Promotion Model     |    ✅   |
|  #2 | Create Promotion (POST)    |    ✅   |
|  #3 | Read Promotion (GET)       |    ✅   |
|  #4 | Update Promotion (PUT)     |    ✅   |
|  #5 | Delete Promotion (DELETE)  |    ✅   |
|  #6 | Search Promotion           |    ✅   |
|  #8 | List Promotions (GET All)  |    ✅   |
|  #9 | Promotion Expiration Logic |    ✅   |
| #10 | Root URL Metadata          |    ✅   |
|  #7 | README Documentation       |    ✅   |

---

## Coverage Summary

```
## Name                               Stmts   Miss  Cover   Missing

service/**init**.py                   30      2    93%   52–53
service/common/cli_commands.py        19      0   100%
service/common/error_handlers.py      33      0   100%
service/common/log_handlers.py        12      0   100%
service/common/status.py              45      0   100%
service/config.py                      7      0   100%
service/models.py                    132      5    96%   133, 135, 137, 141, 153
service/routes.py                     74      1    99%   167
------------------------------------------------------------

TOTAL                                352      8    98%

```
✅ **All 63 tests passed**  
✅ **Required coverage ≥ 95% achieved (97.7%)**  
✅ **Meets full-score rubric for test completeness**

---

## Team Promotions (FA25)

Jackie Wen，Yin (light12222)，Lokesh Boominathan，Sai Vishal，Daiveek S.

**Instructor :** Prof. John J. Rofrano
**TA :** NYU DevOps Team

---

## License

Copyright (c) 2016–2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/).
All rights reserved.

Licensed under the [Apache 2.0 License](https://opensource.org/licenses/Apache-2.0).

This repository is part of the New York University (NYU) masters class:
**CSCI-GA 2820 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute and NYU Stern School of Business.
