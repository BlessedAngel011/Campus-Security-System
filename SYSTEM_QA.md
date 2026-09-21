# UFH Campus Security — Integrated UI & Workflow QA

This build uses the existing polished role dashboards as the visual reference and adds a shared application shell for the newer operational modules.

## Unified modules
- Notifications
- Campus Map / GIS
- Emergency Control
- Officer Duty & GPS
- Admin Analytics
- Audit Logs
- Profile editor
- Incident evidence

These modules now share the same UFH navy/blue/gold visual language, branding, responsive navigation, card system, badges, buttons, spacing and mobile bottom navigation.

## Workflow protections added
- Student map is scoped to that student's own incidents and emergencies.
- Assigning an emergency updates the linked incident to In Progress.
- Student and assigned officer both receive an in-app assignment notification.
- Only the assigned officer can move an emergency to Responding or Resolved.
- Resolving an emergency resolves its linked incident and returns the officer to Available.
- Evidence access remains scoped by role/incident ownership.

## Intended end-to-end flows
1. Student report → priority → evidence → Security → status → Student notification/email → audit/analytics.
2. Student SOS → GPS/manual fallback → ACTIVE → Security → officer assignment → ASSIGNED → RESPONDING → RESOLVED → Student notification → linked incident sync → officer AVAILABLE.
3. Admin → users → analytics/audit/map without receiving operational emergency alerts by default.
