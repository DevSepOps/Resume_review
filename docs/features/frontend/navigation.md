# Navigation (Frontend Feature Doc)

## 1. Overview
Role-aware bottom navigation pill (`AnimatedNav`) plus route guards. Adapted from the `animated_nav` prototype and ported to Flet 0.28.3.

## 2. UI/UX Flow
Gradient pill (max 590 px, `page.width - 32` on small screens). Hover (desktop): the icon lifts out and the label slides in.
The **active item always shows its label and a soft highlight**, so touch devices (no hover) see the current location.
Click/tap navigates; "Logout" is an action item.

| Role | Items |
|------|-------|
| candidate | Resumes, Upload, Logout |
| expert | + Review |
| admin | + Review, Users, Stats |

## 3. Data Flow
App layer builds `NavEntry(key, label, icon, route)` from `navigation.nav_entries_for(role)`; `AnimatedNav` calls `on_select(entry)`; `SessionApp._on_nav_select` does `page.go(route)` or logout. `shared` never imports features.

## 4. Components
`shared/components/animated_nav.py`: `NavEntry`, `NavItem` (Container with `ink=True`, `on_click`, `on_hover`, `tooltip`), `AnimatedNav`. Icons are `ft.Icons.*` constants.

## 5. Services/API
None. Logout calls `AuthService.logout`.

## 6. Hooks
Resize: `page.on_resized` -> `AnimatedNav.set_page_width`.

## 7. State Logic
Active item is a constructor argument (the view is rebuilt per route). Hover state is local to each `NavItem`.

## 8. Edge Cases
Unknown or forbidden routes redirect (`navigation.resolve`); labels are short (max ~7 chars) and ellipsised; width never below 200 px.

## 9. Security Considerations
Guards are UI conveniences; the backend enforces authorisation. Nav entries for a role are derived from the server-provided role.

## 10. Testing Strategy
`test_navigation.py` (guards, entries per role), `test_components.py` (width, active state, click dispatch).

## 11. Future Improvements
Verify keyboard focus ring and Enter/Space activation in a real browser (Flet renders `Container(ink=True)` with an InkWell, which is focusable by Flutter convention, but this was not browser-tested). Badge counts.
