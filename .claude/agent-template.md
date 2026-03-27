---
# AGENT TEMPLATE — copy and fill in
name: <agent-name>
description: >
  <One-sentence role>. <Key input>. <Key output>.
  <Model justification or special capability note>.
tools: Read, Write, Glob, Grep   # Add Bash only if scripts needed
model: opus                       # opus / sonnet / haiku / inherit
skills:                           # Only if skill is small (<200 lines)
  - <skill-name>
---

# <Agent Name>

## Role

<What this agent does in 2-3 sentences — English>
<What it does NOT do — boundaries>

---

## Input

| Field | Source | Required |
|-------|--------|----------|
| `<field>` | `<path>` | ✅ |

---

## Output

| Field | Destination | Format |
|-------|-------------|--------|
| `<field>` | `<path>` | YAML delta |

---

## Execution Flow

```
STEP 0. Prerequisites
→ Read version_manifest.yaml → RUN_ID
→ Verify required input files exist

STEP 1. <Main work>
→ <Substep>

STEP 2. Save output
→ Save to: <path>
```

---

## Output Format

```yaml
---
shot_id: {N}
<delta_field_1>: |
  <value>
<delta_field_2>: "<value>"
---
```

---

## Self-Reflection

Before finalizing output, verify:
- [ ] All required output fields present
- [ ] Files saved to correct paths
- [ ] <Agent-specific check 1>
- [ ] <Agent-specific check 2>
- [ ] No prohibited actions taken

Report: "✅ Self-check passed" or list issues found and corrected.

---

## Prohibitions

- ❌ <specific prohibition>
- ❌ <specific prohibition>

---

## Completion Report

```
✋ [{AGENT_NAME} 완료]
저장: <path>
<Key stats>
```
