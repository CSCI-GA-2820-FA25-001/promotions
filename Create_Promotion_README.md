# Create Promotion - User Story Implementation

## User Story
**As a** customer  
**I need to** create a new promotion  
**So that** I can add discount offers to the system

---

## Endpoint Details

### HTTP Method & URL
```
POST /promotions
```

### Authentication
**Required**: Yes  
**Authorization**: Administrator role only

Use the `X-Role` header to specify the user role:
```http
X-Role: administrator
```

---

## Request Format

### Headers
```http
Content-Type: application/json
X-Role: administrator
```

### Request Body (JSON)

**Required Fields:**
- `product_name` (string) - Unique name for the promotion
- `original_price` (number) - Must be > 0
- `promotion_type` (enum) - Either `"discount"` or `"other"`
- `expiration_date` (ISO 8601 datetime) - Must be after `start_date`

**Optional Fields:**
- `description` (string) - Description of the promotion
- `discount_value` (number) - Discount amount or percentage
- `discount_type` (enum) - Either `"amount"` or `"percent"`
- `start_date` (ISO 8601 datetime) - Defaults to current time
- `status` (enum) - Defaults to `"draft"` if not provided

**Note:** `discounted_price` is computed automatically and should NOT be included in the request.

---

## Response Format

### Success Response (201 Created)

**Status Code:** `201 Created`

**Headers:**
```http
Location: <URL to the created promotion>
Content-Type: application/json
```

**Response Body:**
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
  "start_date": "2025-10-14T10:30:00",
  "expiration_date": "2025-11-14T10:30:00",
  "status": "draft",
  "created_at": "2025-10-14T10:30:00.123456",
  "updated_at": "2025-10-14T10:30:00.123456"
}
```

---

## Validation Rules

### Input Validation (400 Bad Request)
Returns `400 Bad Request` for structural/format errors:
- Missing required fields (`product_name`, `original_price`, `promotion_type`, `expiration_date`)
- Invalid JSON format
- Invalid data types (e.g., string instead of number)
- Invalid enum values (e.g., `promotion_type: "invalid"`)

### Business Logic Validation (422 Unprocessable Entity)
Returns `422 Unprocessable Entity` for business rule violations:
- `original_price <= 0`
- `discount_value > original_price` (when `discount_type = "amount"`)
- `discount_value` not in range 0-100 (when `discount_type = "percent"`)
- `expiration_date <= start_date`
- Discount fields present when `promotion_type != "discount"`

### Duplicate Check (409 Conflict)
Returns `409 Conflict` when:
- A promotion with the same `product_name` already exists

---

## Error Responses

### 401 Unauthorized
Missing or invalid authentication:
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
Authenticated but insufficient privileges (non-admin):
```json
{
  "error": "Forbidden",
  "message": "Administrator privileges required to create promotions"
}
```

### 400 Bad Request
Invalid request format or missing required fields:
```json
{
  "error": "Invalid request",
  "message": "Missing required field: product_name"
}
```

### 422 Unprocessable Entity
Valid format but violates business rules:
```json
{
  "error": "Unprocessable Entity",
  "message": "discount_value cannot exceed original_price for amount-based discounts"
}
```

### 409 Conflict
Duplicate promotion name:
```json
{
  "error": "Conflict",
  "message": "Promotion with name 'Black Friday Sale' already exists"
}
```

---

## Example Usage

### Example 1: Create Percent-Based Discount Promotion

**Request:**
```http
POST /promotions HTTP/1.1
Content-Type: application/json
X-Role: administrator

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

**Response:**
```http
HTTP/1.1 201 Created
Location: http://localhost:8080/promotions
Content-Type: application/json

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

### Example 2: Create Amount-Based Discount Promotion

**Request:**
```http
POST /promotions HTTP/1.1
Content-Type: application/json
X-Role: administrator

{
  "product_name": "Holiday Special",
  "original_price": 200.00,
  "discount_value": 50.00,
  "discount_type": "amount",
  "promotion_type": "discount",
  "expiration_date": "2025-12-25T23:59:59"
}
```

**Response:**
```json
{
  "id": 2,
  "product_name": "Holiday Special",
  "description": null,
  "original_price": 200.0,
  "discount_value": 50.0,
  "discount_type": "amount",
  "promotion_type": "discount",
  "discounted_price": 150.0,
  "start_date": "2025-10-14T10:35:00",
  "expiration_date": "2025-12-25T23:59:59",
  "status": "draft",
  "created_at": "2025-10-14T10:35:00.789123",
  "updated_at": "2025-10-14T10:35:00.789123"
}
```

### Example 3: Create Non-Discount Promotion

**Request:**
```http
POST /promotions HTTP/1.1
Content-Type: application/json
X-Role: administrator

{
  "product_name": "Flash Sale",
  "original_price": 99.99,
  "promotion_type": "other",
  "expiration_date": "2025-10-20T23:59:59"
}
```

**Response:**
```json
{
  "id": 3,
  "product_name": "Flash Sale",
  "description": null,
  "original_price": 99.99,
  "discount_value": null,
  "discount_type": null,
  "promotion_type": "other",
  "discounted_price": 99.99,
  "start_date": "2025-10-14T10:40:00",
  "expiration_date": "2025-10-20T23:59:59",
  "status": "draft",
  "created_at": "2025-10-14T10:40:00.456789",
  "updated_at": "2025-10-14T10:40:00.456789"
}
```

---

## Testing with cURL

### Create a promotion:
```bash
curl -X POST http://localhost:8080/promotions \
  -H "Content-Type: application/json" \
  -H "X-Role: administrator" \
  -d '{
    "product_name": "Test Promotion",
    "original_price": 150.00,
    "discount_value": 15.0,
    "discount_type": "percent",
    "promotion_type": "discount",
    "expiration_date": "2025-12-31T23:59:59"
  }'
```

### Test authentication failure:
```bash
curl -X POST http://localhost:8080/promotions \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Test Promotion",
    "original_price": 150.00,
    "promotion_type": "discount",
    "expiration_date": "2025-12-31T23:59:59"
  }'
```

Expected response: `401 Unauthorized`

---

## Test Coverage

All test cases pass with comprehensive coverage:
- ✅ Success scenarios (percent & amount discounts)
- ✅ Authentication (401 when no X-Role header)
- ✅ Authorization (403 when role is not administrator)
- ✅ Input validation (400 for missing/invalid fields)
- ✅ Business logic validation (422 for rule violations)
- ✅ Duplicate prevention (409 for duplicate names)

**Run tests:**
```bash
make test
```

**Check code quality:**
```bash
make lint
```

---

## Technical Implementation Details

### Authentication Flow
1. Check for `X-Role` header in request
2. If missing → return 401 Unauthorized
3. If not "administrator" → return 403 Forbidden
4. If "administrator" → proceed with creation

### Validation Flow
1. Parse JSON (catch malformed JSON → 400)
2. Validate business logic rules (violations → 422)
3. Check for duplicate `product_name` (duplicate → 409)
4. Deserialize data using model's `deserialize()` method (format errors → 400)
5. Create and persist to database
6. Return 201 Created with serialized promotion

### Discount Calculation
The `discounted_price` is automatically calculated based on:
- **Amount discount:** `original_price - discount_value`
- **Percent discount:** `original_price * (1 - discount_value/100)`
- **No discount:** Returns `original_price`
- **Minimum:** Never goes below 0

---

## Related Files
- `service/routes.py` - Endpoint implementation
- `service/common/status.py` - HTTP status codes
- `service/common/error_handlers.py` - Error handling
- `tests/test_routes.py` - Test suite
- `service/models.py` - Promotion model (already implemented)

---

## Story Acceptance Criteria

- [x] Returns 201 Created with computed `discounted_price`
- [x] Returns 401 for unauthenticated requests
- [x] Returns 403 for non-admin users  
- [x] Returns 400 for invalid input format
- [x] Returns 422 for business rule violations
- [x] Returns 409 for duplicate names
- [x] Promotion persists to database
- [x] Default status is "draft"
- [x] Location header included in response
- [x] All responses in JSON format
- [x] Proper logging for debugging

