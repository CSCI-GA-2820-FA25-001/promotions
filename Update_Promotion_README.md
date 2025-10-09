Description

Update an existing promotion’s details such as price, discount, dates, or status.
Supports both partial and full updates. If a field is omitted, its value remains unchanged.

HTTP Request
PUT /promotions/<id>
Content-Type: application/json

Request Body
Field	Type	Required	Description
product_name	string	No	New name of the product
original_price	decimal	No	Updated base price
discount_value	decimal	No	Updated discount amount or percent
discount_type	string	No	"amount" or "percent"
promotion_type	string	No	"discount" or "other"
start_date	datetime	No	Updated start date (YYYY-MM-DD)
expiration_date	datetime	No	Updated end date (YYYY-MM-DD)
status	string	No	"draft", "active", "expired", "deactivated", "deleted"
Example
curl -X PUT http://localhost:8080/promotions/3 \
     -H "Content-Type: application/json" \
     -d '{
           "discount_value": 15.0,
           "discount_type": "percent",
           "status": "active"
         }'

Success Response

200 OK

{
  "id": 3,
  "product_name": "Wireless Headphones",
  "original_price": 200.0,
  "discount_value": 15.0,
  "discount_type": "percent",
  "discounted_price": 170.0,
  "promotion_type": "discount",
  "start_date": "2025-10-05",
  "expiration_date": "2025-11-05",
  "status": "active"
}

Error Responses
Code	Meaning	Example
400 Bad Request	Invalid or missing field	{"error":"Bad Request","message":"Invalid discount_type"}
404 Not Found	No promotion with that ID	{"error":"Not Found","message":"Promotion with id=3 not found"}
405 Method Not Allowed	Wrong HTTP method	{"error":"Method Not Allowed"}
Acceptance Criteria

✅ Returns 200 with updated JSON when record exists

✅ Returns 404 if promotion ID not found

✅ Returns 400 for invalid input or bad enum values

✅ Error responses always JSON

✅ Covered by unit + route tests
