# 01 — Project Architecture Rules

## Objective
Keep the system modular, predictable, testable, secure, and resistant to uncontrolled AI-generated code growth.

## Required Layering
Prefer a structure conceptually similar to:

UI / Pages
↓
Use Cases / Application Services
↓
Domain / Business Logic
↓
Repository / API Client
↓
Database / External Services

Exact folder names may differ, but responsibilities must remain separated.

## Rules

### 1. Define module boundaries
Each major business capability should live in a distinct module.

Examples:
- customers
- quotes
- orders
- care
- pricing
- inventory
- reports
- settings

### 2. Avoid feature mixing
A module must not directly manipulate another module's internal state or database implementation.

Cross-module operations should use public services/interfaces.

### 3. Separate concerns
Do not mix:
- presentation,
- routing,
- business rules,
- data access,
- authorization,
- persistence

inside one component or file.

### 4. No circular dependencies
Module A → Module B → Module A is prohibited.

If shared behavior exists, extract it into a stable shared/domain layer.

### 5. Prefer stable public interfaces
Internal implementation may change, but other modules should depend on interfaces/services rather than implementation details.

### 6. Do not redesign unrelated architecture
A feature request is not permission to rewrite working architecture.

### 7. Architecture changes require explicit justification
Before changing architectural boundaries, document:
- current limitation,
- proposed change,
- affected modules,
- migration cost,
- compatibility impact,
- rollback strategy.

### 8. Shared code must truly be shared
Do not place code into `shared/` merely because it is convenient.

Shared code should:
- have no feature-specific assumptions,
- be reusable by at least two legitimate consumers,
- have a stable responsibility.

## Preferred Example Structure

src/
├── app/
│   ├── router/
│   ├── auth/
│   └── providers/
├── modules/
│   ├── customers/
│   ├── quotes/
│   ├── orders/
│   └── care/
├── shared/
│   ├── components/
│   ├── hooks/
│   ├── types/
│   └── utils/
├── services/
└── config/

A module may contain:

module/
├── pages/
├── components/
├── use-cases/
├── services/
├── repositories/
├── schemas/
├── types/
└── tests/

## Architecture Review Questions
Before implementation:
- Which module owns this behavior?
- Is this logic UI, business, data, or infrastructure?
- Does an existing service already own it?
- Will this create coupling?
- Will another feature need to know implementation details?
- Can this be tested independently?
