# features/workspace

UI and client-side logic for the Workspace object - the container every
Goal creates, holding its Tasks, Documents, Conversations, Memories, AI
Plans, Progress, and Agents (see `docs/vision.md` "Primary Object").

Implemented (Sprint 1 Day 3): `WorkspaceShell` (nav + title bar),
`WorkspaceContext` (shared data fetch), `OverviewSection`,
`PlaceholderSection` (shared by Tasks/Planner/Knowledge/Timeline/Chat
until those are real). Workspace _creation_ has no dedicated UI - it
happens automatically when a Goal is created (see
`features/dashboard/CreateGoalModal.tsx`).
