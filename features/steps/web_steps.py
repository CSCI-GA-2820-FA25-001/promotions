# flake8: noqa
# pylint: disable=function-redefined, missing-function-docstring

"""
Web Steps (FINAL VERSION — fully aligned with your index.html + rest_api.js)
"""

import logging
from behave import when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8080"

ID_PREFIX = "promotions_"     # ← FIXED: must match your HTML


##################################################################
# Visit Home Page
##################################################################
@when('I visit the "Home Page"')
def step_impl(context):
    context.driver.get(BASE_URL)


##################################################################
# Title check
##################################################################
@then('I should see "{message}" in the title')
def step_impl(context, message):
    assert message in context.driver.title


##################################################################
# Set input field
##################################################################
@when('I set the "{element_name}" to "{text_string}"')
def step_impl(context, element_name, text_string):
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = context.driver.find_element(By.ID, element_id)
    # element.clear()
    # element.send_keys(text_string)
    context.driver.execute_script("arguments[0].value = arguments[1];", element, text_string)


##################################################################
# Change field
##################################################################
@when('I change "{element_name}" to "{text_string}"')
def step_impl(context, element_name, text_string):
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = context.driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(text_string)


##################################################################
# Dropdown Select
##################################################################
@when('I select "{text}" in the "{element_name}" dropdown')
def step_impl(context, text, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    select = Select(context.driver.find_element(By.ID, element_id))
    select.select_by_visible_text(text)


##################################################################
# Dropdown Verify
##################################################################
@then('I should see "{text}" in the "{element_name}" dropdown')
def step_impl(context, text, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    select = Select(context.driver.find_element(By.ID, element_id))
    assert select.first_selected_option.text == text


##################################################################
# Field Empty
##################################################################
@then('the "{element_name}" field should be empty')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    value = context.driver.find_element(By.ID, element_id).get_attribute("value")
    assert value == ""


##################################################################
# Copy Field
##################################################################
@when('I copy the "{element_name}" field')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = context.driver.find_element(By.ID, element_id)
    context.clipboard = element.get_attribute("value")
    logging.info("Copied: %s", context.clipboard)


##################################################################
# Paste Field
##################################################################
@when('I paste the "{element_name}" field')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = context.driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(context.clipboard)


##################################################################
# Press Button
##################################################################
@when('I press the "{button}" button')
def step_impl(context, button):
    button_id = button.lower().replace(" ", "_") + "-btn"
    context.driver.find_element(By.ID, button_id).click()


##################################################################
# Flash Message
##################################################################
@then('I should see "{message}"')
def step_impl(context, message):
    found = WebDriverWait(context.driver, 10).until(
        EC.text_to_be_present_in_element((By.ID, "flash_message"), message)
    )
    assert found


##################################################################
# Field has value
##################################################################
@then('I should see "{text_string}" in the "{element_name}" field')
def step_impl(context, text_string, element_name):
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    el = context.driver.find_element(By.ID, element_id)
    assert text_string in el.get_attribute("value")


##################################################################
# Results contain
##################################################################
@then('I should see "{name}" in the results')
def step_impl(context, name):
    table = context.driver.find_element(By.ID, "search_results")
    WebDriverWait(context.driver, 5).until(
        EC.text_to_be_present_in_element((By.ID, "search_results"), name)
    )
    assert name in table.text


##################################################################
# Results not contain
##################################################################
@then('I should not see "{name}" in the results')
def step_impl(context, name):
    table = context.driver.find_element(By.ID, "search_results")
    assert name not in table.text

@then('I should not see "404 Not Found"')
def step_impl(context):
    assert "404 Not Found" not in context.driver.page_source
