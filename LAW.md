# Laws

Durable statements. Implementations are disposable.
`claim_success` from an agent is not evidence.

## balance

- id: balance
- statement: Account balance is never negative.
- check: balance_never_negative
- require: opening_balance, withdrawals

## migration

- id: migration
- statement: After migration, users.email remains NOT NULL.
- check: email_not_null
- require: users_after_migration

## formula

- id: formula
- statement: x^2 >= 2x for all real x.
- check: formula_always_holds
- require: samples

## pii

- id: pii
- statement: API responses never contain raw national IDs.
- check: none
- require: response_trace

## facts

- id: facts
- statement: SUCCESS/ALLOW requires non-empty supporting facts.
- check: facts_non_empty
- require: facts

## consistency

- id: consistency
- statement: SUCCESS/ALLOW requires consistency score at or above 0.70.
- check: consistency_floor
- require: consistency_score
