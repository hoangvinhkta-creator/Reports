# 02 — Routing Rules

## Objective
Routes must reflect application structure instead of concentrating unrelated functions behind one static URL.

## Rules

### 1. Major capabilities require explicit routes
Examples:

/dashboard
/customers
/customers/:customerId
/quotes
/quotes/:quoteId
/orders
/orders/:orderId
/care/today
/reports
/settings/users

### 2. Do not hide the entire application behind one route
Switching major application sections only through local tab state is discouraged.

Tabs are acceptable for secondary views inside one logical resource.

### 3. Routes must be refresh-safe
Opening or refreshing a valid deep link must render the intended page.

### 4. Browser history must work
Back/forward navigation should reflect meaningful application navigation.

### 5. Route parameters must be explicit
Use stable identifiers such as:

/customers/:customerId

Do not rely on hidden transient state for critical page identity.

### 6. Authentication guards
Protected routes must require authenticated identity.

### 7. Authorization guards
Sensitive routes must check required permission/role before rendering.

Examples:
/settings/users
/admin
/pricing/cost

### 8. Frontend guards are not security boundaries
Backend/database authorization must still enforce access.

### 9. Define route ownership
Every route must belong to one module.

### 10. Route changes require impact review
Check:
- navigation links,
- bookmarks,
- redirects,
- permissions,
- tests,
- analytics,
- API assumptions,
- deep links.

## Routing Checklist
Before completing a route change:
- Direct URL works.
- Refresh works.
- Back/forward works.
- Unauthorized access is blocked.
- Not-found state exists.
- Loading state exists when needed.
- Route parameters are validated.
