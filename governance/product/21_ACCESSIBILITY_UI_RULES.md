# 21 — Accessibility & UI Quality Rules

## Objective
Ensure interfaces remain usable, understandable, consistent, and accessible.

## Rules

### 1. Semantic UI
Use appropriate semantic elements and controls.

### 2. Keyboard usability
Core workflows should not require a mouse where standard keyboard interaction is expected.

### 3. Labels
Inputs and controls need understandable labels.

### 4. Focus
Dialogs, menus, and route changes should preserve sensible focus behavior.

### 5. Error communication
Do not rely only on color to communicate errors or state.

### 6. Loading / Empty / Error States
Major data views should define:
- loading,
- empty,
- error,
- success.

### 7. Destructive actions
Clearly distinguish destructive operations.
Use confirmation when impact is significant.

### 8. Consistency
Reuse design system/components instead of creating visually different controls for the same function.

### 9. Responsive behavior
Core workflows should remain usable at supported viewport sizes.

### 10. Accessibility regression
UI refactoring should not remove existing:
- labels,
- keyboard support,
- focus indicators,
- semantic roles.

## AI Agent Rule
Do not optimize visual appearance by removing necessary labels, states, warnings, or accessibility behavior.
