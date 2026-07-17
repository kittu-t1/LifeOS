# services

Client-side API service layer - typed wrappers around backend endpoints
(goals, workspaces, plans, approvals, memory), building on the pattern
already established in `lib/api.ts`. Keeps data-fetching logic out of
components.

`goals.ts` and `workspaces.ts` are implemented (Sprint 1 Day 3), built on
the shared `apiFetch` helper in `lib/api.ts`.
