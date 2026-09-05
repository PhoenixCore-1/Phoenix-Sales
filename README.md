# Phoenix Sales V1.0

Phoenix Sales is a modular business application running on Phoenix Core V2.0.

## Purpose

Sales owns the commercial lifecycle from opportunity through quote and sales order, including solution definition, pricing and margin, pipeline and forecasting, competitor pricing intelligence, basic commissions, returns/cancellations/credit commercial workflow, sales reporting, and Sales AI.

## Architecture

Phoenix Sales is a business module, not a standalone platform. It integrates with Phoenix Core through defined module contracts and does not bypass Core security, tenancy, permissions, audit, licensing, or integration boundaries.

## V1.0 Principles

- Manufacturer-agnostic
- Tenant-aware
- Permission-controlled
- Auditable
- API/contract based
- No direct access to another module's private persistence
- Sage remains the financial/accounting authority
- AI assists within explicit authority boundaries
- Customer/account visibility is resolved by Phoenix Core access scope, not by Sales-specific territory security

## Core Access Scope

Phoenix Core owns the platform-wide organization and access model, including organizations, regions, territories, teams, primary/secondary assignments, and resource visibility. Sales receives the Core-resolved scope through `RequestContext.access_scope` and uses it to determine which Sales resources are visible to the current user.

Sales must not independently calculate organizational hierarchy, expand assignments, or create a parallel customer-visibility model. Core establishes the accessible resource scope; Sales then applies its own domain permissions and commercial business rules.

This same contract is intended to be reusable by CRM 360, Inventory 360, Projects, and other Phoenix business modules.

## Development

Python 3.11+ is required. The initial test dependency is pytest 8.x.

The repository is built incrementally. Business domains are added only after the module foundation and integration contracts are verified.
