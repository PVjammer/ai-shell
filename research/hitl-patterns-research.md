# Human-in-the-Loop (HITL) Patterns for AI Agents in Shell/System Automation

## Research Report - October 9, 2025

This document synthesizes research on human-in-the-loop patterns, safety mechanisms, and best practices for AI agents operating in shell and system automation contexts.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [HITL Design Patterns](#hitl-design-patterns)
3. [Safety Mechanisms](#safety-mechanisms)
4. [Permission Models](#permission-models)
5. [User Experience Best Practices](#user-experience-best-practices)
6. [Automation vs Control Balance](#automation-vs-control-balance)
7. [Audit and Rollback Mechanisms](#audit-and-rollback-mechanisms)
8. [Command Risk Classification](#command-risk-classification)
9. [Implementation Recommendations](#implementation-recommendations)
10. [Real-World Examples](#real-world-examples)
11. [References](#references)

---

## Executive Summary

Human-in-the-loop is a fundamental pattern for building trustworthy AI agents that ensures LLMs stay within safe operational boundaries. Research shows a clear consensus: **AI agents should not have blanket permissions** and **sensitive actions require explicit human confirmation**.

Key findings:
- Multi-layered safety approach: Model → Safety System → Application → User Experience
- Four core HITL patterns: Approve/Reject, Edit State, Review Tools, Validate Input
- Context-aware permissions outperform static whitelists/blacklists
- Dry-run modes and comprehensive audit logging are essential
- UX design critical: confirmation dialogs should be non-intrusive yet effective

---

## HITL Design Patterns

### 1. Core HITL Patterns

Based on LangGraph and modern agent frameworks, four primary patterns emerge:

#### A. Approve or Reject
**Purpose**: Pause before critical steps (API calls, destructive operations)

**Implementation**:
```python
def human_approval(state: State) -> Command:
    is_approved = interrupt({
        "question": "Execute this command?",
        "command": state["proposed_command"],
        "risk_level": state["risk_assessment"]
    })
    if is_approved:
        return Command(goto="execute_node")
    else:
        return Command(goto="cancel_node")
```

**When to use**:
- Destructive file operations (rm, DROP, etc.)
- Network operations affecting production systems
- Financial transactions
- Mass email operations
- Security configuration changes

#### B. Edit Graph State
**Purpose**: Allow humans to review and modify proposed actions

**Implementation**:
- Pause execution
- Present proposed state/command
- Allow editing before execution
- Resume with modified state

**When to use**:
- Command has valid intent but parameters need adjustment
- User wants to refine AI's proposal
- Multiple similar operations where first needs review

#### C. Review Tool Calls
**Purpose**: Inspect tool calls before execution

**Implementation**:
- Display: tool name, parameters, expected outcome
- Allow approval, rejection, or modification
- Log decision for audit

**When to use**:
- Multiple tools being chained together
- Tools with side effects
- Operations on sensitive resources

#### D. Validate Human Input
**Purpose**: Ensure human-provided data meets requirements before proceeding

**Implementation**:
- Request specific input format
- Validate against schema/rules
- Re-prompt if invalid

**When to use**:
- Credentials or sensitive data needed
- Disambiguation required
- Policy requires explicit confirmation phrases

### 2. Extended Patterns

#### E. Human-as-a-Tool
**Concept**: Treat human reviewers as another callable tool in the agent's toolkit

**Benefits**:
- Consistent interface for agent
- Can route uncertain decisions automatically
- Supports asynchronous workflows

#### F. Fallback Escalation
**Concept**: Automatically route complex/high-risk tasks to humans

**Triggers**:
- Confidence score below threshold
- Risk assessment exceeds policy limit
- Novel situation not covered by training
- Explicit policy requirement

---

## Safety Mechanisms

### 1. Multi-Layer Safety Framework

Based on Microsoft/OpenAI research, implement safety at four layers:

#### Layer 1: Model Level
- Fine-tuning for safety alignment
- Constitutional AI principles
- Output filtering

#### Layer 2: Safety System Level
- Content filters
- Policy enforcement engines
- Real-time monitoring

#### Layer 3: Application Level
- Prompt engineering with safety instructions
- Meta-prompts that reinforce boundaries
- Output validation

#### Layer 4: User Experience Level
- Clear indication of AI vs human actions
- Transparent decision-making process
- Easy intervention mechanisms

### 2. Operational Control Features

#### A. Interruptibility
**Requirement**: Users must be able to gracefully interrupt operations at any time

**Implementation**:
```python
class InterruptibleOperation:
    def __init__(self):
        self.interrupt_flag = threading.Event()

    def check_interrupt(self):
        if self.interrupt_flag.is_set():
            raise InterruptedException("Operation cancelled by user")

    def execute_with_checkpoints(self, operations):
        for op in operations:
            self.check_interrupt()
            op.execute()
```

#### B. Limited Powers (Principle of Least Privilege)
- Agent powers must align with intended purpose
- Limit actions and resource access
- No blanket sudo/admin access
- Resource-specific permissions

#### C. Observability
- Log all agent actions
- Where feasible, log planning/reasoning
- Provide insights into decision-making
- Support post-hoc analysis

#### D. Clear Oversight
- Every agent has defined controlling user(s)
- Delegation chain is explicit
- Accountability is traceable

#### E. Containment Mechanisms
- Sandboxing for testing
- Rollback capabilities
- Circuit breakers to halt cascading damage
- Rate limiting and quotas

### 3. Security Best Practices (OWASP Top 10 for LLM Applications)

1. **Prompt Injection Defenses**: Validate and sanitize inputs
2. **Output Validation**: Never execute commands without validation
3. **Plugin Security**: Vet tools/functions before making available
4. **Least Privilege**: Minimal necessary permissions
5. **Over-Reliance Mitigation**: Clear limitations communication

---

## Permission Models

### 1. Evolution: Static to Dynamic Authorization

#### Traditional Approach (Insufficient for AI Agents)
- Static whitelists/blacklists
- Role-Based Access Control (RBAC) alone
- Coarse-grained permissions

**Why insufficient**: AI agents dynamically create workflows and traverse systems unpredictably

#### Modern Approach (Recommended)
- Policy-Based Access Control (PBAC)
- Attribute-Based Access Control (ABAC)
- Relationship-Based Access Control (ReBAC)
- Context-Aware Authorization

### 2. Fine-Grained vs Coarse-Grained Permissions

#### Coarse-Grained
**Scope**: Broad categories (e.g., "can execute shell commands")

**Pros**:
- Simple to implement
- Easy to understand
- Low overhead

**Cons**:
- All-or-nothing approach
- Difficult to audit specific actions
- Overly permissive

**Use case**: Early prototypes, fully trusted environments

#### Fine-Grained
**Scope**: Specific actions on specific resources

**Example**:
```yaml
permissions:
  filesystem:
    read:
      - /home/user/documents/*
      - /tmp/*
    write:
      - /home/user/documents/*
    delete:
      - /tmp/*
  network:
    allowed_domains:
      - api.example.com
      - *.trusted-service.com
  database:
    read:
      - public_data
    write: []
```

**Pros**:
- Precise control
- Better audit trail
- Limits blast radius
- Supports compliance

**Cons**:
- Complex to configure
- Higher overhead
- Requires careful design

**Use case**: Production systems, regulated industries, multi-tenant environments

### 3. Context-Aware Permissions

**Definition**: Authorization decisions based on runtime context

**Context factors**:
- User identity and role
- Time of day/day of week
- Location (IP address, geographic)
- Device security posture
- Resource sensitivity
- Operation risk level
- Recent activity patterns

**Example**:
```python
def check_permission(user, action, resource, context):
    policy = load_policy(resource)

    # Base permission check
    if not user.has_role(policy.required_role):
        return False

    # Context-aware checks
    if action.risk_level == "high":
        if not context.is_business_hours():
            return False
        if not context.is_secure_network():
            return False
        if context.has_recent_anomalies(user):
            return False

    # Check if human approval already obtained
    if action.requires_approval:
        return context.has_approval(action.approval_token)

    return True
```

**Benefits**:
- Adaptive security
- Reduces false positives
- Supports zero-trust architecture
- Better than static rules

### 4. Trusted Commands and Approval Policies

#### Trust Levels
Define commands by trust level:

**Level 0 - Always Allowed (No confirmation needed)**
- Pure read operations: ls, cat, pwd, echo, date
- Status checks: git status, df -h
- Non-destructive queries: grep (read-only), find

**Level 1 - Low Risk (Optional confirmation)**
- File creation in safe directories
- Append operations
- Non-privileged package installs

**Level 2 - Medium Risk (Confirmation recommended)**
- File modifications
- Network operations
- Write operations in working directories
- git commit, git push

**Level 3 - High Risk (Confirmation required)**
- Destructive file operations: rm -rf, mv to overwrite
- Database modifications: DROP, DELETE, UPDATE
- System configuration changes
- Privilege escalation: sudo
- Process termination: kill -9

**Level 4 - Critical (Requires typed confirmation)**
- System-wide destructive operations: rm -rf /
- Production database operations
- Infrastructure destruction: terraform destroy
- Security credential changes

#### Implementation Pattern

```python
class CommandTrustPolicy:
    def __init__(self):
        self.trust_levels = {
            0: {"commands": ["ls", "cat", "pwd"], "require_confirmation": False},
            1: {"commands": ["touch", "mkdir"], "require_confirmation": False},
            2: {"commands": ["git commit", "cp"], "require_confirmation": True},
            3: {"commands": ["rm", "drop", "delete"], "require_confirmation": True},
            4: {"commands": ["sudo rm -rf /"], "require_typed_confirmation": True}
        }

    def evaluate_command(self, command_str):
        # Parse command
        # Check against trust levels
        # Return required approval type
        pass
```

### 5. Permission Delegation Model

**Agent Identity Pattern** (Recommended):
Treat the AI agent as its own independent client with explicit OAuth credentials

```
User → Delegates Limited Permissions → AI Agent (separate identity)
                                          ↓
                                    Explicit, Auditable Access
```

**Benefits**:
- Clear audit trail
- Agent permissions can be revoked independently
- Supports principle of least privilege
- Enables per-agent policies

**Alternative: User Impersonation** (Not Recommended):
Agent acts with full user permissions

**Drawbacks**:
- Overly permissive
- Difficult to audit what was agent vs user
- Violates least privilege
- Risky if agent is compromised

---

## User Experience Best Practices

### 1. When to Use Confirmation Dialogs

#### Use confirmation dialogs for:
- Actions with serious consequences
- Irreversible operations (data deletion, account removal)
- Security-sensitive changes
- Financial transactions
- Operations affecting multiple resources

#### Avoid confirmation dialogs for:
- Actions lacking serious consequences
- Reversible operations with undo capability
- Frequent routine operations
- User preference changes

**Key principle**: "Confirmation dialogs should be used exclusively for actions with substantial implications"

### 2. Dialog Design Principles

#### A. Clear, Specific Language
**Bad**: "Are you sure?"
**Good**: "Delete 47 files from /home/user/documents?"

**Bad**: Yes/No buttons
**Good**: Action-specific buttons ("Delete", "Cancel")

#### B. Provide Context
Include in confirmation:
- What will be affected
- Scope of impact (number of files, resources)
- Irreversibility warning if applicable
- Risk level indicator

Example:
```
┌─────────────────────────────────────────────────┐
│  Confirm Destructive Operation                  │
├─────────────────────────────────────────────────┤
│  Command: rm -rf /home/user/old_project/        │
│  Risk Level: HIGH                               │
│                                                 │
│  This will permanently delete:                  │
│  • 1,243 files                                  │
│  • 47 directories                               │
│  • Total size: 2.3 GB                          │
│                                                 │
│  This action cannot be undone.                  │
│                                                 │
│  [ Cancel ]  [ Delete Permanently ]            │
└─────────────────────────────────────────────────┘
```

#### C. Non-Intrusive Design
- Strategic placement: noticeable but not blocking unnecessarily
- Appropriate modal type:
  - **Modal dialogs**: For critical, must-acknowledge operations
  - **Non-modal notifications**: For less critical confirmations
- Avoid confirmation fatigue through smart risk assessment

#### D. Graduated Confirmation Levels

**Level 1: Inline confirmation**
```
> Execute: git push origin main
Press Enter to confirm, Ctrl+C to cancel...
```

**Level 2: Simple Yes/No**
```
> Execute: rm large_file.zip (1.2 GB)
Confirm? [y/N]:
```

**Level 3: Action button dialog**
(See example above)

**Level 4: Typed confirmation**
```
> Execute: DROP DATABASE production
This will permanently delete the entire database.
Type 'permanently delete' to confirm:
```

### 3. Batch Operations UX

#### Challenge
How to handle confirmation for multiple operations without overwhelming the user?

#### Patterns

**A. Summary Confirmation**
Present aggregate summary, confirm once:
```
About to execute 5 commands:
1. Create directory: /projects/new_app
2. Copy files: src/* → /projects/new_app/
3. Initialize git repository
4. Install dependencies (npm install)
5. Start development server

Proceed with all operations? [Y/n]:
```

**B. Risk-Based Filtering**
Auto-approve low-risk, confirm only high-risk:
```
Auto-approved (3 operations):
  ✓ ls -la
  ✓ cat config.json
  ✓ pwd

Require confirmation:
  ⚠ rm -rf /tmp/cache/* (HIGH RISK)
  Confirm deletion of 892 files? [y/N]:
```

**C. Interactive Review Mode**
Step through each operation:
```
Command 1 of 5:
  rm file1.txt (LOW RISK)

[A]pprove  [S]kip  [R]eview remaining  [C]ancel all
```

**D. Post-Execution Summary**
For approved batch operations, show results:
```
Batch execution complete:
  ✓ 4 succeeded
  ✗ 1 failed: permission denied on file3.txt
  ⊘ 2 skipped

[View details]  [Retry failed]  [Close]
```

### 4. Approval Workflow Timing

#### Synchronous Approval (Blocking)
**Use when**:
- Real-time decision needed
- User is actively monitoring
- Quick response expected

**Implementation**: Block execution, wait for user input

#### Asynchronous Approval (Non-blocking)
**Use when**:
- Long-running operations
- User may not be present
- Review can happen separately

**Implementation**:
1. Queue operation
2. Notify user (email, Slack, etc.)
3. Execute upon approval
4. Timeout policy if no response

Example:
```
Operation queued for approval:
  Command: terraform apply (affects 42 resources)
  Approval requested via: slack #ops-team
  Timeout: 4 hours

View queue: ai-shell pending
```

### 5. Trust Building and Learning

#### Adaptive Confirmation
Over time, system learns user preferences:

```python
class AdaptiveApprovalSystem:
    def __init__(self):
        self.user_history = UserApprovalHistory()

    def should_confirm(self, operation):
        base_risk = operation.risk_level

        # Check if user has approved similar operations
        similar_ops = self.user_history.find_similar(operation)
        if similar_ops.approval_rate > 0.95 and similar_ops.count > 10:
            # User consistently approves this type
            # Offer to skip confirmation
            return self.offer_trust_option(operation)

        return base_risk >= self.user_history.confirmation_threshold
```

**User control**:
```
You've approved "npm install" 15 times without changes.
Would you like to:
  1. Always allow "npm install" without confirmation
  2. Keep asking each time
  3. Ask only if package.json changed

Choice [1/2/3]:
```

---

## Automation vs Control Balance

### 1. The Spectrum

```
Full Manual ←─────────────────────────→ Full Automation
           ↑                         ↑                ↑
     Human-in-Loop          Human-on-Loop    Fully Autonomous
```

### 2. Human-in-the-Loop (HITL)
**Definition**: Human approval required for specific actions

**Characteristics**:
- Human is part of the execution path
- Operations pause for approval
- Explicit confirmation needed

**Use cases**:
- New/untrusted agents
- High-stakes environments
- Learning/training phase
- Regulated industries

**Trade-offs**:
- Pro: Maximum safety and control
- Con: Reduced automation benefit, potential bottleneck

### 3. Human-on-the-Loop (HOTL)
**Definition**: Human monitors but doesn't block execution; can intervene if needed

**Characteristics**:
- Operations proceed automatically
- Human receives notifications/summaries
- Can halt or rollback if problems detected
- Periodic review points

**Use cases**:
- Mature, trusted agents
- Operations with good rollback capabilities
- Monitoring/alerting scenarios
- Non-critical systems

**Trade-offs**:
- Pro: Better automation, less friction
- Con: Requires trust, good monitoring, rollback capabilities

**Implementation**:
```python
class HumanOnLoop:
    def execute_with_monitoring(self, operation):
        # Notify human operation is starting
        self.notify_start(operation)

        # Execute with ability to halt
        result = operation.execute_interruptible()

        # Notify completion
        self.notify_complete(operation, result)

        # Human has window to review and rollback
        self.enable_rollback_window(operation, duration=300)
```

### 4. Fully Autonomous
**Definition**: Agent operates independently, human reviews only periodically or on exception

**Use cases**:
- Highly trusted, well-tested operations
- Read-only operations
- Monitoring and alerting
- Low-risk automation

### 5. Choosing the Right Level

Decision matrix:

| Factor | Full HITL | Selective HITL | HOTL | Autonomous |
|--------|-----------|----------------|------|------------|
| Operation Risk | Critical | High | Medium | Low |
| Reversibility | Irreversible | Difficult | Easy | Easy |
| Agent Trust Level | New/Untested | Learning | Proven | Highly Trusted |
| User Availability | Always present | Usually present | Periodic | Rarely needed |
| Operation Frequency | Rare | Occasional | Frequent | Continuous |
| Compliance Requirements | Strict | Moderate | Flexible | None |

### 6. Progressive Trust Model

**Concept**: Start restrictive, gradually relax based on demonstrated reliability

**Phases**:

**Phase 1: Training Wheels (Week 1-2)**
- All operations require confirmation
- Detailed explanations provided
- Extensive logging
- User builds mental model

**Phase 2: Selective Autonomy (Week 3-4)**
- Low-risk operations auto-approved
- Medium-risk require confirmation
- System learns user preferences
- Trust metrics collected

**Phase 3: Monitored Autonomy (Week 5+)**
- Most operations auto-approved
- Only high-risk require confirmation
- Human-on-loop monitoring
- Periodic review of agent actions

**Phase 4: Mature Trust (Month 3+)**
- Agent operates with minimal intervention
- User defines policy boundaries
- Exception-based review
- Continuous trust validation

**Implementation**:
```python
class ProgressiveTrustSystem:
    def __init__(self, user):
        self.user = user
        self.trust_level = self.calculate_trust_level()

    def calculate_trust_level(self):
        metrics = {
            "days_active": self.user.days_since_first_use,
            "operations_executed": self.user.operation_count,
            "approval_rate": self.user.approval_rate,
            "error_rate": self.user.error_rate,
            "interventions": self.user.intervention_count
        }

        # Trust level: 0 (no trust) to 100 (full trust)
        if metrics["days_active"] < 7:
            return min(20, metrics["days_active"] * 2)

        if metrics["operations_executed"] < 50:
            return min(40, 20 + metrics["operations_executed"] / 2)

        # Mature user
        base_trust = 60
        if metrics["approval_rate"] > 0.9:
            base_trust += 15
        if metrics["error_rate"] < 0.05:
            base_trust += 15
        if metrics["interventions"] < 5:
            base_trust += 10

        return min(100, base_trust)

    def get_confirmation_policy(self):
        trust = self.trust_level

        if trust < 30:
            return "confirm_all"
        elif trust < 60:
            return "confirm_medium_and_high_risk"
        elif trust < 80:
            return "confirm_high_risk_only"
        else:
            return "confirm_critical_only"
```

---

## Audit and Rollback Mechanisms

### 1. Comprehensive Audit Logging

#### What to Log

**Minimal (Required)**:
- Timestamp
- User/agent identity
- Command/operation requested
- Approval status (approved/rejected/timeout)
- Approver identity (if different from requestor)
- Execution outcome (success/failure)

**Recommended (Additional)**:
- Agent reasoning/justification
- Risk assessment score
- Context at time of operation
- Resources affected
- Before/after state (for modifications)
- Duration
- Error messages

**Advanced (Security/Compliance)**:
- Full command with arguments
- Environment variables
- Working directory
- Parent process
- Network context (IP, location)
- Device information

#### Log Format

**Structured JSON**:
```json
{
  "timestamp": "2025-10-09T14:32:15.123Z",
  "event_type": "command_execution",
  "user_id": "user@example.com",
  "agent_id": "ai-shell-agent-001",
  "session_id": "sess_abc123",
  "command": {
    "raw": "rm -rf /tmp/old_cache",
    "parsed": {
      "executable": "rm",
      "args": ["-rf", "/tmp/old_cache"],
      "risk_level": "high"
    }
  },
  "approval": {
    "required": true,
    "status": "approved",
    "approver": "user@example.com",
    "method": "interactive_prompt",
    "duration_ms": 2341
  },
  "execution": {
    "status": "success",
    "exit_code": 0,
    "duration_ms": 145,
    "files_affected": 234,
    "bytes_deleted": 18393029
  },
  "context": {
    "working_directory": "/home/user/projects",
    "git_branch": "main",
    "environment": "development"
  },
  "agent_reasoning": "User requested cleanup of old cache files. Operation assessed as safe in /tmp directory."
}
```

#### Audit Log Storage

**Requirements**:
- Immutable (append-only)
- Tamper-evident
- Searchable
- Long retention period
- Access-controlled

**Options**:
1. **Local files** (simple, good for development)
2. **Database** (structured queries, good for single-machine)
3. **Centralized logging service** (Elasticsearch, Splunk, CloudWatch)
4. **Blockchain/distributed ledger** (maximum tamper-evidence)

### 2. Dry-Run Mode

**Purpose**: Simulate operations without executing them

**Benefits**:
- Preview effects before committing
- Test configurations safely
- Build confidence in agent behavior
- Training and demonstration

**Implementation patterns**:

**A. Command-line flag**:
```bash
ai-shell --dry-run "cleanup old log files"
```

**B. Pre-execution preview**:
```
Agent proposes:
  rm /var/log/old/*.log (5 files, 12 MB)
  gzip /var/log/app.log (1 file, 45 MB)

Options:
  [E]xecute  [D]ry-run first  [C]ancel

Choice [E/D/C]:
```

**C. Terraform-style plan**:
```
Execution Plan:

Resources to be modified: 3
  ~ file: /home/user/config.json
      - old_value: "debug"
      + new_value: "info"

  + file: /home/user/new_script.sh

  - file: /home/user/deprecated.txt

Approve plan? [y/N]:
```

**Implementation**:
```python
class DryRunExecutor:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.planned_actions = []

    def execute(self, command):
        if self.dry_run:
            # Simulate execution
            effect = self.simulate(command)
            self.planned_actions.append({
                "command": command,
                "simulated_effect": effect
            })
            return effect
        else:
            # Actually execute
            return self.real_execute(command)

    def simulate(self, command):
        # Analyze command and predict effects
        # Without actually executing
        return {
            "would_modify": ["/file1.txt", "/file2.txt"],
            "would_delete": ["/old_file.txt"],
            "estimated_time": "2 seconds"
        }

    def show_plan(self):
        print("Dry-run results:")
        for action in self.planned_actions:
            print(f"  {action['command']}")
            print(f"    Effects: {action['simulated_effect']}")
```

### 3. Undo Mechanisms

#### A. Command History with Rollback

**Simple approach**: Maintain executed command history with ability to reverse

```python
class CommandHistory:
    def __init__(self):
        self.history = []

    def execute(self, command):
        # Execute command
        result = command.execute()

        # Store with undo capability
        self.history.append({
            "command": command,
            "undo_command": command.get_inverse(),
            "timestamp": datetime.now(),
            "result": result
        })

        return result

    def undo_last(self):
        if not self.history:
            raise Exception("No commands to undo")

        last = self.history.pop()
        if last["undo_command"]:
            return last["undo_command"].execute()
        else:
            raise Exception("Command is not reversible")
```

**Example**:
```
> ai-shell "create new python project"
  Created directory: /home/user/new_project/
  Created files: setup.py, README.md, main.py

> ai-shell undo
  Reverting last operation...
  Removed directory: /home/user/new_project/
  Done.
```

#### B. State Snapshots (Memento Pattern)

**For complex state changes**: Save full state before operations

```python
class StateSnapshot:
    def __init__(self):
        self.snapshots = []

    def create_snapshot(self, label=None):
        snapshot = {
            "id": generate_id(),
            "label": label,
            "timestamp": datetime.now(),
            "filesystem_state": self.capture_filesystem(),
            "env_state": self.capture_environment(),
            "git_state": self.capture_git_state()
        }
        self.snapshots.append(snapshot)
        return snapshot["id"]

    def restore_snapshot(self, snapshot_id):
        snapshot = self.find_snapshot(snapshot_id)
        self.restore_filesystem(snapshot["filesystem_state"])
        self.restore_environment(snapshot["env_state"])
        self.restore_git_state(snapshot["git_state"])
```

**Use case**: Before major operations, auto-create snapshots

```
> ai-shell "refactor project structure"
  Creating snapshot... done (snapshot_7f3a9b)
  Refactoring...
    - Moving files
    - Updating imports
    - Running tests
  Complete.

  If issues arise: ai-shell restore snapshot_7f3a9b
```

#### C. Transaction-Based Rollback

**For database-like operations**: Use transaction semantics

```python
class TransactionalExecutor:
    def __init__(self):
        self.transaction_log = []

    def begin_transaction(self):
        self.current_transaction = Transaction()

    def execute(self, operation):
        # Execute within transaction
        self.current_transaction.add(operation)
        try:
            result = operation.execute()
            operation.mark_success()
            return result
        except Exception as e:
            # Auto-rollback on failure
            self.rollback_transaction()
            raise

    def commit_transaction(self):
        self.transaction_log.append(self.current_transaction)
        self.current_transaction = None

    def rollback_transaction(self):
        for operation in reversed(self.current_transaction.operations):
            operation.undo()
```

#### D. Git-Based Rollback

**For file operations**: Leverage git's built-in versioning

```bash
# Before operations, auto-commit current state
git add -A
git commit -m "Auto-save before AI operation: ${operation_description}"

# Mark with tag for easy restoration
git tag -a ai-checkpoint-$(date +%s) -m "Pre-operation checkpoint"

# If rollback needed
git reset --hard ai-checkpoint-<timestamp>
```

### 4. Rollback Capabilities by Operation Type

| Operation Type | Undo Difficulty | Recommended Approach |
|----------------|----------------|----------------------|
| File creation | Easy | Delete created files |
| File modification | Medium | Restore from backup/snapshot |
| File deletion | Hard | Restore from backup (if exists) |
| Database INSERT | Easy | DELETE with saved IDs |
| Database UPDATE | Medium | Restore old values (if saved) |
| Database DELETE | Hard | Restore from backup |
| API calls | Varies | Depends on API (compensating transaction) |
| Email sent | Impossible | No undo (require approval beforehand) |
| System config | Medium | Restore previous config file |
| Package install | Easy | Uninstall package |
| Git operations | Easy | Git revert/reset |

**Design principle**: Operations that are difficult/impossible to undo should require stronger confirmation

### 5. Rollback Window Pattern

**Concept**: After execution, provide time window for rollback before changes become permanent

```python
class DelayedCommitExecutor:
    def __init__(self, rollback_window=300):  # 5 minutes default
        self.rollback_window = rollback_window
        self.pending_commits = []

    def execute_with_delay(self, operation):
        # Execute operation but mark as "pending"
        result = operation.execute()

        # Add to pending commits
        commit_task = {
            "operation": operation,
            "result": result,
            "executed_at": datetime.now(),
            "commits_at": datetime.now() + timedelta(seconds=self.rollback_window),
            "undo_capability": operation.create_undo()
        }
        self.pending_commits.append(commit_task)

        # Schedule actual commit
        self.schedule_commit(commit_task)

        # Notify user
        print(f"Operation executed. You have {self.rollback_window}s to rollback.")
        print(f"To undo: ai-shell rollback {commit_task['id']}")

        return result
```

---

## Command Risk Classification

### 1. Risk Dimensions

Commands should be evaluated across multiple dimensions:

#### A. Operation Type
- **Read**: ls, cat, grep, find, stat
- **Write**: echo >, cp, mv, touch, mkdir
- **Modify**: sed -i, vim, nano (saving changes)
- **Delete**: rm, rmdir, DROP, DELETE
- **Execute**: exec, eval, source, sudo

#### B. Scope
- **Single file/resource**: rm file.txt
- **Directory**: rm -r directory/
- **Recursive**: rm -rf directory/
- **System-wide**: rm -rf /
- **Remote**: ssh commands, API calls

#### C. Reversibility
- **Fully reversible**: git reset, mv (can be moved back)
- **Reversible with tools**: rm (if backups exist, trash bin)
- **Difficult to reverse**: database UPDATE without WHERE clause
- **Irreversible**: DROP DATABASE, rm -rf without backups, sent emails

#### D. Privilege Level
- **User-level**: Operations in user's home directory
- **Shared resources**: Operations in shared directories
- **System-level**: Operations requiring sudo, affecting system files
- **Network-level**: Remote operations, API calls

### 2. Comprehensive Command Classification

#### Level 0: Safe (No confirmation)
**Characteristics**: Read-only, no side effects, local only

Commands:
```
ls, ll, la, pwd, whoami, date, cal, echo (to stdout), printf
cat, less, more, head, tail, bat, grep (no -i), find (read-only)
git status, git log, git diff, git branch (list only)
ps, top, htop, df, du, free, uptime, uname, hostname
env, export (query only), alias (query only), which, whereis
man, help, info, type, file, stat, wc, cksum, md5sum
```

**No confirmation needed**: Output doesn't modify system state

#### Level 1: Low Risk (Optional confirmation)
**Characteristics**: Write operations in safe locations (temp, home), easily reversible

Commands:
```
touch, mkdir, echo > (to new file)
cp (to non-existent destination), mv (rename only)
chmod +x (add execute permission)
git add, git reset (unstaged only)
cd, pushd, popd
nano, vim, emacs (for creating new files)
python script.py (read-only script), node script.js
npm install --save-dev (local project only)
```

**Confirmation**: Optional, can be skipped for trusted users

#### Level 2: Medium Risk (Confirmation recommended)
**Characteristics**: Modify existing files, local write operations, network reads

Commands:
```
cp (overwriting), mv (moving important files)
sed -i, awk (modifying files), perl -i
git commit, git stash
chmod, chown (on user files)
ln, ln -s (creating links)
tar -czf (create archive)
curl, wget (downloading files)
ssh (connection only, no commands)
docker build, docker run (without -v or privileged)
pip install, npm install (global), apt install (user packages)
```

**Confirmation**: Recommended, especially for first-time operations

#### Level 3: High Risk (Confirmation required)
**Characteristics**: Destructive, remote operations, privilege escalation

Commands:
```
rm, rm -r (directories)
rmdir (on non-empty with -f)
DROP (any database operation), DELETE, TRUNCATE, UPDATE without careful WHERE
git push (especially -f), git reset --hard, git clean -fd
chmod 777, chmod -R (recursive changes)
kill, pkill, killall
sudo (any command), su
ssh <command> (executing remote commands)
scp, rsync (with --delete)
docker rm, docker rmi, docker system prune
terraform apply, terraform destroy
kubectl delete, kubectl apply
systemctl stop, systemctl restart
iptables, ufw (firewall changes)
```

**Confirmation**: Required, show impact preview

#### Level 4: Critical (Typed confirmation required)
**Characteristics**: System-wide destruction, production changes, irreversible

Commands:
```
rm -rf / (or any system directory)
dd (disk operations), fdisk, mkfs (formatting)
DROP DATABASE (production), DROP TABLE (production)
git push -f origin main (force push to main/master)
terraform destroy (production)
docker system prune -a --volumes
kubectl delete namespace (production)
> /dev/sda (writing to block device)
:(){ :|:& };: (fork bomb)
chmod -R 777 / (system-wide permission change)
chown -R user:user / (system-wide ownership change)
systemctl stop critical-service (in production)
```

**Confirmation**: Require typing specific phrase (e.g., "permanently delete")

### 3. Context-Aware Risk Assessment

**Risk modifiers based on context:**

#### File Path Context
```python
def assess_path_risk(path):
    risk_multiplier = 1.0

    # System directories
    if path.startswith(('/bin', '/sbin', '/etc', '/usr', '/sys', '/proc')):
        risk_multiplier *= 3.0

    # Home directory (safer)
    if path.startswith(os.path.expanduser('~')):
        risk_multiplier *= 0.5

    # Temp directories (safest)
    if path.startswith(('/tmp', '/var/tmp')):
        risk_multiplier *= 0.3

    # Production indicators
    if 'prod' in path.lower() or 'production' in path.lower():
        risk_multiplier *= 2.0

    # Dot files/dirs (config)
    if '/.config' in path or '/.ssh' in path:
        risk_multiplier *= 1.5

    return risk_multiplier
```

#### Operation Scope Context
```python
def assess_scope_risk(operation):
    risk_score = operation.base_risk

    # Check for recursive operations
    if operation.is_recursive:
        risk_score += 2

    # Check for wildcards
    if '*' in operation.target or '?' in operation.target:
        risk_score += 1
        # Root-level wildcard is extremely dangerous
        if operation.target.startswith('/*'):
            risk_score += 3

    # Check for piped commands
    if operation.is_piped:
        # Risk is cumulative
        risk_score = max([cmd.risk for cmd in operation.commands])

    return min(risk_score, 4)  # Cap at level 4
```

#### Environment Context
```python
def assess_environment_risk(context):
    risk_multiplier = 1.0

    # Production environment
    if context.environment == 'production':
        risk_multiplier *= 2.0

    # Off-hours operations
    if not context.is_business_hours():
        risk_multiplier *= 1.3

    # Remote operations
    if context.is_remote:
        risk_multiplier *= 1.5

    # Elevated privileges
    if context.user.is_sudo or context.user.is_root:
        risk_multiplier *= 2.0

    return risk_multiplier
```

### 4. Special Cases

#### A. Command Chaining and Pipes
```bash
# Risk assessment should consider the highest-risk command
ls | grep "test" | rm  # Risk: HIGH (rm at end)

# AND/OR chains
mkdir test && cd test && rm -rf *  # Risk: HIGH (rm in chain)

# Evaluate entire pipeline
```

#### B. Variable Expansion
```bash
# Dangerous if variable is empty or unexpected
rm -rf $DIR/*  # If $DIR is empty, becomes rm -rf /*

# Requires validation before execution
```

#### C. Glob Patterns
```bash
# Scope matters
rm *.tmp       # Lower risk (specific extension)
rm *           # Higher risk (everything in current dir)
rm /*          # Critical risk (root level)
```

### 5. Dynamic Risk Assessment Implementation

```python
class CommandRiskAssessor:
    def __init__(self):
        self.base_risks = self.load_base_risk_database()

    def assess_command(self, command_str, context):
        """
        Assess risk of a command in context
        Returns: (risk_level, risk_factors, recommendation)
        """
        # Parse command
        parsed = self.parse_command(command_str)

        # Get base risk from command database
        base_risk = self.base_risks.get(parsed.executable, 2)

        # Apply context modifiers
        path_risk = self.assess_path_risk(parsed.targets)
        scope_risk = self.assess_scope_risk(parsed)
        env_risk = self.assess_environment_risk(context)

        # Calculate final risk
        final_risk = base_risk * path_risk * scope_risk * env_risk

        # Categorize
        if final_risk < 1.0:
            level = 0  # Safe
        elif final_risk < 2.0:
            level = 1  # Low risk
        elif final_risk < 4.0:
            level = 2  # Medium risk
        elif final_risk < 8.0:
            level = 3  # High risk
        else:
            level = 4  # Critical risk

        # Generate recommendation
        recommendation = self.generate_recommendation(level, parsed)

        # Collect risk factors for explanation
        risk_factors = {
            "base_risk": base_risk,
            "path_risk": path_risk,
            "scope_risk": scope_risk,
            "environment_risk": env_risk,
            "final_risk": final_risk
        }

        return (level, risk_factors, recommendation)

    def generate_recommendation(self, level, parsed):
        if level == 0:
            return "Safe to execute without confirmation"
        elif level == 1:
            return "Low risk. Optional confirmation."
        elif level == 2:
            return "Medium risk. Confirmation recommended."
        elif level == 3:
            return f"High risk. Confirmation required. " \
                   f"Will affect: {', '.join(parsed.affected_resources)}"
        else:
            return f"CRITICAL RISK. Typed confirmation required. " \
                   f"This operation could cause significant damage."
```

---

## Implementation Recommendations

### 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Intent Parser                            │
│  - Parse natural language                                   │
│  - Identify proposed operations                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Risk Assessor                              │
│  - Classify operations                                      │
│  - Evaluate context                                         │
│  - Assign risk level                                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                   ┌────────┴────────┐
                   │                 │
              Risk < Threshold    Risk >= Threshold
                   │                 │
                   ▼                 ▼
        ┌──────────────────┐  ┌──────────────────┐
        │  Auto-Execute    │  │  HITL Approval   │
        │                  │  │  - Interrupt     │
        │  - Execute       │  │  - Present       │
        │  - Log           │  │  - Wait          │
        │  - Notify        │  │  - Log decision  │
        └────────┬─────────┘  └────────┬─────────┘
                 │                     │
                 │              User Decision
                 │                ┌────┴────┐
                 │          Approved    Rejected
                 │                │            │
                 ▼                ▼            ▼
        ┌──────────────────────────────┐  ┌────────────┐
        │     Execution Engine         │  │   Cancel   │
        │  - Create snapshot           │  └────────────┘
        │  - Execute with monitoring   │
        │  - Handle errors             │
        └────────────┬─────────────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │      Audit Logger            │
        │  - Record all details        │
        │  - Store for compliance      │
        └────────────┬─────────────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │   Rollback Manager           │
        │  - Maintain undo capability  │
        │  - Offer rollback window     │
        └──────────────────────────────┘
```

### 2. Core Components to Implement

#### A. Risk Assessment Engine
```python
# File: risk_assessor.py

class RiskAssessmentEngine:
    """
    Central risk assessment for all operations
    """
    def __init__(self, config_path="risk_config.yaml"):
        self.config = self.load_config(config_path)
        self.command_database = CommandRiskDatabase()

    def assess(self, operation, context):
        """
        Main assessment method
        Returns: RiskAssessment object
        """
        # 1. Get base risk from command
        base_risk = self.command_database.get_risk(operation.command)

        # 2. Apply context modifiers
        modifiers = self.calculate_modifiers(operation, context)

        # 3. Calculate final risk
        final_risk = self.apply_modifiers(base_risk, modifiers)

        # 4. Determine approval requirement
        approval_required = self.requires_approval(final_risk, context)

        # 5. Generate explanation
        explanation = self.generate_explanation(
            operation, base_risk, modifiers, final_risk
        )

        return RiskAssessment(
            level=final_risk.level,
            score=final_risk.score,
            requires_approval=approval_required,
            approval_type=approval_required.type if approval_required else None,
            explanation=explanation,
            modifiers=modifiers
        )
```

#### B. Approval Manager
```python
# File: approval_manager.py

class ApprovalManager:
    """
    Handles human-in-the-loop approval workflows
    """
    def __init__(self):
        self.approval_handlers = {
            "inline": InlineApprovalHandler(),
            "dialog": DialogApprovalHandler(),
            "typed": TypedConfirmationHandler(),
            "async": AsyncApprovalHandler()
        }

    def request_approval(self, operation, risk_assessment):
        """
        Request approval based on risk level and context
        """
        # Select appropriate handler
        handler_type = self.select_handler(risk_assessment)
        handler = self.approval_handlers[handler_type]

        # Prepare approval request
        request = ApprovalRequest(
            operation=operation,
            risk=risk_assessment,
            timeout=self.get_timeout(risk_assessment)
        )

        # Request approval (may block)
        response = handler.request(request)

        # Log decision
        self.log_approval_decision(request, response)

        return response

class InlineApprovalHandler:
    """Simple command-line confirmation"""
    def request(self, request):
        print(f"\nCommand: {request.operation.command}")
        print(f"Risk: {request.risk.level}")
        print(f"\n{request.risk.explanation}")

        response = input("\nProceed? [y/N]: ")
        return ApprovalResponse(
            approved=(response.lower() == 'y'),
            approver=get_current_user(),
            timestamp=datetime.now()
        )

class TypedConfirmationHandler:
    """Require typing specific phrase for critical operations"""
    def request(self, request):
        confirmation_phrase = "permanently delete"

        print(f"\n⚠️  CRITICAL OPERATION ⚠️")
        print(f"Command: {request.operation.command}")
        print(f"\n{request.risk.explanation}")
        print(f"\nType '{confirmation_phrase}' to confirm: ", end='')

        response = input()
        approved = (response == confirmation_phrase)

        if not approved and response:
            print("Confirmation phrase did not match. Operation cancelled.")

        return ApprovalResponse(
            approved=approved,
            approver=get_current_user(),
            timestamp=datetime.now()
        )
```

#### C. Execution Engine with Safety
```python
# File: execution_engine.py

class SafeExecutionEngine:
    """
    Executes operations with safety mechanisms
    """
    def __init__(self):
        self.snapshot_manager = SnapshotManager()
        self.audit_logger = AuditLogger()
        self.rollback_manager = RollbackManager()

    def execute(self, operation, approval=None):
        """
        Execute operation with full safety mechanisms
        """
        # 1. Pre-execution snapshot (if reversibility is difficult)
        snapshot_id = None
        if operation.is_high_risk and operation.is_hard_to_reverse:
            snapshot_id = self.snapshot_manager.create(
                label=f"pre-{operation.id}"
            )

        # 2. Log execution start
        execution_id = self.audit_logger.log_execution_start(
            operation, approval, snapshot_id
        )

        try:
            # 3. Execute with monitoring
            result = self.execute_with_monitoring(operation)

            # 4. Log success
            self.audit_logger.log_execution_success(
                execution_id, result
            )

            # 5. Setup rollback window (if applicable)
            if operation.supports_rollback:
                self.rollback_manager.enable_rollback_window(
                    execution_id=execution_id,
                    operation=operation,
                    result=result,
                    duration=300  # 5 minutes
                )

            return ExecutionResult(
                success=True,
                result=result,
                execution_id=execution_id,
                snapshot_id=snapshot_id
            )

        except Exception as e:
            # Log failure
            self.audit_logger.log_execution_failure(
                execution_id, e
            )

            # Auto-rollback if in transaction
            if operation.is_transactional:
                self.rollback_manager.rollback(execution_id)

            raise ExecutionException(
                message=f"Execution failed: {str(e)}",
                execution_id=execution_id,
                snapshot_id=snapshot_id
            )

    def execute_with_monitoring(self, operation):
        """
        Execute with ability to interrupt and monitor
        """
        # Implementation depends on operation type
        # Could use subprocess for shell commands
        # Could use specific libraries for other operations
        pass
```

#### D. Policy Configuration System
```python
# File: policy_manager.py

class PolicyManager:
    """
    Manages user-defined and organization-wide policies
    """
    def __init__(self, config_path="policies.yaml"):
        self.policies = self.load_policies(config_path)
        self.user_policies = {}

    def get_policy(self, user, operation_type):
        """
        Get applicable policy for user and operation
        """
        # Check user-specific overrides first
        if user.id in self.user_policies:
            user_policy = self.user_policies[user.id].get(operation_type)
            if user_policy:
                return user_policy

        # Fall back to organizational policy
        return self.policies.get(operation_type, self.get_default_policy())

    def update_user_policy(self, user, operation_type, policy):
        """
        Allow users to customize their own policies
        """
        if user.id not in self.user_policies:
            self.user_policies[user.id] = {}

        self.user_policies[user.id][operation_type] = policy
        self.save_user_policies()

# Example policies.yaml:
"""
default:
  risk_threshold_for_approval: 2  # Level 2 and above require approval
  approval_timeout: 300  # 5 minutes
  require_dry_run_first: false
  enable_rollback_window: true
  rollback_window_duration: 300

file_operations:
  delete:
    risk_threshold_for_approval: 1  # More strict for deletions
    require_dry_run_first: true
    snapshot_before_execution: true

  modify:
    risk_threshold_for_approval: 2
    backup_before_modification: true

database_operations:
  any:
    risk_threshold_for_approval: 2
    require_dry_run_first: true
    require_transaction: true

  drop:
    risk_threshold_for_approval: 0  # Always require approval
    approval_type: "typed_confirmation"

trusted_commands:
  - ls
  - cat
  - grep
  - git status
  - git log
  - pwd
"""
```

### 3. Configuration File Structure

```yaml
# config/ai-shell-config.yaml

# Risk Assessment Configuration
risk_assessment:
  enabled: true
  command_database_path: "./config/command_risks.yaml"
  context_aware: true

  # Risk thresholds (0-4 scale)
  thresholds:
    safe: 0
    low_risk: 1
    medium_risk: 2
    high_risk: 3
    critical: 4

# Approval Configuration
approval:
  enabled: true
  timeout: 300  # seconds

  # When to require approval
  require_for_levels: [2, 3, 4]  # Medium, High, Critical

  # Approval types by risk level
  approval_types:
    0: "none"
    1: "none"
    2: "inline"        # Simple y/n
    3: "dialog"        # Detailed dialog with info
    4: "typed"         # Require typing confirmation phrase

  # Async approval (for long-running operations)
  async_approval:
    enabled: true
    notification_channels: ["terminal", "email"]
    max_wait_time: 14400  # 4 hours

# Safety Mechanisms
safety:
  dry_run:
    enabled: true
    default_on: false
    suggest_for_levels: [3, 4]  # Suggest dry-run for high/critical

  snapshots:
    enabled: true
    create_for_levels: [3, 4]
    retention_count: 10
    retention_days: 7

  rollback:
    enabled: true
    rollback_window: 300  # 5 minutes to rollback
    enable_for_levels: [2, 3, 4]

# Audit Logging
audit:
  enabled: true
  log_path: "~/.ai-shell/logs/audit.log"
  format: "json"

  # What to log
  log_all_commands: true
  log_approvals: true
  log_rejections: true
  log_agent_reasoning: true
  log_context: true

  # Retention
  retention_days: 90
  compress_after_days: 7

# Trust and Learning
trust:
  progressive_trust: true
  initial_trust_level: 0

  # Trust advancement criteria
  advancement:
    operations_required: [10, 50, 100]
    approval_rate_threshold: 0.9
    error_rate_threshold: 0.05

  # User can whitelist specific commands
  user_whitelists:
    enabled: true
    max_whitelisted_commands: 50

# Command Permissions
permissions:
  # Fine-grained permissions
  filesystem:
    read: ["~/*", "/tmp/*"]
    write: ["~/*", "/tmp/*"]
    delete: ["~/*", "/tmp/*"]
    forbidden_paths: ["/", "/etc/*", "/sys/*", "/usr/*"]

  network:
    allow_outbound: true
    allowed_domains: ["*"]  # or specific domains
    forbidden_domains: []
    allow_localhost: true

  database:
    allow_read: true
    allow_write: false
    allow_schema_changes: false

  system:
    allow_package_install: false
    allow_service_control: false
    allow_sudo: false

# User Experience
ux:
  confirmation_style: "detailed"  # "minimal", "detailed", "verbose"
  show_risk_explanations: true
  show_affected_resources: true
  colored_output: true

  # Batch operations
  batch_approval:
    mode: "risk_based"  # "all", "risk_based", "individual"
    show_summary: true
```

### 4. Phased Implementation Roadmap

#### Phase 1: Foundation (Week 1-2)
**Goal**: Basic risk assessment and approval flow

1. Implement simple command risk database
2. Basic risk assessment engine (static rules)
3. Inline approval handler
4. Simple audit logging
5. Configuration system

**Milestone**: Can identify dangerous commands and require approval

#### Phase 2: Safety Mechanisms (Week 3-4)
**Goal**: Add rollback and audit capabilities

1. Implement execution engine with monitoring
2. Command history with basic undo
3. Structured audit logging (JSON)
4. Dry-run mode for preview
5. Error handling and rollback on failure

**Milestone**: Safe execution with rollback capability

#### Phase 3: Enhanced UX (Week 5-6)
**Goal**: Better user experience

1. Multiple approval handlers (inline, dialog, typed)
2. Batch operation support
3. Context-aware risk assessment
4. Colored output and clear formatting
5. Configuration UI/TUI

**Milestone**: Pleasant, non-intrusive confirmation flows

#### Phase 4: Advanced Features (Week 7-8)
**Goal**: Progressive trust and learning

1. Trust level tracking
2. User preference learning
3. Command whitelisting
4. Fine-grained permissions system
5. Async approval support

**Milestone**: System adapts to user patterns

#### Phase 5: Enterprise Features (Week 9-10)
**Goal**: Organization-wide deployment

1. Policy management system
2. Centralized audit logging
3. RBAC integration
4. Compliance reporting
5. Multi-user support

**Milestone**: Ready for organizational deployment

### 5. Testing Strategy

#### Unit Tests
```python
# tests/test_risk_assessment.py

def test_safe_command_no_approval():
    assessor = RiskAssessmentEngine()
    operation = Operation("ls -la")
    context = Context(user="test_user", cwd="/home/test")

    assessment = assessor.assess(operation, context)

    assert assessment.level == 0
    assert not assessment.requires_approval

def test_dangerous_command_requires_approval():
    assessor = RiskAssessmentEngine()
    operation = Operation("rm -rf /tmp/important_data")
    context = Context(user="test_user", cwd="/home/test")

    assessment = assessor.assess(operation, context)

    assert assessment.level >= 3
    assert assessment.requires_approval
    assert assessment.approval_type in ["dialog", "typed"]

def test_context_affects_risk():
    assessor = RiskAssessmentEngine()
    operation = Operation("rm file.txt")

    # In /tmp - lower risk
    context_tmp = Context(user="test_user", cwd="/tmp")
    assessment_tmp = assessor.assess(operation, context_tmp)

    # In /etc - higher risk
    context_etc = Context(user="test_user", cwd="/etc")
    assessment_etc = assessor.assess(operation, context_etc)

    assert assessment_etc.level > assessment_tmp.level
```

#### Integration Tests
```python
# tests/test_approval_flow.py

def test_full_approval_flow():
    # Setup
    engine = SafeExecutionEngine()
    operation = Operation("rm test.txt")

    # Mock approval
    with mock_approval(approved=True):
        result = engine.execute(operation)

    assert result.success
    assert result.execution_id is not None

    # Verify audit log
    logs = get_audit_logs()
    assert any(log.operation == "rm test.txt" for log in logs)

def test_rejection_prevents_execution():
    engine = SafeExecutionEngine()
    operation = Operation("rm important.txt")

    # Mock rejection
    with mock_approval(approved=False):
        result = engine.execute(operation)

    assert not result.success
    assert result.reason == "User rejected"

    # Verify file still exists
    assert os.path.exists("important.txt")
```

#### End-to-End Tests
```python
# tests/test_e2e.py

def test_safe_workflow():
    """Test full workflow for safe command"""
    # Run command
    result = run_ai_shell("list files in current directory")

    # Should execute without approval
    assert "ls" in result.commands_executed
    assert not result.required_approval
    assert result.success

def test_dangerous_workflow():
    """Test full workflow for dangerous command"""
    # Prepare test environment
    create_test_file("deleteme.txt")

    # Run command that requires approval
    with interactive_session() as session:
        session.send("delete deleteme.txt")

        # Should prompt for approval
        assert "Confirm?" in session.output

        # Approve
        session.send("y")

        # Should execute
        assert session.success
        assert not os.path.exists("deleteme.txt")
```

### 6. Example User Flows

#### Flow 1: Safe Command (No Approval)
```
$ ai-shell "show me the largest files in current directory"

Analyzing request...
Proposed command: du -ah . | sort -rh | head -n 10
Risk level: SAFE
Executing...

[Command output shown]

✓ Completed in 0.3s
```

#### Flow 2: Risky Command (Requires Approval)
```
$ ai-shell "delete all .log files older than 30 days"

Analyzing request...
Proposed command: find . -name "*.log" -mtime +30 -delete
Risk level: HIGH

⚠️  This will permanently delete files. Details:
  • Scope: Current directory and subdirectories
  • Estimated files: 47 files
  • Estimated size: 123 MB
  • Reversibility: Cannot be undone

Proceed with deletion? [y/N]: y

Creating safety snapshot... done (snapshot_a8f3d2)
Executing...

✓ Deleted 47 files (123 MB)
✓ Completed in 2.1s

If you need to undo: ai-shell restore snapshot_a8f3d2
Rollback available for 5 minutes.
```

#### Flow 3: Critical Command (Typed Confirmation)
```
$ ai-shell "drop the test database"

Analyzing request...
Proposed command: DROP DATABASE test_db;
Risk level: CRITICAL

⚠️⚠️⚠️  CRITICAL OPERATION  ⚠️⚠️⚠️

This will PERMANENTLY delete the entire 'test_db' database.
  • All tables will be destroyed
  • All data will be lost
  • This cannot be undone
  • No backup will be created

Type 'permanently delete' to confirm: permanently delete

Executing DROP DATABASE...

✓ Database test_db dropped
✓ Completed in 0.8s
```

#### Flow 4: Batch Operations with Summary
```
$ ai-shell "cleanup project: remove node_modules, .pyc files, and cache"

Analyzing request...
Proposed operations:

1. rm -rf node_modules/          [HIGH RISK]
   • Will delete: 15,234 files (431 MB)

2. find . -name "*.pyc" -delete  [MEDIUM RISK]
   • Will delete: ~50 files (2 MB)

3. rm -rf .cache/                [MEDIUM RISK]
   • Will delete: 234 files (18 MB)

Total: Will delete 15,518 files (451 MB)

Review each operation individually? [y/N]: n

Proceed with all operations? [y/N]: y

Executing batch operations...
  ✓ Removed node_modules/ (431 MB)
  ✓ Removed 52 .pyc files (2.1 MB)
  ✓ Removed .cache/ (18 MB)

✓ All operations completed successfully
✓ Total time: 8.3s
```

#### Flow 5: Learning and Trust Building
```
$ ai-shell "run tests"

Analyzing request...
Proposed command: npm test
Risk level: LOW

You've run "npm test" 12 times without issues.

Would you like to:
  1. Always run "npm test" without confirmation
  2. Keep asking each time
  3. Ask only if package.json changed

Choice [1/2/3]: 1

✓ Added "npm test" to trusted commands
Executing...

[Test output shown]

✓ Tests passed
```

---

## Real-World Examples

### 1. LangGraph (LangChain)
**Framework**: Python-based agent framework

**HITL Features**:
- Dynamic interrupts via `interrupt()` function
- State persistence during pauses
- Resume with human input via `Command` objects
- Four primary patterns: approve/reject, edit state, review tools, validate input

**Example**:
```python
from langgraph.types import interrupt, Command

def critical_action_node(state):
    # Pause for human approval
    approved = interrupt({
        "action": state["proposed_action"],
        "risk": "high",
        "explanation": "This will modify production database"
    })

    if approved:
        return Command(goto="execute_action")
    else:
        return Command(goto="cancel_action")
```

**Use case**: Building AI agents that need human oversight for critical decisions

### 2. AWS Bedrock Agents
**Platform**: Amazon Web Services

**HITL Features**:
- User confirmation checkpoints
- Action review before execution
- Integration with AWS IAM for permissions
- Audit logging via CloudWatch

**Use case**: Enterprise agents with compliance requirements

### 3. Terraform
**Tool**: Infrastructure as Code

**HITL Pattern**: Plan-then-Apply workflow

**How it works**:
```bash
# Step 1: Plan (dry-run)
$ terraform plan -out=tfplan
# Shows what will change

# Step 2: Review plan file
# Human reviews proposed changes

# Step 3: Apply (requires explicit apply command)
$ terraform apply tfplan
# Executes approved changes
```

**Safety features**:
- Separate plan and apply phases
- Plan saved to file (can be reviewed, version controlled)
- Color-coded output (green = create, yellow = modify, red = delete)
- Resource count summary
- Option to target specific resources

**Use case**: Infrastructure changes where mistakes are costly

### 4. Ansible
**Tool**: Configuration management and automation

**HITL Patterns**:

**A. Check Mode (Dry-Run)**:
```bash
ansible-playbook playbook.yml --check
# Shows what would change without changing it
```

**B. Step Mode**:
```bash
ansible-playbook playbook.yml --step
# Prompts before each task
```

**C. Diff Mode**:
```bash
ansible-playbook playbook.yml --check --diff
# Shows file differences for changes
```

**Use case**: Server configuration changes across multiple machines

### 5. Kubernetes
**Tool**: Container orchestration

**HITL Patterns**:

**A. Dry-Run**:
```bash
kubectl apply -f deployment.yaml --dry-run=client
# Validates locally without contacting cluster

kubectl apply -f deployment.yaml --dry-run=server
# Validates with API server without persisting
```

**B. Diff**:
```bash
kubectl diff -f deployment.yaml
# Shows what would change
```

**Use case**: Deploying applications to production clusters

### 6. GitHub Actions (Environments with Protection Rules)
**Platform**: CI/CD

**HITL Features**:
- Required reviewers for deployments
- Environment protection rules
- Manual approval gates in workflows
- Deployment logs and audit trail

**Example workflow**:
```yaml
jobs:
  deploy_production:
    runs-on: ubuntu-latest
    environment:
      name: production
      # This environment requires approval from designated reviewers
    steps:
      - name: Deploy
        run: ./deploy.sh
```

**Use case**: Software deployments requiring human approval

### 7. Azure DevOps Pipelines
**Platform**: CI/CD

**HITL Features**:
- Pre-deployment and post-deployment approvals
- Service connection approvals
- Manual intervention tasks
- Gates (automated checks before/after)

**Configuration**:
```yaml
stages:
  - stage: Production
    jobs:
      - deployment: DeployWeb
        environment: production  # Has approval configured
        strategy:
          runOnce:
            deploy:
              steps:
                - task: ManualIntervention@8
                  inputs:
                    instructions: 'Review deployment and approve'
```

**Use case**: Enterprise release pipelines

### 8. Google Cloud Build with Approval
**Platform**: CI/CD

**HITL Features**:
- Manual approval step in build pipelines
- Integration with Cloud Functions for custom approval logic
- Pub/Sub notifications for approval requests

**Use case**: Deployments requiring manual checkpoints

### 9. OpenAI Function Calling (with Safety Layers)
**Platform**: AI/LLM

**Recommended Safety Pattern**:
```python
def safe_function_executor(function_call):
    # 1. Validate function call
    if not validate_function(function_call):
        return "Invalid function call"

    # 2. Risk assessment
    risk = assess_risk(function_call)

    # 3. Require approval for high-risk
    if risk >= HIGH_RISK:
        approved = request_user_confirmation(function_call, risk)
        if not approved:
            return "Operation cancelled by user"

    # 4. Execute with least privilege
    result = execute_with_limited_permissions(function_call)

    # 5. Audit log
    log_function_execution(function_call, result)

    return result
```

**Use case**: AI agents calling external APIs or tools

### 10. CrewAI with HumanLayer
**Framework**: Multi-agent orchestration

**HITL Features**:
- Human-as-a-tool pattern
- Interrupt workflows for clarification
- Approval flows for agent actions
- Route uncertain tasks to humans

**Example**:
```python
from crewai import Agent, Task, Crew
from humanlayer import HumanLayer

hl = HumanLayer()

agent = Agent(
    role="DevOps Engineer",
    goal="Deploy application",
    tools=[deploy_tool, hl.human_as_tool()]
)

# Agent can call human for approval
task = Task(
    description="Deploy to production",
    agent=agent,
    require_human_approval=True
)
```

**Use case**: Multi-agent systems with human oversight

### 11. Permit.io + OPAL
**Platform**: Authorization and policy management

**HITL Pattern**: Policy-based access control with dynamic authorization

**Features**:
- Fine-grained permissions
- Policy as code
- Real-time authorization decisions
- Audit trail of access requests

**Example policy**:
```python
# In Permit.io
allow(agent, "execute_command", command) if
    command.risk_level == "low" or
    (command.risk_level == "medium" and user.trust_level >= 50) or
    (command.risk_level == "high" and user.has_approved(command))
```

**Use case**: Enterprise AI agents with complex authorization needs

### 12. Salesforce Einstein (Agentforce)
**Platform**: CRM with AI agents

**Safety Features**:
- Agent-specific permissions
- Transaction rollback capabilities
- Audit trails
- User must grant agent permissions explicitly

**Use case**: AI agents operating on business-critical CRM data

---

## References

### Academic Papers

1. **"AI Agents Under Threat: A Survey of Key Security Challenges and Future Pathways"** (2024)
   - ACM Computing Surveys
   - Comprehensive security taxonomy for AI agents
   - https://arxiv.org/abs/2406.02630

2. **"Multi-Agent Risks from Advanced AI"** (2025)
   - Risk taxonomy: miscoordination, conflict, collusion
   - https://arxiv.org/abs/2502.14143

3. **"Transforming cybersecurity with agentic AI to combat emerging cyber threats"** (2024)
   - ScienceDirect
   - Safety mechanisms for security contexts

### Technical Documentation

4. **LangGraph Human-in-the-Loop Concepts**
   - https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
   - Primary reference for HITL patterns

5. **AWS Bedrock Agents - Human-in-the-Loop**
   - https://aws.amazon.com/blogs/machine-learning/implement-human-in-the-loop-confirmation-with-amazon-bedrock-agents/
   - Enterprise HITL implementation

6. **OpenAI Responsible AI Practices**
   - https://platform.openai.com/docs/guides/safety-best-practices
   - Multi-layer safety framework

7. **Microsoft Azure Responsible AI for OpenAI**
   - https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/openai/overview
   - Safety practices and validation

### Industry Best Practices

8. **OWASP Top 10 for LLM Applications (2025)**
   - Security recommendations for LLM-based systems
   - https://owasp.org/www-project-top-10-for-large-language-model-applications/

9. **Nielsen Norman Group - Confirmation Dialogs**
   - https://www.nngroup.com/articles/confirmation-dialog/
   - UX research on confirmation patterns

10. **Cerbos - Permission Management for AI Agents**
    - https://www.cerbos.dev/blog/permission-management-for-ai-agents
    - Fine-grained authorization patterns

11. **Permit.io - Human-in-the-Loop for AI Agents**
    - https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo
    - Best practices and frameworks overview

### Infrastructure Tools Documentation

12. **Terraform Plan Command Reference**
    - https://developer.hashicorp.com/terraform/cli/commands/plan
    - Infrastructure dry-run pattern

13. **Ansible Check Mode**
    - https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_checkmode.html
    - Configuration management safety

14. **Kubernetes Dry-Run**
    - https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/
    - Container orchestration safety

15. **Azure DevOps Pipeline Approvals**
    - https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals
    - CI/CD approval workflows

### Security Resources

16. **WorkOS - Securing AI Agents**
    - https://workos.com/blog/securing-ai-agents
    - Authentication, authorization, defense guide

17. **Google AI Agent Security**
    - https://simonwillison.net/2025/Jun/15/ai-agent-security/
    - Google's approach to agent security

18. **Dangerous Linux Commands Guides**
    - https://phoenixnap.com/kb/dangerous-linux-terminal-commands
    - Command risk classification references

### Design Patterns

19. **Memento Pattern (Undo/Rollback)**
    - https://refactoring.guru/design-patterns/memento
    - State snapshot pattern for rollback

20. **Command Pattern**
    - https://refactoring.guru/design-patterns/command
    - Encapsulation of operations for undo/redo

---

## Appendix: Quick Reference Tables

### Approval Requirements by Risk Level

| Risk Level | Confirmation Type | Timeout | Dry-Run Recommended | Snapshot Recommended |
|------------|------------------|---------|---------------------|---------------------|
| 0 - Safe | None | N/A | No | No |
| 1 - Low | Optional | N/A | No | No |
| 2 - Medium | Yes (inline) | 5 min | Suggested | Optional |
| 3 - High | Yes (dialog) | 10 min | Strongly suggested | Yes |
| 4 - Critical | Yes (typed) | 30 min | Required | Yes |

### Command Examples by Risk Level

| Level | Examples |
|-------|----------|
| 0 | `ls`, `pwd`, `cat`, `grep`, `git status`, `echo` |
| 1 | `touch`, `mkdir`, `echo >`, `cp` (new file) |
| 2 | `mv`, `sed -i`, `git commit`, `chmod`, `wget` |
| 3 | `rm -r`, `DROP TABLE`, `git push -f`, `sudo`, `kill` |
| 4 | `rm -rf /`, `DROP DATABASE`, `terraform destroy`, `mkfs` |

### Permission Model Comparison

| Model | Granularity | Complexity | Flexibility | Best For |
|-------|-------------|------------|-------------|----------|
| Whitelist | Coarse | Low | Low | Development, trusted users |
| Blacklist | Coarse | Low | Medium | General purpose |
| RBAC | Medium | Medium | Medium | Organizations with roles |
| ABAC | Fine | High | High | Complex, context-aware needs |
| PBAC | Fine | High | Very High | Dynamic, policy-driven orgs |

### Rollback Capability by Operation

| Operation | Difficulty | Method | Requirements |
|-----------|-----------|---------|--------------|
| File create | Easy | Delete | None |
| File modify | Medium | Restore backup | Backup exists |
| File delete | Hard | Restore backup | Backup exists, trash enabled |
| DB INSERT | Easy | DELETE with IDs | IDs captured |
| DB UPDATE | Medium | UPDATE with old values | Old values saved |
| DB DELETE | Hard | INSERT from backup | Backup exists |
| API call | Varies | Compensating transaction | API supports |
| Git commit | Easy | `git revert` or `git reset` | None |
| Package install | Easy | Uninstall | Package manager |
| Config change | Medium | Restore old config | Old config saved |

---

## Conclusion

Implementing effective human-in-the-loop patterns for AI agents in shell/system automation requires balancing several concerns:

1. **Safety First**: High-risk operations must always require human approval
2. **User Experience**: Confirmations should be non-intrusive and context-appropriate
3. **Progressive Trust**: Systems should learn and adapt to user patterns
4. **Comprehensive Audit**: All operations should be logged for accountability
5. **Multiple Safety Layers**: Defense in depth with risk assessment, approval, monitoring, and rollback

The research clearly shows that modern AI agent systems are moving toward:
- **Context-aware authorization** over static rules
- **Policy-based access control** over simple whitelists
- **Multi-layer safety** over single-point protection
- **Graduated confirmation levels** over one-size-fits-all dialogs
- **Human-on-the-loop** for mature systems over always-in-the-loop

For implementation in ai-shell, the recommended approach is:
1. Start with a robust risk classification system
2. Implement clear approval workflows with appropriate UX
3. Add comprehensive audit logging early
4. Build in rollback capabilities from the start
5. Layer on progressive trust as the system matures

This foundation will enable safe, user-friendly AI-powered shell automation that users can trust.

---

*Research compiled: October 9, 2025*
*Last updated: October 9, 2025*
