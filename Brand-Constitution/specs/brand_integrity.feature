Feature: Brand Integrity and Constitutional Compliance

  Background:
    Given the Brand Constitution is loaded from "constitution.example.md"

  Scenario Outline: Reject forbidden marketing clichés across all channels
    Given an article draft or social copy asset
    When the text contains the forbidden term "<term>"
    Then the validation pipeline must flag a "Severity 1" brand violation
    And the build must fail with an exit code of 1

    Examples:
      | term                        |
      | delve                       |
      | tapestry                    |
      | game-changer                |
      | in today's fast-paced world |
      | cutting-edge                |

  Scenario: Enforce attribution on empirical claims
    Given an article draft containing numerical statistics
    When a percentage claim is presented without attribution or methodology
    Then the validation agent must demand an inline citation or source footnote

  Scenario: Validate typographical standards
    Given a published markdown article
    When curly or smart quotation marks are detected
    Then the linter must automatically convert them to standard ASCII straight quotes
