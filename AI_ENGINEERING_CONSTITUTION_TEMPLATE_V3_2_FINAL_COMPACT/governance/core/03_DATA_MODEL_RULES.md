# 03 — Data Model Rules

## Objective
Data structure must be designed intentionally before feature code is built.

## Rule: No schema-by-accident
A new feature must identify all affected entities and fields before implementation.

## Every Entity Should Define
- entity name,
- purpose,
- identifier,
- fields,
- types,
- required/optional status,
- defaults,
- relationships,
- ownership,
- created timestamp,
- updated timestamp,
- lifecycle/status where applicable.

## Field Classification
Each important field should be classified as one of:

- Public
- Internal business data
- Sensitive business data
- Personal/customer data
- System data
- Secret / server-only

## Example

Customer
- id
- name
- phone
- assignedUserId
- createdAt
- updatedAt

Quote
- id
- customerId
- ownerId
- status
- items[]
- subtotal
- discount
- total
- createdAt
- updatedAt

## Rules

### 1. One authoritative representation
Avoid storing the same business fact in multiple locations unless denormalization is intentional and synchronized.

### 2. Stable identifiers
Do not use display labels as primary identity.

### 3. Explicit relationships
Relationships must be represented intentionally.

### 4. Validate data at boundaries
Incoming external/client data must be validated before persistence.

### 5. Do not trust missing/null semantics implicitly
Define whether:
- missing,
- null,
- empty string,
- zero

have different meanings.

### 6. Schema changes require compatibility analysis
Before changing a persisted schema, identify:
- old schema,
- new schema,
- existing records,
- migration need,
- rollback,
- backward compatibility.

### 7. No destructive rename/delete without migration
Do not rename or remove production fields and assume old data will adapt automatically.

### 8. Timestamps
Use a consistent timestamp strategy.

### 9. Status fields
Use defined enums/state values rather than arbitrary strings.

### 10. Sensitive values
Do not expose sensitive fields merely because the frontend does not display them.

## Migration Template
For persisted schema changes document:

Current schema:
...

Target schema:
...

Migration:
...

Backward compatibility:
...

Validation:
...

Rollback:
...
