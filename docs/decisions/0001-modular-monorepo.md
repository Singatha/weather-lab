# ADR 0001: Modular monorepo

- Status: Accepted
- Date: 2026-11-07

## Context

The application has one browser client and one backend service that evolve
together. The learning goals require clear backend boundaries without the
operational burden of microservices.

## Decision

Keep the React and FastAPI applications in one repository and implement the
backend as a modular monolith. Add modules when a phase introduces behavior,
not as empty placeholders.

## Alternatives

Separate repositories provide independent release histories but add duplicated
automation and coordination. Microservices increase deployment and reliability
complexity without a present scaling or ownership need.

## Consequences

Cross-application changes can be reviewed atomically and local setup remains
simple. CI still treats web and API checks as separate jobs, preserving useful
boundaries and fast feedback.

