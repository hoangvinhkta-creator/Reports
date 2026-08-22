# 04 — Security Rules

## Core Security Principle
The client is untrusted.

Anything delivered to the browser/app must be treated as observable and potentially manipulable.

## Mandatory Rules

### 1. Never store secrets in frontend code
Do not expose:
- private API keys,
- admin credentials,
- database secrets,
- private tokens,
- service account credentials.

### 2. UI hiding is not authorization
This is NOT security:

if (!isAdmin) hideButton()

Authorization must also be enforced in:
- backend,
- server function,
- API,
- database/security rules.

### 3. Least privilege
Users and services receive only the permissions necessary for their role.

### 4. Default deny
Sensitive resources should be inaccessible unless explicitly permitted.

### 5. Never trust client-submitted authorization data
Do not trust client values such as:
- role,
- userId,
- ownerId,
- permission,
- price,
- discount,
- approval state.

Validate authoritative values server-side.

### 6. Protect sensitive business data
Examples:
- cost price,
- margins,
- internal supplier terms,
- internal notes,
- customer personal information,
- exports.

### 7. Authentication is not authorization
An authenticated user is not automatically allowed to access every resource.

### 8. Resource ownership must be enforced
If users can only access assigned customers/orders/etc., enforce that rule at the backend/data layer.

### 9. Validate mutations
Create/update/delete operations require:
- authenticated identity,
- authorization,
- validated input,
- permitted state transition.

### 10. Avoid excessive data return
APIs and database queries should return only necessary fields.

### 11. Logging restrictions
Never log:
- passwords,
- full authentication tokens,
- private secrets,
- unnecessary sensitive customer data.

### 12. Error messages
Do not leak internal stack details or secrets to end users.

### 13. Security-sensitive operations
Consider additional controls for:
- deleting records,
- bulk export,
- role changes,
- price overrides,
- financial adjustments,
- sensitive configuration.

### 14. Auditability
High-risk changes should record:
- actor,
- timestamp,
- action,
- target,
- relevant before/after state where appropriate.

## Security Review
For every feature ask:
- Who can read this?
- Who can create it?
- Who can update it?
- Who can delete it?
- Can users access another user's resource by changing an ID?
- Does the frontend receive data the user should never see?
- Is authorization enforced outside the UI?
