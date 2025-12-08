Feature: Promotions service back-end
    As a Marketing Manager
    I need a RESTful promotions service
    So that I can manage product promotions

Background:
    Given the following promotions
        | product_name | description     | promotion_type | original_price | discount_value | discount_type | expiration_date      | status   |
        | Apple        | Fresh apples    | discount       | 10.0           | 2.0            | amount        | 2025-12-31T23:59:59  | active   |
        | Orange       | Sweet oranges   | discount       | 8.0            | 10.0           | percent       | 2025-12-31T23:59:59  | expired  |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Promotions Management" in the title
    And I should not see "404 Not Found"

Scenario: Create a Promotion
    When I visit the "Home Page"
    And I set the "Product Name" to "Phone"
    And I set the "Description" to "Holiday sale"
    And I set the "Original Price" to "999"
    And I select "Discount" in the "Promotion Type" dropdown
    And I set the "Discount Value" to "20"
    And I select "Percent" in the "Discount Type" dropdown
    And I set the "Expiration Date" to "2025-12-31T23:59"
    And I select "Active" in the "Status" dropdown
    And I press the "Create" button
    Then I should see "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    And I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see "Success"
    And I should see "Phone" in the "Product Name" field
    And I should see "Holiday sale" in the "Description" field

Scenario: List all promotions
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "Success"
    And I should see "Apple" in the results
    And I should see "Orange" in the results

Scenario: Search promotions by product name
    When I visit the "Home Page"
    And I set the "Product Name" to "Apple"
    And I press the "Search" button
    Then I should see "Success"
    And I should see "Apple" in the results
    And I should not see "Orange" in the results

Scenario: Update a Promotion
    When I visit the "Home Page"
    And I set the "Product Name" to "Apple"
    And I press the "Search" button
    Then I should see "Success"
    When I change "Description" to "Updated description"
    And I press the "Update" button
    Then I should see "Success"
    When I press the "Clear" button
    And I set the "Product Name" to "Apple"
    And I press the "Search" button
    Then I should see "Updated description" in the results

Scenario: Delete a Promotion
    When I visit the "Home Page"
    And I set the "Product Name" to "Orange"
    And I press the "Search" button
    Then I should see "Success"
    When I copy the "Id" field
    And I press the "Delete" button
    Then I should see "Promotion has been Deleted!"
    When I press the "Search" button
    Then I should not see "Orange" in the results

Scenario: Duplicate a promotion from the search results
    When I visit the "Home Page"
    And I set the "Product Name" to "Apple"
    And I press the "Search" button
    Then I should see "Success"
    And I should see "Apple" in the results
    When I press the "Duplicate" button for "Apple"
    Then I should see "Promotion duplicated"

