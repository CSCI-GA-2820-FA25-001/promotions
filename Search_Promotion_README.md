Description

Retrieve promotions filtered by one or more query parameters such as product name, status, discount type, or expiration date.
If no parameters are given, all promotions are returned.

HTTP Request
GET /promotions

Query Parameters
Parameter	Type	Description	Example
product_name	string	Case-insensitive substring match	?product_name=phone
status	string	Filter by status (active, draft, etc.)	?status=active
promotion_type	string	Filter by promotion type	?promotion_type=discount
discount_type	string	Filter by discount type	?discount_type=percent
expiration_date	date	Promotions expiring before or on date	?expiration_date=2025-12-31
Examples
# Active promotions only
curl http://localhost:8080/promotions?status=active

# Discount promotions containing “phone” in the name
curl http://localhost:8080/promotions?product_name=phone&promotion_type=discount

Success Response

200 OK

[
  {
    "id": 2,
    "product_name": "Smartphone Pro",
    "discount_value": 10.0,
    "discount_type": "percent",
    "status": "active"
  },
  {
    "id": 5,
    "product_name": "Phone Cover",
    "discount_value": 2.5,
    "discount_type": "amount",
    "status": "active"
  }
]

Error Responses
Code	Meaning	Example
400 Bad Request	Invalid query or format	{"error":"Bad Request","message":"Invalid date format"}
405 Method Not Allowed	Wrong HTTP verb	{"error":"Method Not Allowed"}
Acceptance Criteria

Returns 200 with JSON array of matching promotions

Returns empty list if no matches

Supports multiple filters combined

Returns 400 for invalid query formats

Covered by route tests for valid + invalid filters

Follows PEP8 and achieves ≥ 95 % coverage

🔧 Testing Notes
# Inside container
docker exec -it nyu-project bash
pytest tests/test_routes.py::TestUpdatePromotion
pytest tests/test_routes.py::TestSearchPromotions


Each test should assert both successful and failure cases, verifying correct status codes, JSON structure, and message consistency.
