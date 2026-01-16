# Roadmap: NetBox Automation

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped)
- ✅ **v1.1 Test Infrastructure** - Phases 5-8 (shipped)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

<details>
<summary>✅ v1.0 MVP (Phases 1-4) - SHIPPED</summary>

Phases 1-4 delivered discovery, correlation, web review, NetBox/DNS push.
See archived milestone documentation.

</details>

### ✅ v1.1 Test Infrastructure (Complete)

**Milestone Goal:** Comprehensive test coverage as safety net before future feature development.

- [x] **Phase 5: Unit Tests** - Core module test coverage
- [x] **Phase 6: Integration & E2E Tests** - External mocks and CLI workflows
- [x] **Phase 7: CI Pipeline** - GitHub Actions automation
- [x] **Phase 8: Fix mypy type errors for CI** - Resolve type checking issues

## Phase Details

### Phase 5: Unit Tests
**Goal**: Core modules have comprehensive unit test coverage
**Depends on**: Nothing (first phase of v1.1)
**Requirements**: UNIT-01, UNIT-02, UNIT-03, UNIT-04, UNIT-05, UNIT-06, UNIT-07, UNIT-08, UNIT-09, UNIT-10
**Success Criteria** (what must be TRUE):
  1. `pytest tests/unit/` runs without errors
  2. MAC correlation tests verify host merging logic
  3. Status transition tests enforce workflow constraints
  4. Config tests validate YAML loading and env var overrides
**Research**: Unlikely (pytest is standard, patterns established)
**Plans**: 4 (05-01 through 05-04)

### Phase 6: Integration & E2E Tests
**Goal**: External API mocks and CLI workflow tests complete
**Depends on**: Phase 5
**Requirements**: INTG-01, INTG-02, INTG-03, INTG-04, INTG-05, INTG-06, E2E-01, E2E-02, E2E-03, E2E-04
**Success Criteria** (what must be TRUE):
  1. `pytest tests/integration/` runs with mocked external services
  2. `pytest tests/e2e/` runs CLI commands against fixture data
  3. No real API calls made during test runs (all mocked)
**Research**: Unlikely (mocking patterns well-known)
**Plans**: 4 (06-01 through 06-04)

### Phase 7: CI Pipeline
**Goal**: GitHub Actions runs full test suite on push/PR
**Depends on**: Phase 6
**Requirements**: CI-01, CI-02, CI-03, CI-04
**Success Criteria** (what must be TRUE):
  1. GitHub Actions workflow passes on push/PR
  2. `make ci` equivalent runs in CI (lint + type + test)
  3. Tests run on Python 3.11 and 3.12
**Research**: Unlikely (GitHub Actions for Python is well-documented)
**Plans**: 1 (07-01)

### Phase 8: Fix mypy type errors for CI
**Goal**: Resolve all mypy type checking errors so CI passes
**Depends on**: Phase 7
**Requirements**: TYPE-01, TYPE-02
**Success Criteria** (what must be TRUE):
  1. `make type` passes with zero errors
  2. CI pipeline passes type checking step
**Research**: None (errors already diagnosed)
**Plans**: 2 (08-01, 08-02)

## Progress

**Execution Order:**
Phases execute in numeric order: 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. Unit Tests | 4/4 | Complete | 2026-01-16 |
| 6. Integration & E2E | 4/4 | Complete | 2026-01-16 |
| 7. CI Pipeline | 1/1 | Complete | 2026-01-16 |
| 8. Fix mypy type errors | 2/2 | Complete | 2026-01-16 |
