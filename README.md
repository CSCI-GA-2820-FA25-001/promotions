# NYU DevOps Project — Promotions Microservice

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![Build Status](https://github.com/CSCI-GA-2820-FA25-001/promotions/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA25-001/promotions/actions)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-FA25-001/promotions/branch/master/graph/badge.svg)](https://codecov.io/gh/CSCI-GA-2820-FA25-001/promotions)
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
```

Start the containers:
```
cd .devcontainer
docker compose up -d
docker exec -it nyu-project bash
```


## Testing

Run all tests with coverage:

```
make test
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
  - `find_by_status(status)`: Find promotions by status
  - `find_by_expiration_date(expiration_date)`: Find promotions by expiration_date
  - `find_by_promotion_type(promotion_type)`: Find promotions by promotion_type
  - `find_by_discount_type(discount_type)`: Find promotions by discount_type


## model_testing


The tests cover:

- Creating, updating, deleting promotions
- Validating data types
- Checking `discounted_price` calculation
- Handling `discount` and `other` promotion types
- Rollback behavior on database errors



## API Endpoints

| Method | Endpoint           | Description                  | Success        | Errors                |
| :----- | :----------------- | :--------------------------- | :------------- | :-------------------- |
| POST   | `/promotions`      | Create a new promotion       | 201 Created    | 400 / 403 / 409 / 422 |
| GET    | `/promotions/<id>` | Retrieve a promotion by ID   | 200 OK         | 400 / 404             |
| PUT    | `/promotions/<id>` | Update an existing promotion | 200 OK         | 400 / 404 / 422       |
| DELETE | `/promotions/<id>` | Soft delete promotion        | 204 No Content | 400 / 403 / 404 / 409 |
| POST   | `/promotions/<id>/duplicate` | Duplicate a promotion | 201 Created | 400 / 401 / 403 / 404 / 409 / 422 |
| GET    | `/promotions`      | List promotions (role-based) | 200 OK         | 400 / 404             |
| GET    | `/`                | Service metadata             | 200 OK         | 500                   |

---

## Authentication & Authorization

### Authentication Method
Uses `X-Role` header for role-based access control.

**Header Format:**
```http
X-Role: administrator
```

**Available Roles:**
- `administrator` - Full access (create, update, delete)
- `customer` - Read-only access to active promotions
- `supplier` - Read-only access to active and expired promotions
- `manager` - Read-only access to all promotions

### Authorization Rules

| Endpoint | Method | Required Role |
|----------|--------|---------------|
| `POST /promotions` | Create | Administrator |
| `PUT /promotions/<id>` | Update | Administrator |
| `DELETE /promotions/<id>` | Delete | Administrator |
| `POST /promotions/<id>/duplicate` | Duplicate | Administrator |
| `GET /promotions` | List/Search | Any (filtered by role) |
| `GET /promotions/<id>` | Read | Any |

---

## Detailed API Documentation

### Root URL - `GET /`

Returns service metadata and available endpoints.

**Response (200 OK):**
```json
{
  "service": "Promotions REST API Service",
  "version": "1.0",
  "description": "This service manages promotions for an eCommerce platform.",
  "list_url": "http://localhost:8080/promotions"
}
```

---

### Create Promotion - `POST /promotions`

Create a new promotion (admin only).

**Required Headers:**
```http
Content-Type: application/json
X-Role: administrator
```

**Request Body:**
```json
{
  "product_name": "Black Friday Sale",
  "description": "Huge discount event",
  "original_price": 100.00,
  "discount_value": 20.0,
  "discount_type": "percent",
  "promotion_type": "discount",
  "start_date": "2025-10-14T00:00:00",
  "expiration_date": "2025-11-14T23:59:59"
}
```

**Required Fields:**
- `product_name` - Unique name
- `original_price` - Must be > 0
- `promotion_type` - `"discount"` or `"other"`
- `expiration_date` - Must be after `start_date`

**Success Response (201 Created):**
```json
{
  "id": 1,
  "product_name": "Black Friday Sale",
  "description": "Huge discount event",
  "original_price": 100.0,
  "discount_value": 20.0,
  "discount_type": "percent",
  "promotion_type": "discount",
  "discounted_price": 80.0,
  "start_date": "2025-10-14T00:00:00",
  "expiration_date": "2025-11-14T23:59:59",
  "status": "draft",
  "created_at": "2025-10-14T10:30:00.123456",
  "updated_at": "2025-10-14T10:30:00.123456"
}
```

**Validation Rules:**
- `original_price > 0`
- `discount_value <= original_price` (for amount type)
- `0 <= discount_value <= 100` (for percent type)
- `expiration_date > start_date`
- If `promotion_type = "other"` → discount fields must be null

**cURL Example:**
```bash
curl -X POST http://localhost:8080/promotions \
  -H "Content-Type: application/json" \
  -H "X-Role: administrator" \
  -d '{
    "product_name": "Holiday Special",
    "original_price": 200.00,
    "discount_value": 50.00,
    "discount_type": "amount",
    "promotion_type": "discount",
    "expiration_date": "2025-12-25T23:59:59"
  }'
```

---

### List Promotions - `GET /promotions`

List promotions filtered by user role.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `role` | string | `customer` | Filter by user role |

**Role-Based Filtering:**
- **customer**: Only `active` promotions
- **supplier**: `active` + `expired` promotions
- **manager**: All promotions

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "product_name": "Black Friday Sale",
    "status": "active",
    "discounted_price": 80.0,
    "original_price": 100.0,
    "discount_value": 20.0,
    "discount_type": "percent",
    ...
  }
]
```

**cURL Examples:**
```bash
# Customer view (active only)
curl http://localhost:8080/promotions?role=customer

# Supplier view (active + expired)
curl http://localhost:8080/promotions?role=supplier

# Manager view (all)
curl http://localhost:8080/promotions?role=manager
```

---

### Search Promotions - `GET /promotions`

Search promotions using query parameters.

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `product_name` | string | Substring match | `?product_name=phone` |
| `status` | string | Filter by status | `?status=active` |
| `promotion_type` | string | Filter by type | `?promotion_type=discount` |
| `discount_type` | string | Filter by discount | `?discount_type=percent` |
| `expiration_date` | date | Expiring on/before | `?expiration_date=2025-12-31` |

**Note:** Multiple filters can be combined.

**Success Response (200 OK):**
```json
[
  {
    "id": 2,
    "product_name": "Smartphone Pro",
    "discount_value": 10.0,
    "discount_type": "percent",
    "status": "active",
    ...
  }
]
```

**cURL Examples:**
```bash
# Active promotions only
curl http://localhost:8080/promotions?status=active

# Discount promotions containing "phone"
curl "http://localhost:8080/promotions?product_name=phone&promotion_type=discount"

# Percent-based discounts
curl http://localhost:8080/promotions?discount_type=percent
```

---

### Update Promotion - `PUT /promotions/<id>`

Update an existing promotion (partial or full update).

**Headers:**
```http
Content-Type: application/json
X-Role: administrator
```

**Request Body (all fields optional):**
```json
{
  "discount_value": 15.0,
  "discount_type": "percent",
  "status": "active"
}
```

**Success Response (200 OK):**
```json
{
  "id": 3,
  "product_name": "Wireless Headphones",
  "original_price": 200.0,
  "discount_value": 15.0,
  "discount_type": "percent",
  "discounted_price": 170.0,
  "promotion_type": "discount",
  "status": "active",
  "updated_at": "2025-10-14T11:45:00.789012",
  ...
}
```

**cURL Example:**
```bash
curl -X PUT http://localhost:8080/promotions/3 \
  -H "Content-Type: application/json" \
  -H "X-Role: administrator" \
  -d '{
    "discount_value": 15.0,
    "status": "active"
  }'
```

---

### Duplicate Promotion - `POST /promotions/<id>/duplicate`

Create a new promotion by copying an existing one (admin only).

**Required Headers:**
```http
Content-Type: application/json
X-Role: administrator
```

**Request Body (all fields optional overrides):**
```json
{
  "product_name": "Duplicated Promotion",
  "expiration_date": "2025-12-31T23:59:59",
  "discount_value": 25.0
}
```

**Success Response (201 Created):**
```json
{
  "id": 456,
  "product_name": "Duplicated Promotion",
  "description": "Original description",
  "original_price": 100.0,
  "discount_value": 25.0,
  "discount_type": "percent",
  "promotion_type": "discount",
  "discounted_price": 75.0,
  "status": "draft",
  "start_date": "2025-10-14T00:00:00",
  "expiration_date": "2025-12-31T23:59:59",
  "created_at": "2025-10-14T10:30:00.123456",
  "updated_at": "2025-10-14T10:30:00.123456"
}
```

**Key Features:**
- Copies all fields from original promotion
- Generates new system fields (id, created_at, updated_at)
- Sets default status to `"draft"`
- Allows field overrides via request body
- Only administrators can duplicate promotions

**cURL Examples:**
```bash
# Duplicate with no overrides
curl -X POST http://localhost:8080/promotions/123/duplicate \
  -H "Content-Type: application/json" \
  -H "X-Role: administrator" \
  -d '{}'

# Duplicate with overrides
curl -X POST http://localhost:8080/promotions/123/duplicate \
  -H "Content-Type: application/json" \
  -H "X-Role: administrator" \
  -d '{
    "product_name": "Black Friday 2025",
    "expiration_date": "2025-12-31T23:59:59",
    "discount_value": 30.0
  }'
```

**Error Responses:**
- **401 Unauthorized** - Missing X-Role header
- **403 Forbidden** - Non-admin role (customer, supplier, manager)
- **404 Not Found** - Original promotion doesn't exist
- **409 Conflict** - Duplicate product_name (if overridden)
- **422 Unprocessable Entity** - Validation errors in overrides

---

## Discount Calculation

The `discounted_price` is automatically calculated based on:

- **Amount discount:** `original_price - discount_value` (minimum: 0)
- **Percent discount:** `original_price * (1 - discount_value/100)` (minimum: 0)
- **No discount:** Returns `original_price`

**Examples:**
```python
# Amount discount
original_price: 100.00, discount_value: 25.00, discount_type: "amount"
→ discounted_price = 75.00

# Percent discount
original_price: 100.00, discount_value: 20.0, discount_type: "percent"
→ discounted_price = 80.00

# No discount (promotion_type: "other")
original_price: 99.99
→ discounted_price = 99.99
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

All error responses follow a consistent JSON format:

| Code | Meaning                                         | Example Scenario |
| :--- | :---------------------------------------------- | :--------------- |
| 400  | Bad Request – invalid fields                    | Missing required field, invalid JSON, bad enum |
| 401  | Unauthorized – missing authentication           | No X-Role header |
| 403  | Forbidden – unauthorized action                 | Non-admin trying to create |
| 404  | Not Found – invalid ID                          | Promotion doesn't exist |
| 405  | Method Not Allowed – wrong HTTP method          | PUT on root URL |
| 409  | Conflict – duplicate name                       | product_name already exists |
| 422  | Unprocessable Entity – business logic violation | discount > price, invalid dates |
| 500  | Internal Server Error                           | Unexpected server errors |

### Error Response Examples

**401 Unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "error": "Forbidden",
  "message": "Administrator privileges required to create promotions"
}
```

**400 Bad Request:**
```json
{
  "error": "Invalid request",
  "message": "Missing required field: product_name"
}
```

**422 Unprocessable Entity:**
```json
{
  "error": "Unprocessable Entity",
  "message": "discount_value cannot exceed original_price for amount-based discounts"
}
```

**409 Conflict:**
```json
{
  "error": "Conflict",
  "message": "Promotion with name 'Black Friday Sale' already exists"
}
```

**404 Not Found:**
```json
{
  "error": "Not Found",
  "message": "Promotion with id=123 not found"
}
```

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
