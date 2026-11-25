Feature: Shopping cart and checkout
  As a customer I want to buy products so that I receive an order confirmation.

  Scenario: Customer buys an in-stock product
    Given the store has "Smart Watch" in stock
    When I add 2 units of "Smart Watch" to my cart
    And I check out as "Nimali" with email "nimali@example.com" and address "Matara"
    Then I should see an order confirmation
    And the stock of "Smart Watch" should be 5

  Scenario: Customer cannot add more than the available stock
    Given the store has "Smart Watch" in stock
    When I add 8 units of "Smart Watch" to my cart
    Then my cart should be empty

  Scenario Outline: Checkout rejects invalid customer details
    Given the store has "Ceramic Mug" in stock
    When I add 1 units of "Ceramic Mug" to my cart
    And I check out as "<name>" with email "<email>" and address "<address>"
    Then I should not see an order confirmation

    Examples:
      | name  | email         | address |
      |       | a@b.co        | Galle   |
      | Kamal | not-an-email  | Galle   |
      | Kamal | a@b.co        |         |
