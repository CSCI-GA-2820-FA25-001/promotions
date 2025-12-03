from behave import given, when, then
import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:8080"

######################################################################
# Reset DB
######################################################################
def reset_database():
    resp = requests.delete(f"{BASE_URL}/promotions/reset")
    assert resp.status_code in (200, 204), f"Reset failed: {resp.status_code}"
    return resp


######################################################################
# GIVEN — seed
######################################################################
@given('the following promotions')
def step_impl(context):

    reset_database()

    for row in context.table:

        payload = {
            "product_name": row["product_name"],
            "description": row["description"],
            "promotion_type": row["promotion_type"],
            "original_price": float(row["original_price"]),
            "discount_value": float(row["discount_value"]) if row["discount_value"] else None,
            "discount_type": row["discount_type"] or None,
            "expiration_date": row["expiration_date"],
            "status": row["status"],
        }

        resp = requests.post(
            f"{BASE_URL}/promotions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
        )

        assert resp.status_code == 201, f"Create failed: {resp.text}"


######################################################################
# WHEN — create
######################################################################
@when('I create a promotion with:')
def step_impl(context):
    for row in context.table:

        payload = {
            "product_name": row["product_name"],
            "description": row["description"],
            "promotion_type": row["promotion_type"],
            "original_price": float(row["original_price"]),
            "discount_value": float(row["discount_value"]) if row["discount_value"] else None,
            "discount_type": row["discount_type"] or None,
            "expiration_date": row["expiration_date"],
            "status": row["status"],
        }

        context.resp = requests.post(
            f"{BASE_URL}/promotions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
        )


######################################################################
# WHEN — retrieve
######################################################################
@when('I retrieve promotion "{id}"')
def step_impl(context, id):
    context.resp = requests.get(f"{BASE_URL}/promotions/{id}")


######################################################################
# WHEN — delete
######################################################################
@when('I delete promotion "{id}"')
def step_impl(context, id):
    context.resp = requests.delete(f"{BASE_URL}/promotions/{id}")


######################################################################
# WHEN — list
######################################################################
@when('I list all promotions')
def step_impl(context):
    context.resp = requests.get(f"{BASE_URL}/promotions?role=manager")


######################################################################
# THEN — status code
######################################################################
@then('the status code should be "{code}"')
def step_impl(context, code):
    assert str(context.resp.status_code) == code, \
        f"Expected {code}, got {context.resp.status_code}. Body: {context.resp.text}"


######################################################################
# THEN — body contains
######################################################################
@then('I should see "{text}" in the response')
def step_impl(context, text):
    assert text in context.resp.text


######################################################################
# THEN — body not contain
######################################################################
@then('the response should not contain "{text}"')
def step_impl(context, text):
    assert text not in context.resp.text


######################################################################
# THEN — count
######################################################################
@then('the response contains "{count}" promotions')
def step_impl(context, count):
    data = context.resp.json()
    assert len(data) == int(count)
