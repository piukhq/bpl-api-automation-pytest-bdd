@bpl @cm @vouchers
Feature: Post a balance adjustment for a incorrect-retailer
  As a VM system
  Using the POST [retailer_slug]/accounts/[account_holder_uuid]/vouchers endpoint
  I can't add an account holder voucher

  Scenario: POST a voucher for invalid retailer

    When I post a voucher for a invalid-retailer account holder with a valid auth token
    Then I receive a HTTP 403 status code in the voucher response
    And I get a invalid_retailer voucher response body

  Scenario: POST a voucher for an invalid retailer with an invalid authorisation token

    When I post a voucher for a invalid-retailer account holder with a invalid auth token
    Then I receive a HTTP 401 status code in the voucher response
    And I get a invalid_token voucher response body

  Scenario: POST a voucher for an valid retailer with an valid authorisation token for an unknown account holder

    When I post a voucher for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 404 status code in the voucher response
    And I get a no_account_found voucher response body