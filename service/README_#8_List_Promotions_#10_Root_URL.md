## Summary
This update implements and documents two REST API endpoints in the Promotions microservice:
- **#8 – List Promotions**
- **#10 – Root URL**

These endpoints are part of the Flask-based Promotions REST API and provide basic information and data retrieval.

---

## Endpoints

### GET /
**Description:**  
Returns basic service information and a map of available endpoints.

**Example Request:**
```bash
curl http://localhost:8080/
````

**Example Response:**

```json
{
  "name": "Promotions REST API Service",
  "version": "1.0",
  "endpoints": {
    "list_promotions": "http://localhost:8080/promotions"
  }
}
```

**Status Code:** 200 OK

---

### GET /promotions

**Description:**
Returns a list of all promotions currently stored in the database.

**Example Request:**

```bash
curl http://localhost:8080/promotions
```

**Example Response:**

```json
[
  {
    "id": 1,
    "product_name": "Apple Watch",
    "description": "10% off all models",
    "original_price": 299.99,
    "discount_value": 30.0,
    "discount_type": "amount",
    "promotion_type": "discount",
    "start_date": "2025-01-01T00:00:00",
    "expiration_date": "2025-12-31T23:59:59",
    "status": "active"
  }
]
```

**Status Code:** 200 OK

---

## Test Coverage

* `test_routes.py::test_index` — verifies root URL returns service info and endpoint map
* `test_routes.py::test_list_promotions` — verifies list of promotions is returned successfully
* Unit tests run with `pytest --cov=service --cov-report=term-missing`

---

## Tech Stack

| Component  | Purpose                     |
| ---------- | --------------------------- |
| Flask      | REST API framework          |
| SQLAlchemy | ORM for database operations |
| MySQL      | Backend database            |
| pytest     | Testing framework           |

---

## Contributors

| Name            | Role              | Issues    |
| --------------- | ----------------- | --------- |
| Yin Wang        | Backend Developer | #8, #10   |
| [Teammate Name] | Reviewer          | QA Review |

---

## Closing

closes #8
closes #10
