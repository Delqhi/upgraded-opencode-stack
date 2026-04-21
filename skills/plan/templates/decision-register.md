# Decision Register

> Log all significant decisions made during planning and execution.
> Each decision includes rationale, alternatives considered, and owner.
> This creates an audit trail for future reference and post-mortems.

---

## Decision Log

| ID | Decision | Rationale | Alternatives Considered | Decided By | Date | Status | Revisit Date |
|----|----------|-----------|------------------------|------------|------|--------|-------------|
| D1 | [What was decided] | [Why this choice] | [What else was considered] | [role/name] | YYYY-MM-DD | approved/rejected/deferred | YYYY-MM-DD or N/A |
| D2 | | | | | | | |

---

## Decision Details

### D1: [Decision Title]

**Context:**
[What situation prompted this decision?]

**Decision:**
[What was decided?]

**Rationale:**
[Why was this choice made?]

**Alternatives Considered:**
1. [Alternative 1] - [Why rejected]
2. [Alternative 2] - [Why rejected]

**Impact:**
[What does this decision affect?]

**Risks:**
[What risks does this decision introduce?]

**Revisit Criteria:**
[Under what conditions should this decision be revisited?]

---

## Guidelines

1. **Log every decision** that affects scope, timeline, architecture, or user experience
2. **Include alternatives** even if rejected - explains the thinking process
3. **Set revisit dates** for decisions that may need updating
4. **Link to issues/PRs** when decisions are implemented
5. **Update status** when decision is implemented, superseded, or reversed

---

## Decision Categories

| Category | Examples | Approval Required |
|----------|----------|------------------|
| **Architecture** | Tech stack, patterns, dependencies | Tech Lead + EM |
| **Scope** | Feature inclusion/exclusion, priority changes | Product Owner |
| **Timeline** | Deadline changes, phase reordering | EM + Stakeholders |
| **Quality** | Test coverage targets, performance thresholds | Tech Lead |
| **Process** | Workflow changes, tool adoption | Team consensus |
