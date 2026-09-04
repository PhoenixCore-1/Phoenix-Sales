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

## Development

Python 3.11+ is required. The initial test dependency is pytest 8.x.

The repository is built incrementally. Business domains are added only after the module foundation and integration contracts are verified.
