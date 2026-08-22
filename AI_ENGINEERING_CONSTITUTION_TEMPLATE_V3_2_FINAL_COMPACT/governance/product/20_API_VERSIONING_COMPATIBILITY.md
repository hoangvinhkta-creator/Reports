# 20 — API Versioning & Compatibility Rules

## Objective
Prevent client/server changes from silently breaking existing consumers.

## Rules

### 1. Treat published API contracts as interfaces
Do not change response/request meaning casually.

### 2. Classify changes

Non-breaking examples:
- adding optional response field,
- adding optional request field with safe default.

Potentially breaking:
- removing field,
- renaming field,
- changing type,
- changing status meaning,
- changing authorization behavior,
- changing endpoint semantics.

### 3. Breaking changes require migration strategy
Options may include:
- versioned endpoint,
- compatibility adapter,
- staged rollout,
- coordinated client deployment.

### 4. Error contracts
Use predictable error categories.

### 5. Enum/status expansion
Consumers should be considered when adding new states.

### 6. Deprecation
When an API is deprecated:
- mark it,
- identify consumers,
- set migration path,
- remove only after migration criteria are met.

### 7. Internal APIs
Even internal APIs require compatibility thinking if multiple modules/services consume them.

## API Review
Before changing an API ask:
- Who consumes this?
- Are older clients still active?
- Can deployment order break the system?
- Can the change be backward compatible?
