@bpl @vm
Feature: Voucher code status updates from 3rd party
  As a retailer I want to be able to handle updates to vouchers provided by a 3rd party
  so that existing vouchers can be updated in BPL to show status changes.

  Scenario: Handle importing redeemed and/or cancelled voucher code status changed from a 3rd party

    Given The voucher code provider provides a bulk file for test-retailer and the file is imported by the voucher management system
    Then The test-retailer import file is archived by the voucher importer
