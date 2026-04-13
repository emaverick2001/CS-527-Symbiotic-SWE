# 3. Draft your research project report / plan

## **Abstract (Snapshot of the Entire Project)**

- **Purpose:**
  - Provide a _compressed, self-contained summary_ of the entire project.
  - Answers If someone only reads this, do they understand the entire project at a high level?
- ## \*\*Key Question:
- **Constraints:**
  - Maximum: **150–200 words**
  - Each subsection should be **1–2 sentences max**
  - Must be readable as **one continuous paragraph**
  - Must not introduce concepts that are not expanded later in the paper
  - Must strictly follow this flow:
    - Problem → Challenge → Gap → Idea → Method → Results → Impact

---

### **Problem Context (1–2 sentences)**

- What problem are you solving at a high level?
- What is its importance or impact?
- **Output of this section should be:**
  - A **clear, high-level problem statement**

---

-

### **Core Challenge (1 sentence)**

- Why is this problem fundamentally difficult?
- What makes it unsolved?
- **Output of this section should be:**
  - A **single core difficulty**

---

-

### **Key Insight / Idea (1–2 sentences)**

- What is the minimal conceptual insight that makes your approach work?
- What assumption does your method change or relax?
- **Output of this section should be:**
  - A one-sentence thesis (core idea)

---

-

### **Approach Summary (1–2 sentences)**

- What type of system/method did you build?
- What are the key components at a high level?
- **Output of this section should be:**
  - A high-level method description (no mechanism details)

---

-

### **Results / Expected Outcomes (1–2 sentences)**

- What improvement, property, or capability does your approach achieve?
- What metrics or behaviors improve?
- **Output of this section should be:**
  - A **clear claim about performance or capability**

---

-

### **Impact (1 sentence)**

- Why does this matter?
- What broader implication does this unlock?
- **Output of this section should be:**
  - A **one-line significance statement**

---

-

## **Introduction (Problem Framing + Why It Matters + Positioning)**

- **Purpose:**
  - Build a _compelling narrative_ from problem → difficulty → gap → idea.
- ## \*\*Key Question:
- **Constraints:**
  - No detailed implementation (belongs to Proposed Technique)
  - No experimental results (belongs to Evaluation)
  - No full literature breakdown (belongs to Related Work)
  - Focus on _conceptual understanding_, not mechanisms
  - Each subsection must introduce **new information only** (no repetition)

---

### **Problem Context & Importance**

- What is the real-world or technical problem?
- Who does it affect and why should we care?
- What happens if this problem is not solved?
- What downstream systems, decisions, or users are impacted?
- ## **Output of this section should be:**

---

- [[Autonomous Software Agent]]s are increasingly used to automate debugging, code repair, and developer workflows. These systems impact:
  - developers (productivity)
  - organizations (cost, reliability)
  - downstream systems (software correctness and safety)
- A critical failure mode emerges in **logic-heavy bugs**, where correctness depends on:
  - predicates
  - invariants
  - edge-case completeness
- When these bugs are incorrectly resolved:
  - systems may silently fail in production
  - errors propagate into downstream pipelines (e.g., data systems, ML models, infrastructure)
  - trust in automated coding systems degrades
- This problem is especially important because SWE agents are moving toward **autonomous decision-making systems**, where incorrect fixes are not easily caught by humans.

### **Why is this Problem Hard?**

- What makes this problem fundamentally challenging?
- Frame in terms of:
  - scale
  - uncertainty
  - constraints
  - tradeoffs
- What specific property of the problem breaks naive solutions?
- ## **Output of this section should be:**

---

1. Unbounded Input Space
   - Programs must be correct for **all possible inputs**, but:
     - tests only cover a finite subset
     - edge cases are often missing
2. Partial Observability
   - The agent sees:
     - code
     - tests
     - error messages
   - But does not directly observe:
     - invariants
     - implicit constraints
     - full behavioral specifications
3. Uncertainty in Reasoning
   - LLMs generate patches probabilistically:
     - no guarantees of logical consistency
     - prone to small but critical predicate errors
4. Tradeoff: Exploration vs Correctness
   - Agents must:
     - explore possible fixes
     - minimize iterations / tokens
   - Without strong signals, they rely on inefficient trial-and-error

### **Current Approaches (High-Level Only)**

- What _categories_ of approaches exist?
- What general strategies do they use?
- What key assumptions do they rely on?
- **Output of this section should be:**
  - A small set of approach categories + their core assumptions
- ⚠️ Do NOT:
  - list individual papers
  - go into implementation details

---

- **Neural Agent-Based Approaches**
  - Strategy:
    - generate patches using LLM reasoning
    - validate using execution feedback (tests)
  - Assumption:
    - test feedback is sufficient proxy for correctness
- **Execution-Guided Search**
  - Strategy:
    - iteratively refine patches based on failures
  - Assumption:
    - failures provide informative gradients toward correct solutions
- **Symbolic / Formal Methods**
  - Strategy:
    - encode program behavior as constraints and verify correctness
  - Assumption:
    - program logic can be expressed and solved within tractable bounds
- **[[Neuro-Symbolic AI]] (Loose Integration)**
  - Strategy:
    - use symbolic tools offline or as auxiliary signals
  - Assumption:
    - symbolic reasoning does not need to be tightly integrated into decision-making

### **Research Gap (Surface-Level Limitations)**

- Where do existing approaches fail in practice?
- What important capability is missing?
- In what scenarios do they break?
- **Output of this section should be:**
  - A clear list of **observable failure modes**

---

- **Test Overfitting**
  - patches pass tests but fail unseen cases
- **Logical Regression**
  - fixes introduce new bugs outside tested scenarios
- **Inefficient Search**
  - many iterations needed due to weak feedback
- **Edge-Case Blindness**
  - missing coverage leads to incomplete fixes
- **Uninformative Feedback**
  - “fail/pass” signals lack explanation or structure
- **Disconnected Symbolic Tools**
  - formal methods are not used during decision-making

### **Root Cause of Failure (Deeper Insight)**

- Why do these approaches fail fundamentally?
- What assumption breaks in your setting?
- Why can’t existing methods be easily extended to fix this?
- **Output of this section should be:**
  - A single unifying explanation for why current methods fail

---

- All failure modes can be traced to a single underlying issue: **Mismatch between the space of reasoning during execution and the space of feedback**
- Specifically:
  - reasoning happens over:
    - full program logic
    - implicit invariants
  - feedback happens over:
    - finite execution traces (tests)
- This creates:
  - weak supervision signals
  - no mechanism to enforce correctness beyond observed cases
- Why existing methods can’t fix this easily:
  - adding more tests → still incomplete
  - improving prompts → still probabilistic
  - using symbolic tools offline → not influencing decisions

### **Key Idea / Thesis**

- What is your main conceptual idea (one sentence)?
- What assumption does your method change or relax?
- What new perspective or formulation do you introduce?
- How does this idea directly address the root cause?
- **Output of this section should be:**
  - A one-sentence thesis + short explanation

---

- **Thesis (one sentence):**
  - We propose reframing automated debugging as a search process guided by formal counterexamples rather than execution traces.
- **Explanation:**
  - Instead of:
    - “Did this patch pass tests?”
  - We ask:
    - “Does this patch violate any logical constraints?”
- This changes the core assumption:
  - from: tests approximate correctness
  - to: counterexamples expose correctness violations
- This directly addresses the root cause by:
  - aligning feedback with the **logical space of the problem**
  - providing **structured, adversarial signals** instead of binary outcomes

### **Scope & Non-Goals**

- What are you explicitly not solving?
- What assumptions are you making?
- What boundaries define your approach?
- **Output of this section should be:**
  - A clearly defined problem boundary

---

- **Scope**
  - Bugs that:
    - can be expressed as logical constraints
    - involve predicates, invariants, or edge cases
  - Primarily:
    - single-function or small-scope reasoning
    - deterministic behavior
- **Non-Goals**
  - Large-scale refactoring
  - API misuse requiring documentation reasoning
  - multi-file architectural changes
  - problems requiring new algorithm design
- **Assumptions**
  - availability of:
    - type hints, assertions, or inferable constraints
  - constraints are expressible in SMT

### **Contributions (VERY IMPORTANT)**

- List **specific, testable contributions**, each phrased as:
  - _We introduce…_
  - _We show that…_
  - _We demonstrate…_
- Example structure:
  - We introduce a [method/system] for [problem]
  - We show that [key result or property]
  - We demonstrate improvements in [metric] under [conditions]
  - We provide [artifact: dataset/tool/analysis]
- ## **Output of this section should be:**
- ⚠️ Each contribution must:
  - map directly to evaluation
  - be falsifiable/testable

---

- We introduce a **neuro-symbolic inner-loop repair architecture** that integrates symbolic verification directly into the agent’s iterative decision-making process.
- We introduce **Counter-Example Guided Feedback (CEGF)** as a mechanism to convert formal constraint violations into structured feedback for LLM-based refinement.
- We show that incorporating formal counterexamples **reduces patch search entropy/options**, leading to fewer iterations and more targeted fixes.
- We demonstrate that Symbiotic-SWE improves **bug resolution rates and logical correctness** on logic-heavy tasks compared to neural-only baselines.
- We provide a **taxonomy and benchmark subset** for identifying solver-expressible logic failures in SWE tasks.
- We provide a **fully instrumented artifact pipeline** (schemas, logs, trajectories) enabling reproducible analysis of agent behavior.

## **Related Work (What has been tried?)**

- **Purpose:**
  - Position your work relative to existing approaches
  - Identify how prior work **approaches the problem space and where it falls short**
- \*\*Key Question:
  - What solution strategies exist, what assumptions do they make, and how does my approach differ?
- **Constraints:**
  - No problem motivation (belongs to Introduction)
    - No deep implementation details (belongs to Proposed Technique)
    - No repetition of high-level limitations (already covered in Introduction)
    - Focus on **method categories, assumptions, and design patterns**
    - Each category must produce a **clear takeaway**

---

### **Category-by-Category Analysis**

- We group related work into **four categories**:

---

#### **1. LLM-Based SWE Agents**

- **Core Idea:**
  - Use an LLM as the central reasoning engine to retrieve context, generate code patches, and iteratively interact with software engineering environments.
- **Typical Approach:**
  - These systems read bug reports, inspect repositories, generate candidate edits, and validate them through environment interaction or test execution.
- **Key Assumptions:**
  - The LLM can infer the relevant bug mechanism from repository context.
  - Iterative trial-and-error combined with tool use is sufficient to find a valid fix.

---

- **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (2024)**
  - **Strengths:**
    - Strong at repository navigation, tool use, and long-horizon interaction.
    - Provides a realistic agentic framework for software engineering workflows.
  - **Limitations (Category-Specific):**
    - Relies heavily on execution signals and iterative search.
    - Does not directly enforce logical correctness or reason over untested inputs.
- **OpenHands (2024)**
  - **Strengths:**
    - Expands the interactive tool-using agent paradigm and supports multi-step debugging workflows.
    - Strong for practical software engineering tasks that require repository interaction.
  - **Limitations (Category-Specific):**
    - Still fundamentally depends on execution-based validation.
    - Intermediate reasoning remains probabilistic and weakly constrained.
- **SWE-bench Pro (2025)**
  - SWE-bench Pro analyzes failure modes of LLM-based SWE agents in long-horizon debugging tasks. It highlights that many failures arise from incorrect reasoning about program logic and incomplete exploration of edge cases, reinforcing the need for stronger feedback mechanisms beyond test execution.
- **Category Takeaway:**
  - LLM-based SWE agents are strong at exploration and patch generation, but their repair loop is driven mainly by **behavioral signals**, not formal guarantees.

#### **2. Execution-Guided Repair and Validation Methods**

- **Core Idea:**
  - Use tests, runtime traces, and observed failures as the main supervisory signal for patch selection and refinement.
- **Typical Approach:**
  - Generate a candidate patch, run tests, inspect failures, and repeat until a patch passes the available validation suite.
- **Key Assumptions:**
  - Test suites are sufficiently informative proxies for correctness.
  - Runtime failures expose enough signal to guide repair toward the true bug.

---

- **1. Test-driven agentic repair pipelines**
  - **Strengths:**
    - Easy to integrate into existing software engineering workflows.
    - Works well when test coverage is high and failure traces are informative.
  - **Limitations (Category-Specific):**
    - Sparse pass/fail signals do not explain why a patch is wrong.
    - Can overfit to tests and miss invariant violations or edge-case failures.
- **2. SWE-bench-style evaluation setups**
  - **Strengths:**
    - Provide realistic bug-fixing tasks with repository context and failing tests.
    - Enable standardized comparison across repair systems.
  - **Limitations (Category-Specific):**
    - Encourage evaluation through test-passing behavior rather than logical correctness.
    - Can underrepresent cases where correctness depends on unobserved inputs or invariants.
  - **Category Takeaway:**
    - Execution-guided methods provide practical and scalable validation, but they assume that **runtime signals are rich enough to stand in for correctness**, which breaks on logic-heavy bugs.

#### **3. Symbolic Execution and Formal Methods**

- **Core Idea:**
  - Model program behavior using symbolic variables and logical constraints, then search for counterexamples or prove properties with solvers.
- **Typical Approach:**
  - Translate code, assertions, contracts, or type information into logical formulas and ask an SMT solver whether violations exist.
- **Key Assumptions:**
  - Program behavior can be expressed in a tractable symbolic form.
  - The relevant correctness properties are either explicit or can be reasonably inferred.

---

- **1. CrossHair**
  - **Strengths:**
    - Provides symbolic execution for Python and integrates naturally with assertions and type hints.
    - Useful for finding concrete counterexamples over a broader input space.
  - **Limitations (Category-Specific):**
    - Typically operates as a standalone verifier, not as an online repair controller.
    - Scalability depends on slice size and expressibility of the target logic.
- **2. Z3-based solver workflows**
  - **Strengths:**
    - Strong at checking satisfiability, invariant violations, and symbolic consistency.
    - Provides precise counterexamples when constraints are expressible.
  - **Limitations (Category-Specific):**
    - Requires careful encoding and a tractable symbolic subset.
    - Not designed by itself for open-ended repository-level patch generation.
- **LLM-Powered Symbolic Execution (2025)**
  - This line of work uses LLMs to augment symbolic execution pipelines, for example by generating missing type hints or annotations required for effective constraint solving. While it improves solver applicability, it does not address how symbolic reasoning can be used to guide LLM-based repair in an online, agentic setting.
- **Category Takeaway:**
  - Formal methods are strong at **precise correctness reasoning**, but weak at open-ended search and developer-style patch generation.

#### **4. Neuro-Symbolic and Hybrid Approaches**

- **Core Idea:**
  - Combine neural methods with symbolic reasoning so that learning-based systems can benefit from formal structure.
- **Typical Approach:**
  - Use symbolic tools to generate data, infer annotations, improve verification coverage, or supply auxiliary signals to learning systems.
- **Key Assumptions:**
  - Loose coupling between neural and symbolic systems is sufficient to gain the benefits of both.
  - Symbolic reasoning can remain outside the main online decision loop.

---

- **LLM-Powered Symbolic Execution**
  - **Strengths:**
    - Uses LLMs to improve symbolic tooling, for example by adding type hints or making symbolic analysis more applicable.
    - Shows that LLMs and symbolic methods can complement each other.
  - **Limitations (Category-Specific):**
    - Focuses on improving symbolic analysis itself, not agentic repair.
    - Does not close the loop between solver output and iterative patch refinement.
- **Neuro-Symbolic Program Analysis (various)**
  - Strengths:
    - Show the value of combining formal reasoning with learning-based representations.
    - Useful for tasks like offline verification, dataset generation, or local repair.
  - Limitations (Category-Specific):
    - Often operate offline or at unit scope.
    - Rarely treat the symbolic engine as an active tool inside a live debugging loop.
  - Prior work has explored combining neural models with symbolic reasoning for tasks such as code understanding, verification, and test generation. These approaches typically use symbolic methods to enhance training data or provide auxiliary signals but do not tightly integrate them into the decision loop of an autonomous agent.
- **Counterexample-Guided Inductive Synthesis (CEGIS)**
  - CEGIS is a classical paradigm in program synthesis where candidate programs are iteratively refined using counterexamples generated by a verifier. While highly effective in constrained settings, it assumes a well-defined specification and does not directly extend to open-ended repository-level debugging tasks handled by LLM agents.
- **Category Takeaway:**
  - Hybrid methods recognize the value of combining neural and symbolic reasoning, but most stop short of making symbolic feedback a **first-class control signal** for an autonomous SWE agent.

#### **Program Repair**

- Automated Program Repair (APR) systems (GenProg, etc.)
- Neural program repair papers

#### **Tool-Augmented LLMs**

- ReAct / Toolformer-style work (LLMs using tools iteratively)

#### **Verification-Aware ML**

- Work on integrating formal guarantees into ML systems

### **Cross-Category Comparison (Synthesis Layer)**

- Compare categories along key dimensions:
- **Example axes:**
  - Static vs dynamic decision-making
  - Token-level vs semantic-level reasoning
  - Local vs global optimization
  - Heuristic vs learned approaches
- **Output of this section should be:**
  - A **structured comparison of design tradeoffs across categories**

---

- **Static vs dynamic decision-making**
  - Formal verification methods are often static and analysis-driven.
  - Agentic SWE systems are dynamic and iterative.
- **Behavioral vs logical feedback**
  - Execution-guided methods rely on observed runtime behavior.
  - Symbolic methods reason over logical possibility spaces.
- **Open-ended generation vs constrained validation**
  - LLM agents are good at exploring many candidate patches.
  - Solvers are good at rejecting incorrect candidates with precision.
- **Local vs global correctness reasoning**
  - Test-based methods validate a finite set of cases.
  - Symbolic methods attempt to reason about broader input domains.
- **Loose coupling vs closed-loop integration**
  - Most neuro-symbolic approaches keep symbolic reasoning peripheral.
  - A tighter loop would allow counterexamples to directly shape repair.

### **Positioning of This Work**

- Clearly state how your work differs from prior approaches:
- **Use structured contrasts:**
  - “Unlike [category], we…”
  - “While prior work assumes [X], we instead…”
  - “Existing methods optimize for [Y], whereas we focus on [Z]”
  - Explicitly tie to:
    - broken assumptions
    - missing capabilities
    - new perspective introduced
- **Output of this section should be:**
  - A **clear differentiation statement**

---

- **Unlike LLM-based SWE agents**, we do not rely solely on execution feedback and iterative trial-and-error to guide repair.
- **Unlike standalone symbolic execution tools**, we do not treat formal reasoning as a separate verification stage detached from generation.
- **Unlike loosely coupled neuro-symbolic methods**, we integrate symbolic reasoning directly into the **inner repair loop** so that solver-produced counterexamples become actionable feedback for patch refinement.
- **While prior execution-guided methods assume tests are an adequate proxy for correctness**, we instead assume that logic-heavy bugs require feedback aligned with the program’s constraint structure.
- **Existing methods optimize primarily for task completion through behavioral validation**, whereas this work focuses on improving **logical correctness, failure diagnosis, and search efficiency** through counterexample-guided refinement.

### **Comparison Table (Concrete Summary)**

- Keep it **high-level and readable**
- Focus on **patterns**, not individual papers
- **Output of this section should be:**
  - A **quick visual summary of the design space**

---

| Papers               | Method Category                 | Core Idea                                                            | Key Assumption                                                 | Strengths                                                | Limitations                                       |
| -------------------- | ------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| SWE-agent, OpenHands | LLM-based autonomous SWE agents | Use LLMs to navigate repos, generate patches, and iterate with tools | Execution feedback plus LLM reasoning is sufficient for repair | Strong repository interaction, flexible patch generation | Weak logical guarantees, trial-and-error behavior |
|                      |                                 |                                                                      |                                                                |                                                          |                                                   |

## **Problem Formulation (What exactly are we solving?)**

- **Purpose:**
  - Define the problem in **precise, formal, and measurable terms**
  - Translate the **conceptual idea (Introduction)** into a **well-specified technical problem**
- **Key Question:**
  - _Given specific inputs and constraints, what output should the system produce, and what does “optimal” mean?_
- **Constraints:**
  - No discussion of _how_ the solution works (belongs to Proposed Technique)
  - No experimental results (belongs to Evaluation)
  - Must define all variables, assumptions, and objectives clearly
  - Should be specific enough that **multiple methods could solve this formulation**

---

### **Inputs**

- What are the **inputs to the system**?
- What information is available at decision time?
- What is the structure and representation of the inputs?
- **Output of this section should be:**
  - A **fully specified input space**

---

- The system operates on a structured software repair task defined as:

```python
task = {
    "task_id": str,
    "repo": Codebase,
    "bug_report": str | None,
    "failing_tests": list[TestCase],
    "execution_trace": list | None,
    "oracle": {
        "type": "tests | constraints | ground_truth",
        "spec": Any
    }
}
```

#### **1. Codebase (Program State)**

- A repository snapshot:
  - repo = {f_1, f_2, ..., f_n}
- Each file contains:
  - functions
  - classes
  - control flow structures
- Representations:
  - raw source code
  - [[Abstract Syntax Tree (AST)]]
  - optional [[Control Flow Graph (CFG)]] / [[Data Flow Graph(DFG)]]

#### **2. Bug Specification**

- Natural language description:
  - bug_report ∈ Text
- Optional execution signal:
  - execution_trace ∈ Trace

#### **3. Test-Based Signal**

- Failing test cases:

```python
failing_tests = [
    {
        "input": x,
        "expected": y,
        "actual": y_hat
    }
]
```

#### **4. Correctness Oracle**

- Defines what “correct” means:
  - oracle ∈ {tests, logical_constraints, ground_truth_patch}
- Examples:
  - **Tests:** pass/fail behavior
  - **Constraints:** logical invariants
  - **Ground truth:** known correct patch

#### **Formal Input Space**

- We define the input as:
  - X = (P, B, T, O)
- Where:
  - P: program (codebase)
  - B: bug specification
  - T: test signals
  - O: correctness oracle

### **Outputs**

- What decision or prediction must the system make?
- At what granularity is the output defined?
- **Output of this section should be:**
  - A **clearly defined output space**

---

- The system must produce a **program modification (patch)**:
  - patch ∈ ΔP
- Where:
  - ΔP is the space of valid edits to the program P

#### **Patch Representation**

```python
patch = {
    "file": str,
    "location": (line_start, line_end),
    "edit": str  # code diff
}
```

#### **Resulting Program**

- Applying the patch:
  - P' = P ⊕ patch

#### **Correctness Condition**

- A patch is considered **valid** if:

```python
Valid(P') ⇔
    passes_tests(P', T) ∧
    satisfies_constraints(P', O)
```

#### **Output Space**

- `Y = {patch | patch transforms P → P' such that Valid(P')}`

### **Constraints**

- What **system-level or problem-level constraints** must be satisfied?
- Categories:
  - **Memory constraints:**
    - e.g., KV cache budget ≤B\leq B≤B
  - **Latency constraints:**
    - per-step or end-to-end latency
  - **Compute constraints:**
    - FLOPs, GPU limits
  - **Quality constraints:**
    - minimum accuracy / fidelity
  - **Causality / online constraints:**
    - decisions must be made sequentially without future knowledge
- **Output of this section should be:**
  - A **set of formal constraints that define feasibility**

---

#### **1. Syntactic Constraints**

- Patch must produce:
  - P' is syntactically valid Python code

#### **2. Semantic Constraints**

- Program must satisfy oracle:
  - ∀ x ∈ InputDomain: spec(P', x) = True

#### **3. Test Constraints**

- All failing tests must pass:
- ∀ t ∈ T: execute(P', t.input) = t.expected

#### **4. Logical Consistency Constraints**

- No counterexamples exist: ¬∃ x such that ¬spec(P', x)

#### **5. Execution Constraints**

- Program must terminate: P'(x) terminates ∀ x ∈ valid inputs

#### **6. Resource Constraints**

##### **Compute**

- bounded number of iterations: iterations ≤ K

##### **Token Budget**

- total_tokens ≤ B

##### **Solver Budget**

- solver_time ≤ τ

#### **7. Feasibility Region**

- A solution is feasible if:

```
Feasible(P') ⇔
    syntactic_validity ∧
    test_pass ∧
    logical_consistency ∧
    resource_constraints
```

### **Objective Function (What does “good” mean?)**

- What are we optimizing for?
- Is the objective **explicit (mathematical)** or **implicit (proxy-based)**?

---

- We define a **multi-objective optimization problem**:

```
maximize:
    correctness(P')
    − λ₁ · cost_tokens
    − λ₂ · cost_time
    − λ₃ · num_iterations
```

#### **Primary Objective**

- Define the main goal

---

- The main goal is to produce a **functionally and logically correct patched program**.

```
correctness(P') =
1 if Valid(P')
0 otherwise
Where:
Valid(P') ⇔
    passes_tests(P') ∧
    satisfies_constraints(P')
```

- This enforces:
  - behavioral correctness (tests)
  - logical correctness (no counterexamples)

#### **Efficiency Objectives**

---

##### **Token Efficiency**

- cost_tokens = total LLM tokens used
- Measures:
  - prompt + completion usage across all iterations
- Reflects:
  - economic cost
  - search inefficiency

##### **Time Efficiency**

- cost_time = total wall-clock runtime
- Includes:
  - LLM latency
  - solver execution time
  - analysis overhead

##### **Search Efficiency**

- num_iterations = number of refinement steps until convergence
- Measures:
  - how quickly the system converges
- Lower = better-guided search

#### **Implicit Objectives**

---

- These are not directly optimized but emerge from the system design.

##### **Search Entropy Minimization**

- minimize |{distinct patches explored}|
- Encourages:
  - focused search
  - fewer redundant or oscillating patches

##### **Feedback Informativeness**

- The system implicitly aims to maximize information_gain(feedback)
- High-quality feedback should:
  - reduce ambiguity
  - directly point to failure conditions

#### **Tradeoffs**

- What competing objectives exist?
- Examples:
  - Quality vs memory
  - Latency vs accuracy
  - Throughput vs personalization

---

- The system operates under several key tradeoffs:

##### **1. Correctness vs Efficiency**

- More symbolic analysis → higher correctness
- But:
  - increased solver time
  - higher latency

##### **2. Exploration vs Convergence**

- Exploring more patches:
  - increases chance of finding correct solution
- But:
  - increases tokens and iterations

##### **3. Symbolic Precision vs Coverage**

- Strong constraints:
  - improve logical guarantees
- But:
  - may be incomplete or expensive to extract

##### **4. Neural Flexibility vs Formal Rigor**

- LLM:
  - flexible, creative
- Solver:
  - precise, rigid
- Symbiotic-SWE balances: flexible proposal ↔ formal verification

### **Assumptions**

- What assumptions are required to make the problem tractable?
- Examples:
  - Retrieval scores are available and meaningful
  - Attention reflects relevance
  - Data distribution is stationary
  - Errors are independent across steps
- **Output of this section should be:**
  - A **list of modeling assumptions**

---

#### **1. Oracle Assumptions**

- Test suites are:
  - partially correct but possibly incomplete
- Logical constraints (if available) are:
  - sound representations of intended behavior

#### **2. Symbolic Execution Assumptions**

- Program slices are:
  - small enough for tractable symbolic execution
- Constraints can be:
  - expressed in SMT-compatible form

#### **3. LLM Assumptions**

- The LLM can:
  - interpret natural language critiques
  - refine patches based on structured feedback

#### **4. Feedback Assumptions**

- Counterexamples:
  - correspond to meaningful failure modes
- Mapping from symbolic failure → natural language:
  - preserves key information

#### **5. Task Assumptions**

- Bugs are:
  - localized enough to be fixed with small edits
- Correct solutions exist within:
  ΔP (patch search space)

#### **6. Independence Assumptions**

- Iterations are treated as:
  - sequential refinements
- Errors are:
  - partially independent across iterations

### **Evaluation Alignment (VERY IMPORTANT)**

- How does this formulation map to evaluation?
- What will be measured?
- What constitutes success or failure?
- Example:
  - Success = minimal drop in F1 under memory constraint
  - Failure = degradation beyond threshold δ\deltaδ
- **Output of this section should be:**
  - A **direct bridge to your Evaluation section**

---

#### **Mapping Objective → Metrics**

| Objective Component     | Evaluation Metric        |
| ----------------------- | ------------------------ |
| correctness(P')         | Bug Resolution Rate      |
| logical correctness     | Logical Correctness Rate |
| regression minimization | Regression Rate          |
| cost_tokens             | Tokens-per-Success       |
| cost_time               | Time-to-Success          |
| num_iterations          | Iterations-to-Success    |

#### **Success Criteria**

- A task is considered **successful** if Valid(P') = True
  - passes all tests
  - no counterexamples found

#### **Efficiency Success Criteria**

- A method is considered more efficient if it:
  - achieves higher success rate with:
    - fewer tokens
    - fewer iterations
    - lower runtime

#### **Failure Criteria**

- A task is considered a **failure** if no valid patch found within:
  - iteration ≤ K OR token budget ≤ B
- OR:
  - patch:
    - passes tests but fails logical constraints

#### **System-Level Evaluation Alignment**

- Objective encourages:
  - low entropy search + high signal feedback
- Measured via:
  - number of distinct patches explored
  - repeated failure rate
  - solver outcome distribution

## **Proposed Technique (What did I build?)**

- **Purpose:**
  - Describe the **method/system** designed to solve the problem
  - Translate the **problem formulation → concrete solution**
- **Key Question:**
  - _What is the system, how is it structured, and why should it work?_
- **Constraints:**
  - No problem motivation (belongs to Introduction)
  - No comparison to prior work (belongs to Related Work)
  - No experimental results (belongs to Evaluation)
  - Must clearly separate:
    - **Concept (WHY)**
    - **Design (WHAT)**
    - **Execution (HOW)**

---

### **Hypothesis (Driving Claim)**

- State the **core hypothesis** of your approach
- **Format:**
  - _If we [do X], then [desired outcome Y], because [reason Z]_
- Example:
  - If we prioritize semantically relevant chunks during decoding, then we can preserve generation quality under memory constraints, because attention reflects contextual utility.
- **Output of this section should be:**
  - A **testable, mechanism-linked hypothesis**

---

- If we integrate symbolic execution into the agent loop to generate **minimal, concrete counterexamples over relevant program slices**, then the agent will **converge more reliably and efficiently to correct patches**, because:
  - counterexamples expose **exact failure conditions**
  - constraints eliminate **invalid regions of the patch search space**
  - feedback becomes **deterministic and verifiable**, rather than heuristic

### **System Design (WHAT is built)**

- Describe the **architecture of your system**
- **Output of this section should be:**
  - A **clear system architecture + pipeline**

---

#### **High-Level Pipeline**

- Describe the system as a sequence of stages:
- Example:
  1.  Input processing
  2.  Feature extraction
  3.  Decision module
  4.  Output generation

---

1. Setup
   - fill out the readme
   - setup repo + project folders
   - download dependencies
2. **Data Processing**
   - ingest bug report, repository, failing tests
3. **Context Retrieval**
   - select relevant code regions
4. **Neural Proposal**
   - LLM generates candidate patch
5. **Impact Slicing**
   - isolate affected program regions
6. **Constraint Extraction**
   - convert code behavior → symbolic constraints
7. **Symbolic Verification**
   - solver searches for violating inputs
8. **Counterexample Generation**
   - produce failing input (if exists)
9. **Feedback Transformation**
   - convert symbolic failure → natural language critique
10. **Patch Refinement (CEGF Loop)**
    - update patch using critique
11. **Termination**
    - stop when no counterexamples OR iteration limit reached

#### **Data Lifecycle**

##### **Dataflow Example**

- Bug: division by zero when list is empty
- Repo contains:

```python
def sum_list(lst):
    return sum(lst)/len(lst)
```

- **Bug report:** `"Function fails when list is empty"`
- **Expected behavior:** return `0` when `lst == []`

##### **End-to-end dataflow w/ manipulations**

1. Load task
   - The system first loads a structured repair task containing:
     - repository snapshot
     - bug report
     - failing tests
     - optional execution trace / oracle
   - Manipulation:
     - raw benchmark fields are normalized into a canonical task object
     - repository is materialized locally
2. Parse and index the repository
   - The system parses the repository once and builds reusable structural metadata.
   - Manipulation:
     - source files → ASTs
     - file contents → symbol table
     - imports / function references → repository graph
3. Select relevant context from the local repository
   - The system identifies the code regions most relevant to the bug report and failing test.
   - Manipulation:
     - task + repo index → candidate files/functions/tests
     - local context selection reduces prompt noise
4. Construct the neural proposal prompt
   - The selected context is converted into the input prompt for the LLM.
   - Manipulation:
     - bug report + failing tests + code context → prompt
5. Generate candidate patch
   - The LLM proposes a candidate code change.
   - Manipulation:
     - prompt text → candidate patch / diff
6. Apply patch and isolate impacted program region
   - The candidate patch is applied to a temporary working copy and the system identifies which program region should be symbolically analyzed.
   - Manipulation:
     - diff → patched source
     - patched source + AST → impacted function / variables / conditions
7. Extract symbolic constraints
   - The system translates the sliced program behavior into logical constraints suitable for the solver.
   - Manipulation:
     - Python code + type/domain assumptions → symbolic variables + path conditions + postconditions
8. Run symbolic verification
   - The solver checks whether the patched program violates any of the logical constraints.
   - Manipulation:
     - symbolic problem → SAT / UNSAT / UNKNOWN / TIMEOUT
9. Generate counterexample
   - If the solver finds a violating assignment, the system converts it into a concrete counterexample.
   - Manipulation:
     - solver model → failing input + failure description
10. Transform symbolic failure into critique
    - The counterexample is converted into natural-language feedback for the next patch iteration.
    - Manipulation:
      - structured symbolic failure → concise natural-language critique
11. Refine patch using counterexample-guided feedback
    - The critique is fed back into the next LLM prompt.
    - Manipulation:
      - previous prompt + previous patch + critique → refined prompt → refined patch
12. Repeat until convergence
    - The same lifecycle repeats until:
      - no counterexample is found
      - iteration budget is exhausted
    - Manipulation:
      - iterative update of:
        - patch
        - slice
        - symbolic constraints
        - solver outputs
        - critiques

#### **Datastructures**

1. TaskObject (Canonical Input Representation)
   ```python
   TaskObject = {
   "task_id": str,
   "repo_path": str,
   "bug_report": str,
   "failing_tests": list[dict],
   "execution_trace": list | None,
   # metadata
   "repo_name": str,
   "base_commit": str,
   "dataset": str,
   }
   ```
   - Purpose:
     - Unified representation of a bug-fixing task
     - Entry point for the entire pipeline
2. RepoIndex (Static Program Representation)
   ```python
   RepoIndex = {
   "files": dict[str, str],              # filepath → source code
   "ast_map": dict[str, AST],            # filepath → AST
   "symbol_table": dict[str, dict],      # symbol → metadata
   "import_graph": dict[str, list[str]],
   "call_graph": dict[str, list[str]],
   }
   ```
   - Purpose:
     - Parsed, structured view of the repository
   - Enables:
     - context selection
     - slicing
     - dependency reasoning
3. Context Object (Pre-Neural Selection)
   ```python
   Context = {
   "relevant_files": list[str],
   "relevant_functions": list[str],
   "relevant_tests": list[str],
   "code_chunks": list[str],
   }
   ```
   - Purpose:
     - Reduced, task-specific view of the repo
     - Used to construct the LLM prompt
4. Prompt Object
   ```python
   Prompt = {
   "bug_report": str,
   "code_context": list[str],
   "failing_tests": list[str],
   "previous_patch": str | None,
   "critique": str | None,
   }
   ```
   - Purpose:
     - Structured input to the LLM
     - Evolves across iterations
5. Patch Object
   ```python
   Patch = {
   "iteration": int,
   "target_file": str,
   "diff": str,
   "applied": bool,
   }
   ```
   - Purpose:
     - Represents a candidate code modification
     - Central object in the CEGF loop
6. Program Slice (Post-Patch Structural Focus)
   ```python
   ProgramSlice = {
   "functions": list[str],
   "variables": list[str],
   "conditions": list[str],
   "source_snippet": str,
   }
   ```
   - Purpose:
     - Narrowed region for symbolic reasoning
     - Reduces solver complexity
7. Symbolic Problem (Constraint Representation)
   ```python
   SymbolicProblem = {
   "function_name": str,
   "variables": dict[str, str],          # var → type
   "path_constraints": list[str],
   "postconditions": list[str],
   }
   ```
   - Purpose:
     - Formal encoding of program behavior
     - Input to solver
8. Solver Result
   ```python
   SolverResult = {
   "status": str,   # "sat" | "unsat" | "unknown" | "timeout"
   "model": dict | None,
   "violated_property": str | None,
   }
   ```
   - Purpose:
     - Output of symbolic verification
     - Determines whether refinement is needed
9. Counterexample
   ```python
   Counterexample = {
   "inputs": dict,
   "observed_failure": str,
   "violated_property": str,
   "affected_function": str,
   }
   ```
   - Purpose:
     - Concrete failing case derived from solver
     - Bridges symbolic → concrete
10. Critique Object (Feedback Representation)
    ```python
    Critique = {
    "text": str,
    "structured": {
    "function": str,
    "inputs": dict,
    "error": str,
    }
    }
    ```
    - Purpose:
      - Converts failure into actionable feedback
      - Used for patch refinement
11. Iteration State (Core Loop State Object)
    ```python
    IterationState = {
    "task": Task,
    "context": Context,
    "prompt": Prompt,
    "patch": Patch,
    "slice": ProgramSlice,
    "symbolic_problem": SymbolicProblem,
    "solver_result": SolverResult,
    "counterexample": Counterexample | None,
    "critique": Critique | None,
    }
    ```
    - Purpose:
      - Captures the full state at each iteration
    - Enables:
      - debugging
      - logging
      - replay
12. Run Metadata
    ```python
    RunMetadata = {
    "run_id": str,
    "config": dict,
    "tasks": list[str],
    "start_time": str,
    "end_time": str,
    }
    ```
    - Purpose:
      - Tracks experiment-level execution
      - Ensures reproducibility
13. Final Result Object
    ```python
    FinalResult = {
    "task_id": str,
    "success": bool,
    "final_patch": Patch,
    "num_iterations": int,
    "termination_reason": str,
    }
    ```
    - Purpose:
      - Final output used for evaluation

#### **System Components**

- Define:
  - components
  - dataflow
  - interactions

---

1. Task Loader & Normalizer
   - Role:
     - Ingest raw benchmark data and convert it into a canonical task representation
   - Input → Output:
     - Input:
       - raw dataset entry (JSON / SWE-bench row)
     - Output:
       - Task object (normalized schema)
   - Interaction:
     - Feeds into Repository Indexer
     - Initializes the Iteration State
2. Repository Indexer (Static Analysis Layer)
   - Role:
     - Parse and structure the repository into reusable program representations
   - Input → Output:
     - Input:
       - Task.repo_path
     - Output:
       - RepoIndex (ASTs, symbol table, graphs)
   - Interaction:
     - Used by Context Selector and Impact Slicer
     - Cached and reused across iterations
3. Context Selector (Bug Localization Layer)
   - Role:
     - Identify the most relevant code regions for the bug
   - Input → Output:
     - Input:
       - Task
       - RepoIndex
     - Output:
       - Context (relevant files, functions, code chunks)
   - Interaction:
     - Feeds into Prompt Builder
     - Reduces input size and noise for the LLM
4. Prompt Builder
   - Role:
     - Construct structured prompts for the LLM using task + context + feedback
   - Input → Output:
     - Input:
       - Task
       - Context
       - optional Critique
       - optional previous Patch
     - Output:
       - Prompt
   - Interaction:
     - Feeds into Neural Patch Generator
     - Updated every iteration
5. Neural Patch Generator (LLM Agent)
   - Role:
     - Generate candidate patches using the LLM
   - Input → Output:
     - Input:
       - Prompt
     - Output:
       - Patch
   - Interaction:
     - Feeds into:
       - Patch Applier
       - Impact Slicer
     - Receives feedback via updated prompts
6. Patch Applier
   - Role:
     - Apply candidate patches to a temporary working copy of the repository
   - Input → Output:
     - Input:
       - Patch
       - Task.repo_path
     - Output:
       - patched repository state
   - Interaction:
     - Feeds into:
       - Impact Slicer
       - optional test execution
     - Ensures isolation via per-task workspace
7. Impact Slicer (Post-Patch Localization)
   - Role:
     - Identify the program region affected by the patch for analysis
   - Input → Output:
     - Input:
       - patched code
       - RepoIndex
       - Patch
     - Output:
       - ProgramSlice
   - Interaction:
     - Feeds into Constraint Extractor
     - Reduces symbolic reasoning scope
8. Constraint Extractor
   - Role:
     - Convert program behavior into a formal symbolic representation
   - Input → Output:
     - Input:
       - ProgramSlice
     - Output:
       - SymbolicProblem
   - Interaction:
     - Feeds into Symbolic Verifier
     - Encodes logic for solver reasoning
9. Symbolic Verifier (Solver Engine)
   - Role:
     - Check whether the patch satisfies logical constraints
   - Input → Output:
     - Input:
       - SymbolicProblem
     - Output:
       - SolverResult (sat / unsat / unknown / timeout)
   - Interaction:
     - If sat → passes to Counterexample Generator
     - If unsat → signals termination
10. Counterexample Generator
    - Role:
      - Convert solver output into a concrete failing input
    - Input → Output:
      - Input:
        - SolverResult
      - Output:
        - Counterexample
    - Interaction:
      - Feeds into Feedback Generator
      - Bridges symbolic → concrete domain
11. Feedback Generator (Critique Builder)
    - Role:
      - Translate counterexamples into natural-language critiques
    - Input → Output:
      - Input:
        - Counterexample
      - Output:
        - Critique
    - Interaction:
      - Feeds back into Prompt Builder
      - Drives the CEGF loop
12. Iteration Controller (CEGF Loop Manager)
    - Role:
      - Manage iterative refinement and termination conditions
    - Input → Output:
      - Input:
        - IterationState
        - SolverResult
      - Output:
        - updated IterationState
        - final termination decision
    - Interaction:
      - Coordinates:
        - patch generation
        - symbolic verification
        - feedback loop
      - Enforces:
        - max iterations
        - convergence criteria
13. Evaluation Engine
    - Role:
      - Measure system performance across tasks and runs
    - Input → Output:
      - Input:
        - FinalResult
        - run artifacts
      - Output:
        - metrics (accuracy, iterations, tokens, runtime)
    - Interaction:
      - Consumes outputs from Iteration Controller
      - Produces results for analysis

### **Execution Details (HOW it works)**

- Provide a **step-by-step breakdown**
- **Output of this section should be:**
  - A **fully specified execution process**

---

#### \*\*0. Pipeline

##### **0. Setup**

###### **Key Components / Deliverables**

- Project repository
- local code environment setup
  - version control
  - tooling
  - logging
  - ci/cd pipeline
  - file structure
- Core Schemas
- Core constants
- Basic README
- [[Symbiotic-SWE-README]]

###### **Low-level Pipeline Steps**

- mention Failure Modes
- mention Tests

1. Setup version control + experiment tracking
   1. Initialize git repo
   2. Add:
      - .gitignore (exclude artifacts, caches)
   3. Define commit conventions
   4. Track:
      - config versions
      - schema versions
2. Choose tooling
3. Setup logging + Observability
   1. Run logs
   2. Error logs
   3. Solver logs
   4. Patch logs
   5. Failure logs for:
      1. patch apply failure
      2. AST parse failure
      3. solver timeout
      4. unsupported symbolic construct
4. Setup environment + dependency management
   1. Create:
      - pyproject.toml
   2. Create reproducible environment:
      - poetry
      - venv
5. Setup CI/CD
6. Define datastructure schemas / dataclasses
   - `TaskObject`
   - `RepoIndex`
7. Add schema validation / smoke validation
   1. validating config files
   2. validating task schema
   3. validating artifact schema round-trips
8. Define Constants
9. Initialize repository structure aligned to pipeline stages
   1. Create top-level directories:
      - src/ (core logic)
      - data/
        - raw/
        - processed/
        - benchmarks/
      - tests/
      - docs/
   2. Subdivide src/ into pipeline modules:
      - pipeline/ (orchestration)
      - dataset/
        - main Task Loader & Normalizer module
        - main Repository Indexer (Static Analysis Layer) module
      - context_selection/ (NOT RAG)
        - main Context Selector (Bug Localization Layer) module
      - patch_generation/
      - slicing/
      - symbolic/
      - feedback/
      - evaluation/
10. Write README + developer documentation
    1. Include:
       - project overview
       - pipeline stages
       - setup instructions
       - how to run:
         - single task
         - benchmark
         - artifact structure
    2. Add:
       - expected outputs
       - common failure cases

##### \*\*1. Data Processing

###### Key Components / Deliverables

- Task Loader & Normalizer
- Repository Indexer (Static Analysis Layer)

###### **Low-level Pipeline Steps**

- mention Failure Modes
- mention Tests

1. Implement Task Loader & Normalizer
   1. Create a Task Loader Module in `~/dataset/task_loader.py`
      1. Read benchmark entries from:
         - SWE-bench Verified subset
         - optional synthetic HumanEval bug tasks later
      2. Extract raw fields needed for each task and populate `TaskObject`:
         - task id
         - repo identifier
         - base commit
         - bug report / problem statement
         - failing tests
         - optional patch / oracle fields
      3. Validate required fields before further processing
      4. Skip or log malformed tasks
      5. Filter and select usable tasks
         1. Restrict to selected repositories if needed:
            - sympy
            - pandas
            - numpy
            - scikit-learn
            - matplotlib
         2. Apply logic-heavy heuristics:
            - patch modifies conditional logic or comparisons
            - issue text suggests edge cases / wrong logic / assertions
         3. Remove tasks with:
            - dependency changes
            - import fixes
            - config changes
            - large refactors
         4. Create three task subsets:
            - smoke tasks
            - dev tasks
            - final evaluation tasks
   2. Create a Task Normalizer module `~/dataset/task_normalizer.py`
      1. Normalize tasks into canonical internal schema
         1. Convert benchmark-specific fields into one shared Task object
         2. Assign stable task_id
         3. Attach metadata:
            - dataset source
            - repo name
            - logic-heavy label
            - bug-type label if available
         4. Preserve raw benchmark fields separately for traceability
         5. Write normalized task artifacts to disk
2. Implement Repository Indexer (Static Analysis Layer) in `~/dataset/repo_indexer.py`
   1. Load bug specification and validation signals
      1. Persist bug report / issue description
      2. Persist failing test identifiers
      3. Persist optional execution trace if available
      4. Persist optional oracle fields:
         1. gold patch
         2. test patch
      5. constraint specification if available
      6. Merge these into the canonical task artifact
   2. Parse and index repository once
      1. Traverse all Python files in the repository
      2. Parse each file into an AST
      3. Extract file-level metadata:
         1. imports
         2. source/test role
         3. top-level symbols
      4. Extract symbol-level metadata:
         1. functions
         2. classes
         3. line spans
      5. Build reusable repo indexes:
         1. filepath -> AST
         2. symbol table
         3. import graph
         4. call graph if available
      6. Record parse failures without crashing the task
      7. Cache the index for later stages
   3. Construct final prepared task artifact
      1. Merge:
         1. normalized task metadata
         2. local repo path
         3. bug report
         4. failing tests
         5. execution trace
         6. repo index references
      2. Mark task status:
         1. valid
         2. partial
         3. invalid
      3. Attach schema version + preprocessing timestamp
      4. Write one canonical task.json per valid task

##### **2. Context Retrieval**

###### **Key Components / Deliverables**

- Context Selector (Bug Localization Layer)
- Prompt Builder

###### **Low-level Pipeline Steps**

- mention Failure Modes
- mention Tests

## **Experimental Evaluation (Did it work?)**

- **Purpose:**
  - Empirically evaluate whether the proposed method satisfies the **hypothesis and objectives** defined earlier
  - Provide **quantitative and qualitative evidence**
  - Research Questions → Metrics → Setup → Plan → Results → Analysis → Limitations
- **Key Question:**
  - _Does the proposed method work, under what conditions, and why?_
- **Constraints:**
  - No explanation of how the system works (belongs to Proposed Technique)
  - No restating problem motivation (belongs to Introduction)
  - Every result must map to:
    - a **research question**
    - a **metric**
  - Separate clearly:
    - **what is being tested**
    - **how it is tested**
    - **what the results are**
    - **why the results occur**

---

### **Research Questions (What are we testing?)**

- Define the **key questions your evaluation answers**
- Each should map to:
  - hypothesis
  - contribution
- **Output of this section should be:**
  - A **small set of testable evaluation questions**

---

#### **Effectiveness**

- Does the method improve task performance?
- Does it achieve the intended objective?

---

- **RQ1:** Does Symbiotic-SWE achieve a higher **bug resolution rate** than neural-only agents on logic-heavy tasks?
- **RQ2:** Does Symbiotic-SWE improve **logical correctness**, beyond simply passing tests?
- **RQ3:** Does Symbiotic-SWE reduce **logical regressions** (patches that pass tests but violate invariants)?

#### **Efficiency**

- Does the method improve resource usage?
- Memory, latency, throughput?

---

- **RQ4:** Does Symbiotic-SWE reduce the **number of iterations** required to reach a correct solution?
- **RQ5:** Does it reduce **token usage per successful repair**?
- **RQ6:** What is the **systems overhead** introduced by symbolic execution, and is it offset by faster convergence?

#### **Quality of Behavior / Decisions**

- Does the system make better intermediate decisions?
- Are outputs more stable, relevant, or consistent?

---

- **RQ7:** Do counterexample-based critiques lead to **more targeted and stable patch updates**?
- **RQ8:** Does the system reduce **repeated failure modes across iterations**?
- **RQ9:** Does symbolic feedback improve the **quality and usefulness of intermediate reasoning**?

#### _(Optional)_ Additional RQs:

- Robustness
- Generalization
- Scalability

---

-

### **Evaluation Setting (What environment are we testing in?)**

- **Output of this section should be:**
  - A **fully specified evaluation environment**

---

#### Benchmarks

##### **Primary benchmark**

- We evaluate on **SWE-bench Verified**, a curated set of real-world software engineering bug-fixing tasks consisting of human-validated issue descriptions, repository snapshots, and failing tests. This benchmark enables evaluation of end-to-end repair performance in realistic development settings.
- However, since SWE-bench primarily evaluates correctness via **test-passing behavior**, it does not fully capture **logical correctness beyond test coverage**.
- To address this limitation, we additionally construct a **small synthetic benchmark of logic bugs derived from HumanEval problems**, where ground-truth behavior is known and logical errors can be precisely characterized. This allows us to directly evaluate whether counterexample-guided feedback improves **semantic correctness**, not just test satisfaction.

###### SWE-bench Verified

- In addition to overall performance, we focus on a **logic-heavy subset of tasks**, where symbolic reasoning is expected to provide the greatest benefit.
- This subset is central to our evaluation, as it isolates scenarios where **execution-based feedback is insufficient** and **constraint-based reasoning is required**.
- **40 tasks total**
  - 15-25 logic-heavy tasks
  - 3-5 task for smoke testing
  - Keep tasks with
    - arithmetic predicate bugs
    - relational operator bugs
    - assertion-violation bugs
    - multi-conditional reasoning bugs
    - bugs whose fixes primarily modify **logical conditions or expressions**, rather than requiring large structural or architectural changes
    - patch modifies:
      - `if`, `elif`, `else`
      - boolean expressions
      - comparison operators (`<, >, ==, !=`)
      - arithmetic logic
    - bug involves:
      - edge cases
      - incorrect conditions
      - wrong return logic
  - Remove tasks where
    - patch involves:
      - dependency changes
      - import fixes
      - file I/O
      - config changes
      - large refactors (> ~20–30 lines changed)
    - bug description mentions:
      - “missing file”
      - “API change”
      - “version mismatch”
  - Repos
    - `sympy` → symbolic math logic (BEST FIT)
    - `pandas` → condition handling, edge cases
    - `numpy` → numerical edge cases
    - `scikit-learn` → validation logic
    - `matplotlib` → conditional rendering logic

###### HumanEval Synthetic Benchmark

##### **Benchmark outputs to compare**

We evaluate both **end-to-end performance** and **internal system behavior** using the following metrics:

- **Task Resolution Rate**
  - Percentage of tasks successfully fixed
- **Repair Efficiency**
  - number of repair iterations
  - total token consumption
  - wall-clock runtime
- **Solver Overhead**
  - fraction of total runtime spent in symbolic execution and constraint solving
- **Feedback Quality**
  - critique usefulness and specificity (via LLM-as-judge and qualitative analysis)
- **Search Behavior** - regression rate (patches that pass tests but remain logically incorrect) - repeated failure rate across iterations
  These metrics allow us to evaluate not only whether the system succeeds, but **how it arrives at a solution**.

#### **Baselines**

- What methods are you comparing against?
- Why are they relevant?

---

##### **Primary Baseline**

- **Vanilla SWE-agent**
  - Uses the same LLM (GPT-4o) and retrieval setup
  - Relies solely on **execution-based feedback (tests)**
  - Serves as the primary point of comparison for real-world repair performance

##### **Additional Baselines**

- **Chain-of-Thought Agent**
  - Uses structured reasoning in natural language
  - Does not incorporate external verification or symbolic feedback
- **Execution-Only Agent**
  - Iteratively refines patches using test outcomes only
  - Lacks constraint-based validation
- **Ablation Variants**
  - **Neural + Slicing (no solver):** evaluates impact of structural localization without symbolic reasoning
  - **Neural + Solver (no counterexample feedback):** evaluates whether verification alone improves performance without feedback integration
  - **Neural + CEGF (no slicing):** evaluates the role of precise localization in enabling effective symbolic reasoning

##### **Fairness Constraints**

- To ensure a fair comparison, all methods share the same:
  - LLM model (GPT-4o)
  - maximum token budget
  - maximum number of iterations
  - retrieval and context construction setup
- The **only difference** between methods is the presence or absence of:
  - symbolic constraint extraction
  - solver-based verification
  - counterexample-guided feedback (CEGF)

#### **Metrics**

##### **1. Effectiveness Metrics**

- **Bug Resolution Rate**
  - Accuracy = (# successfully resolved bugs) / (total bugs)
- **Logical Correctness Rate**
  - % of patches that satisfy symbolic constraints (solver UNSAT)
- **Regression Rate**
  - Regression Rate = (# patches that pass tests but fail logic) / (# patches)

##### **2. Efficiency Metrics**

- **Iterations to Success**
  - Avg Iterations = mean(iterations until success)
- **Tokens-per-Success (TPS)**
  - TPS = (# successful tasks) / (total tokens used)
- **Time-to-Success**
  - Time = wall-clock time until resolution
- **Solver Overhead**
  - Solver Overhead = solver_time / total_runtime
- **Per-Stage Latency Breakdown**
  - retrieval time
  - LLM generation time
  - slicing time
  - constraint extraction time
  - solver time

##### **3. Feedback Quality Metrics**

- **Failure Resolution Efficiency**
  - \# of iterations after first failure until success
- **Repeated Failure Rate**
  - (# repeated counterexamples) / (# iterations)
- **Critique Utility Score (LLM-as-Judge)**
  - Rate critique on:
    - correctness
    - specificity
    - usefulness for fixing bug
- **Patch Stability**
  - whether fixes introduce new bugs in later iterations

##### **4. System-Level Metrics (Important for your paper)**

- **Search Entropy Proxy**
  - number of distinct patches explored before success
- **Constraint Coverage**
  - % of program slice successfully encoded into SMT
- **Solver Outcome Distribution**
  - {sat, unsat, unknown, timeout}

##### **5. Proxy Metrics (if needed)**

- If true objective is not directly measurable, define proxies:
- Examples:
  - F1 score / exact match
  - Perplexity
  - Attention-weight preservation
  - Task success rate
- **Output of this section should be:**
  - A **clear definition of optimality + tradeoffs**

---

- Since correctness is binary and logical correctness may be expensive to fully verify, we use proxies:

###### **1. Task Success Rate**

- success_rate = # successful patches / total tasks

###### **2. Logical Correctness Rate**

- % of patches with no counterexamples (UNSAT)

###### **3. Regression Rate**

- % of patches that pass tests but violate constraints

###### **4. Tokens-per-Success (TPS)**

- TPS = successful_tasks / total_tokens

###### **5. Iterations-to-Success**

- Average iterations required to converge

### **Evaluation Plan (How will we test it?)**

- **Output of this section should be:**
  - A **reproducible experimental procedure**

---

#### **Experiment Structure**

- What experiments are run?
- What variables are controlled vs varied?

---

- We evaluate Symbiotic-SWE through a set of controlled experiments designed to isolate the impact of **symbolic verification and counterexample-guided feedback (CEGF)**.

1. **(A) End-to-End Performance Comparison**
   - Compare:
     - Symbiotic-SWE
     - Vanilla SWE-agent
     - Additional baselines (CoT-only, execution-only)
   - Measure:
     - effectiveness (success rate)
     - efficiency (tokens, iterations, time)
     - behavior (failure patterns, critique quality)
2. **(B) Logic-Heavy Task Evaluation**
   - Focus on subset of tasks involving:
     - conditional logic
     - edge cases
     - invariant violations
   - Goal:
     - isolate scenarios where symbolic reasoning should provide the most benefit
3. **(C) Spec-Based Evaluation (Optional but Strong)**
   - Evaluate using:
     - constraint-based oracles
   - Goal:
     - measure correctness beyond test coverage

##### **Controlled Variables**

- LLM model (GPT-4o)
- prompt format
- token budget
- iteration limit
- retrieval pipeline
- execution environment

##### **Independent Variables (Varied)**

- presence of symbolic execution
- presence of counterexample feedback
- slicing enabled vs disabled
- solver configuration (timeout, depth)

#### **Execution Loop**

- How is each experiment executed?
- Example:
  1.  Load input
  2.  Run system
  3.  collect outputs
  4.  compute metrics

---

- Each experiment follows a standardized execution pipeline:

1. **Load Input**
   - task (repo, bug report, tests, oracle)
2. **Initialize System State**
   - empty patch history
   - iteration counter
   - token tracker
3. **Run Repair Loop**
   - generate patch
   - validate via:
     - tests (execution)
     - solver (symbolic)
4. **Collect Outputs**
   - final patch
   - iteration trace
   - counterexamples
   - critiques
5. **Compute Metrics**
   - correctness
   - efficiency
   - system-level stats

#### **Aggregation**

- How are results aggregated?
- Mean, median, variance?

---

- **Primary Aggregation Methods**
  - **Mean**:
    - average success rate
    - average tokens
    - average iterations
  - **Median**:
    - robust central tendency for skewed distributions
  - **Variance / Standard Deviation**:
    - measure consistency across tasks
- **Additional Aggregations**
  - **Per-category breakdown**
    - logic-heavy vs non-logic-heavy tasks
  - **Distributional analysis**
    - histogram of iterations-to-success
    - solver outcome distribution

#### **Ablation Grid (Experimental Design Space)**

- Define variations of the system
- **Output of this section should be:**
  - A **structured experimental grid**

---

##### **Baseline Systems**

- Vanilla SWE-agent
- Chain-of-Thought-only repair agent

##### **System Variants**

- Neural-only agent
- Neural + Impact Slicing
- Neural + Symbolic Verification (no critique injection)
- Neural + Counterexample Guided Feedback (no slicing)
- Full Symbiotic-SWE

##### **Constraint Source Variants**

- Assertions only
- Type hints only
- Assertions + type hints
- Assertions + type hints + inferred contracts
- Assertions + type hints + inferred contracts + optional LLM-generated invariants

##### **Retrieval Variants**

- Semantic retrieval only
- Semantic retrieval + structural expansion

##### **Termination / Budget Variants**

- max iterations = 1, 2, 3, 5
- solver timeout thresholds

##### **Critique Variants**

- raw solver output
- structured critique template
- structured critique + light LLM rewrite

- We perform ablations to isolate the contribution of each component in the system.

| Component                   | Enabled                          |
| --------------------------- | -------------------------------- |
| Full System (Symbiotic-SWE) | ✓                                |
| Neural Only                 | ✓ (no solver, no CEGF)           |
| Neural + Slicing            | ✓ (no solver)                    |
| Neural + Solver (No CEGF)   | ✓ (solver without feedback loop) |
| Neural + CEGF (No Slicing)  | ✓ (feedback but no slicing)      |

#### **Statistical Analysis**

- Confidence intervals
- significance testing
- variance analysis

---

- To ensure results are reliable and not due to randomness

1. Confidence Intervals
   - Compute:
     - 95% CI = mean ± 1.96 \* (σ / √n)
   - Applied to:
     - success rate
     - tokens-per-success
     - iterations-to-success
2. Significance Testing
   - Use:
     - paired t-test (same tasks across methods)
     - or bootstrap resampling
   - Compare:
     - Symbiotic-SWE vs baseline
3. Variance Analysis
   - Analyze:
     - variability across tasks
     - stability of convergence
4. Effect Size (Optional but Strong)
   - Measure magnitude of improvement: effect_size = (mean_A - mean_B) / std_dev

#### **Diagrams (System Visualization Layer)**

- Visual representations of the system
- **Output of this section should be:**
  - A **visual understanding of system + artifacts**

---

##### **System Overview Diagram**

- Bug Report → Context Retrieval → Neural Proposal → Impact Slicing → Constraint Extraction → Symbolic Execution → Counterexample Generation → Feedback Transformation → CEGF Loop

##### **Dataflow Diagram**

- task instance → repo context → patch diff → program slice → SMT constraints → solver result → critique → refined patch

##### **Repair Loop Diagram**

- shows the closed-loop interaction between the LLM and symbolic solver

##### **Artifact Flow Diagram**

- maps which files are consumed and produced at each stage

##### **Failure Mode Diagram**

- shows branching outcomes such as:
  - patch parse failure
  - unsupported symbolic construct
  - solver SAT / UNSAT / UNKNOWN / TIMEOUT

##### **Ablation Diagram**

- full Symbiotic-SWE vs. stripped variants:
  - neural only
  - neural + slicing
  - neural + solver without critique
  - neural + critique without slicing
  - full system

### **Threats to Validity (How could this be wrong?)**

- What could invalidate your conclusions?
- Types:
  - dataset bias
  - metric limitations
  - experimental setup bias
  - implementation artifacts
- **Output of this section should be:**
  - A **critical reflection on limitations of evaluation**

---

#### **1. Dataset Bias**

- **Description**
  - The dataset may not accurately represent the full distribution of real-world software bugs.
- **Potential Issues**
  - Overrepresentation of:
    - logic-heavy bugs (aligned with system strengths)
  - Underrepresentation of:
    - large-scale refactoring bugs
    - API misuse
    - multi-file architectural issues
  - Synthetic bug generation may:
    - simplify real-world complexity
    - introduce unrealistic patterns
- **Impact**
  - Results may overestimate performance on logic-constrained, small-scope bugs
  - May not generalize to real-world, long-horizon software engineering tasks
- **Mitigation**
  - Include:
    - curated real-world bugs
    - diverse bug categories
  - Report results separately:
    - synthetic vs real tasks

#### **2. Metric Limitations**

- **Description**
  - Metrics may not fully capture the true quality of generated patches.
- **Potential Issues**
  - **Binary correctness (Valid / Invalid):**
    - ignores partial correctness
    - does not capture code quality
  - **Logical correctness via solver:**
    - limited by:
      - constraint coverage
      - expressibility in SMT
  - **LLM-as-judge (for feedback quality):**
    - subjective
    - potentially biased
- **Impact**
  - System may appear better or worse depending on what is measured vs what is ignored
- **Mitigation**
  - Use multiple metrics:
    - correctness
    - regression rate
    - efficiency
  - report:
    - solver coverage
    - failure distributions

#### **3. Experimental Setup Bias**

- **Description**
  - Differences in configuration may unintentionally favor one method over another.
- **Potential Issues**
  - Prompt design:
    - tuned for Symbiotic-SWE
  - Iteration limits:
    - may advantage methods with stronger feedback
  - Solver configuration:
    - timeout thresholds affect results
- **Impact**
  - Improvements may reflect setup choices rather than inherent method superiority
- **Mitigation**
  - Enforce fairness:
    - same LLM
    - same token budget
    - same iteration limit
  - perform:
    - ablation studies
    - sensitivity analysis

#### **4. Implementation Artifacts**

- **Description**
  - Engineering details may influence results independently of the core method.
- **Potential Issues**
  - Bugs in:
    - constraint extraction
    - slicing
    - patch application
  - Logging or caching effects:
    - repeated runs not independent
  - Solver integration issues:
    - inconsistent behavior across runs
- **Impact**
  - Observed improvements may be partially due to implementation-specific effects
- **Mitigation**
  - modularize components
  - validate each stage independently
  - include:
    - sanity checks
    - debugging artifacts

#### **5. Oracle and Validation Bias**

- **Description**
  - The definition of correctness may be incomplete or inconsistent.
- **Potential Issues**
  - Test suites may:
    - miss edge cases
  - Symbolic constraints may:
    - not fully capture intended behavior
  - Ground truth patches may:
    - not be unique
- **Impact**
  - System may:
    - appear correct when incorrect
    - be penalized despite valid solutions
- **Mitigation**
  - combine:
    - test-based validation
    - symbolic validation
  - analyze:
    - disagreements between signals

#### **6. External Validity (Generalization)**

- **Description**
  - Results may not generalize beyond the evaluated setting.
- **Potential Issues**
  - Limited to:
    - Python programs
    - solver-compatible logic
  - Does not cover:
    - large codebases
    - distributed systems
    - non-deterministic programs
- **Impact**
  - Conclusions may not hold for complex, real-world engineering environments
- **Mitigation**
  - clearly define:
    - scope of applicability
  - evaluate on:
    - multiple task types
  - discuss limitations explicitly

#### **7. Internal Validity (Causality)**

- **Description**
  - Improvements may not be solely due to the proposed method.
- **Potential Issues**
  - Gains may come from:
    - better prompts
    - improved retrieval
    - tuning choices
- **Impact**
  - Hard to attribute performance gains → specific components
- **Mitigation**
  - ablation studies
  - controlled comparisons

#### **8. Solver-Specific Bias**

- **Description**
  - Results depend on the capabilities and limitations of the chosen solver.
- **Potential Issues**
  - Z3 performance varies with:
    - constraint structure
    - encoding strategy
  - Some bugs:
    - not expressible in SMT
- **Impact**
  - Method performance tied to solver capabilities, not general principle
- **Mitigation**
  - report:
    - solver outcomes (SAT / UNSAT / UNKNOWN / TIMEOUT)
  - analyze:
    - constraint coverage
  - consider:
    - alternative solvers (future work)

### **Failure Analysis**

- **Purpose:**
  - Identify where and why the system fails
  - Categorize failures by **component and root cause**
  - Provide insight into:
    - system limitations
    - future improvements
    - validity of assumptions
- **Output of this section should be:**
  - A structured breakdown of failure modes with explanations and diagnostic signals

---

#### **1. Neural Proposal Failures (LLM Stage)**

- **Description**
  - The LLM generates:
    - incorrect patches
    - irrelevant modifications
    - syntactically invalid code
- **Failure Modes**
  - Incorrect logic:
    - wrong condition or operator
  - Overfitting to tests:
    - patch passes tests but is logically incorrect
  - Hallucinated edits:
    - modifies unrelated code
  - Syntax errors:
    - invalid Python after patch
- **Root Cause**
  - LLM reasoning is probabilistic and pattern-based, not constraint-grounded
- **Detection Signals**
  - high iteration count
  - repeated similar patches
  - syntax parsing failures
- ## **Mitigation**

#### **2. Context Retrieval Failures**

- **Description**
  - Relevant code is not retrieved or insufficient context is provided to the LLM
- **Failure Modes**
  - missing function definitions
  - incomplete dependency context
  - irrelevant code chunks
- **Root Cause**
  - embedding similarity does not capture:
    - logical dependencies
    - call graph relationships
- **Detection Signals**
  - patch modifies wrong file/function
  - LLM ignores correct fix location

#### **3. Impact Slicing Failures**

- **Description**
  - The program slice used for symbolic reasoning is:
    - too large (inefficient)
    - too small (missing constraints)
- **Failure Modes**
  - missing variables or conditions
  - incomplete dependency graph
  - excessive slice size → solver timeout
- **Root Cause**
  - imperfect static analysis:
    - CFG/DFG approximations
    - aliasing and dynamic behavior
- **Detection Signals**
  - low constraint coverage
  - solver timeouts
  - missed counterexamples

#### **4. Constraint Extraction Failures**

- **Description**
  - Program behavior is incorrectly or incompletely translated into logical constraints
- **Failure Modes**
  - missing constraints:
    - edge cases not encoded
  - incorrect translation:
    - wrong logical relationships
  - unsupported constructs:
    - complex Python features not representable
- **Root Cause**
  - mismatch between Python semantics ↔ SMT expressibility
- **Detection Signals**
  - solver returns UNSAT but patch is incorrect
  - constraint coverage is low
  - inconsistent solver outputs

#### **5. Symbolic Execution / Solver Failures**

- **Description**
  - The solver fails to produce useful results
- **Failure Modes**
  - TIMEOUT:
    - constraint space too large
  - UNKNOWN:
    - solver cannot determine satisfiability
  - false negatives:
    - misses valid counterexample
- **Root Cause**
  - path explosion
  - complex constraints
  - insufficient solver configuration
- **Detection Signals**
  - high solver latency
  - frequent UNKNOWN outcomes
  - no counterexample despite visible bug

#### **6. Counterexample Quality Failures**

- **Description**
  - Generated counterexamples are:
    - trivial
    - uninformative
    - hard to interpret
- **Failure Modes**
  - edge cases not helpful for fixing logic
  - redundant counterexamples
  - overly complex inputs
- **Root Cause**
  - solver finds _any_ violation, not necessarily minimal or most informative violation
- **Detection Signals**
  - repeated failure across iterations
  - patch does not improve after feedback

#### **7. Feedback Transformation Failures**

- **Description**
  - Symbolic outputs are poorly translated into natural language critiques
- **Failure Modes**
  - vague feedback:
    - “function fails for some input”
  - incorrect interpretation:
    - misrepresents failure
  - loss of key constraint information
- **Root Cause**
  - lossy mapping symbolic constraints → natural language
- **Detection Signals**
  - LLM ignores feedback
  - patch does not change meaningfully

#### **8. Iteration / Convergence Failures**

- **Description**
  - The system fails to converge to a correct patch
- **Failure Modes**
  - oscillation:
    - patches alternate between states
  - stagnation:
    - same patch repeated
  - divergence:
    - patches become increasingly incorrect
- **Root Cause**
  - insufficient feedback signal
  - search space too large
  - poor refinement dynamics
- **Detection Signals**
  - high iteration count
  - repeated counterexamples
  - low patch diversity or chaotic changes

#### **9. Oracle / Evaluation Failures**

- **Description**
  - The system incorrectly evaluates patch correctness
- **Failure Modes**
  - false positives:
    - patch appears correct but is not
  - false negatives:
    - correct patch rejected
  - incomplete test coverage
- **Root Cause**
  - weak or incomplete oracle:
    - missing constraints
    - insufficient tests
- **Detection Signals**
  - mismatch between:
    - test results
    - symbolic verification

### **Evaluation Results (What happened?)**

- **Output of this section should be:**
  - A **clear presentation of results**

---

#### **Quantitative Results**

##### Tables:

- Main performance comparisons

---

-

##### Figures:

- Trends, scaling behavior

---

-

#### **Trajectory / Process Visualization (VERY STRONG)**

- Show how the system behaves over time or steps
- Examples:
  - decision sequences
  - attention evolution
  - memory usage over time

---

-

#### **Qualitative Analysis**

- Example cases
- Success vs failure examples

---

-

#### **Tables**

##### Table 1: Overall Performance

| Method | Accuracy | TPS | Avg Iterations | Time |
| ------ | -------- | --- | -------------- | ---- |

##### Table 2: Logic-Heavy Subset

| Method | Accuracy | Regression Rate | Solver Success |
| ------ | -------- | --------------- | -------------- |

#### **Figures**

- **Bar Chart:** success rate comparison
- **Line Plot:** iteration vs success probability
- **Histogram:** solver outcomes (sat/unsat/timeout)
- **Box Plot:** tokens per task

#### **Trajectory Visualization (VERY STRONG for your project)**

For a single task:
Iteration 0 → bad patch
Iteration 1 → counterexample (lst=[])
Iteration 2 → correct patch

#### **Qualitative Analysis**

Include 2–3 case studies:

- where baseline fails but Symbiotic-SWE succeeds
- show:
  - patch evolution
  - counterexample
  - final fix

## **Analysis (Why did it behave this way?)**

- **Purpose:**
  - Explain _why_ the system behaves as observed in evaluation
  - Provide **causal insights**, not just observations
  - Connect results back to:
    - hypothesis
    - design choices
    - problem formulation
  - Observations → Explanations → Failure Modes → Tradeoffs → Insights
- **Key Question:**
  - _Why did the method perform the way it did, and what does that reveal about the problem and design?_
- **Constraints:**
  - No new experiments (belongs to Evaluation)
  - No system description (belongs to Proposed Technique)
  - Must explain **observed results only**
  - Avoid repeating raw results → focus on **interpretation**

---

### **Key Observations (What patterns do we see?)**

- Summarize the **most important findings** from evaluation
- Focus on:
  - trends
  - unexpected behaviors
  - differences vs baselines
- Examples:
  - performance improves under constraint X
  - degradation occurs in scenario Y
  - system is stable/unstable under Z
- **Output of this section should be:**
  - A **small set of high-level behavioral patterns**

---

-

### **Mechanistic Explanation (Why does this happen?)**

- Explain _why_ the observed behavior occurs
- Tie directly to:
  - design decisions
  - system components
  - hypothesis
- Guiding prompts: - Which part of the system caused this behavior? - What assumption explains this outcome? - How does this connect to your hypothesis?
  **Output of this section should be:**
- A **causal explanation of system behavior**

---

-

### **Error Analysis (Where and how does it fail?)**

- Analyze **failure cases systematically**
- **Output of this section should be:**
  - A **structured understanding of failure modes**

---

#### **Error Taxonomy**

- Categorize types of errors
- Examples:
  - incorrect decisions
  - missing context
  - over-pruning / under-pruning
  - instability across steps

---

-

#### **Failure Case Studies**

- Provide **concrete examples**:
  - input → failure → explanation

---

-

#### **Root Causes of Errors**

- Why do these errors occur?
- Examples:
  - violated assumptions
  - insufficient signal
  - conflicting objectives

---

-

### **Cost Analysis (What is the tradeoff?)**

- Analyze **resource-performance tradeoffs**
- **Output of this section should be:**
  - A **clear tradeoff curve or relationship**

---

#### **Resource Usage**

- Memory
- Compute
- Latency

---

-

#### **Cost vs Performance Tradeoff**

- How does performance change with:
  - memory budget
  - compute budget
  - time

---

-

#### **Efficiency Gains**

- Where does the system become more efficient?
- Under what conditions?

---

-

### **Sensitivity & Robustness (When does it break?)**

- How sensitive is the system to:
  - hyperparameters
  - input variations
  - constraints
- Examples:
  - performance vs memory budget
  - behavior under noisy inputs
  - stability across runs
- **Output of this section should be:**
  - A **robustness profile of the system**

---

-

### **Design Tradeoffs & Implications**

- Reflect on the **design decisions**
- Questions: - What tradeoffs were worth it? - What design choices had the biggest impact? - What would you change?
  **Output of this section should be:**
- A **set of design insights**

---

-

### **Key Takeaways (What did we learn?)**

- Summarize the **most important insights**
- Example structure: - The method works best when… - The main limitation is… - The key insight is…
  **Output of this section should be:**
- A **concise list of actionable insights**

---

-

## **Conclusion (What did we learn and why does it matter?)**

- **Purpose:**
  - Summarize the **core contributions and findings**
  - Reinforce the **importance of the problem and solution**
  - Provide **forward-looking insights and implications**
  - Problem → Idea → Results → Insights → Limitations → Future Work → Impact
- **Key Question:**
  - _What did we accomplish, what did we learn, and what should happen next?_
- **Constraints:**
  - No new technical details
  - No repetition of full explanations from earlier sections
  - Focus on **synthesis, not restatement**
  - Must connect:
    - problem → idea → results → insights

---

### **Problem & Motivation (Reinforcement)**

- Restate the **core problem and its importance**
- Keep this concise (1–2 sentences max)
- Prompts:
  - What problem did we address?
  - Why does it matter?
- **Output of this section should be:**
  - A **clear reminder of the problem and its significance**

---

-

### **Proposed Idea & Approach (High-Level Recap)**

- Summarize your **core idea (thesis)**
- Emphasize what makes it **different or novel**
- Prompts:
  - What is the key idea?
  - What perspective or assumption did we change?
- **Output of this section should be:**
  - A **clean restatement of your core contribution**

---

-

### **Key Results (What did we show?)**

- Highlight the **most important results**
- Focus on:
  - improvements
  - capabilities
  - tradeoffs
- Prompts:
  - What did the evaluation demonstrate?
  - What improvements were achieved?
- **Output of this section should be:**
  - A **concise summary of empirical findings**

---

-

### **Key Insights (What did we learn?)**

- Extract **deeper lessons from the analysis**
- Prompts:
  - Why did the method work?
  - When does it work best?
  - What limitations emerged?
- **Output of this section should be:**
  - A **set of core insights about the problem + method**

---

-

### **Limitations (Honest Reflection)**

- Acknowledge **key limitations of your approach**
- Examples:
  - assumptions that may not hold
  - scenarios where performance degrades
  - constraints not addressed
- **Output of this section should be:**
  - A **clear statement of boundaries and weaknesses**

---

-

### **Future Work (What comes next?)**

- Suggest **next directions** based on your findings
- Types:
  - extending method
  - addressing limitations
  - applying to new domains
  - improving scalability
- **Output of this section should be:**
  - A **set of concrete future directions**

---

-

### **Broader Impact (Why does this matter long-term?)**

- Reflect on **broader implications**
- Examples:
  - impact on systems design
  - implications for ML / inference
  - downstream applications
- **Output of this section should be:**
  - A **high-level significance statement**

---

-

## **Appendix**

- **Purpose:**
  - Provide **supplementary material** that supports, validates, and extends the main paper
  - Include detailed artifacts, extended results, and implementation specifics
  - Main Paper → Appendix = (Details, Depth, Reproducibility, Extensions)
- **Key Question:**
  - _What additional details are needed to fully understand, reproduce, or extend this work?_
- **Constraints:**
  - No new core contributions (must already appear in main paper)
  - No new claims without supporting evidence
  - Content should:
    - deepen understanding
    - enable reproducibility
    - provide transparency

---

### **A. System Diagrams (Deep Visualization Layer)**

- Provide detailed visualizations not included in main paper
- Include:
  - expanded architecture diagrams
  - component-level breakdowns
  - interaction diagrams
- **Output of this section should be:**
  - A **fine-grained visual understanding of the system**

---

-

### **B. Dataflow Walkthrough (End-to-End Example)**

- Provide a **step-by-step walkthrough** of a full system execution
- Include:
  - full input example
  - intermediate transformations
  - final output
- Structure:
  1.  Input
  2.  Processing stages
  3.  Intermediate artifacts
  4.  Final output
- **Output of this section should be:**
  - A **fully traceable execution example**

---

-

### **C. Artifact Schemas (Formal Definitions)**

- Define all major artifacts formally
- For each artifact:
  - Fields
  - Types
  - Description
- Example:
  ```python
  {
    "chunk_id": "string",
    "tokens": ["..."],
    "attention_score": "float"
  }
  ```
- **Output of this section should be:**
  - A **complete artifact specification**

---

-

### **D. Implementation Details (Low-Level System Details)**

- Provide details necessary for replication
- Include:
  - libraries / frameworks
  - configuration settings
  - hyperparameters
  - environment setup
- **Output of this section should be:**
  - A **reproducible implementation reference**

---

-

### **E. Extended Experimental Results**

- Provide additional results not shown in main paper
- Include:
  - full tables
  - additional plots
  - edge-case evaluations
- **Output of this section should be:**
  - A **comprehensive result set**

---

-

### **F. Ablation Study Details**

- Provide full ablation breakdowns
- Include:
  - all configurations tested
  - detailed results per variant
  - interpretation (optional)
- **Output of this section should be:**
  - A **complete ablation matrix**

---

-

### **G. Failure Case Analysis (Expanded)**

- Provide detailed failure examples
- Include:
  - multiple failure cases
  - input → output → explanation
- **Output of this section should be:**
  - A **deep understanding of failure modes**

---

-

### **H. Prompt Templates / System Inputs**

- Provide all templates used in the system
- Include:
  - prompts
  - input formats
  - structured inputs
- **Output of this section should be:**
  - A **fully specified input interface**

---

-

### **I. Reproducibility Details (VERY IMPORTANT)**

- Provide everything needed to reproduce results
- Include:
  - dataset access instructions
  - model checkpoints
  - random seeds
  - experiment scripts
  - environment configuration
- **Output of this section should be:**
  - A **reproducibility checklist**

---

-

### **J. Exploratory Extensions (Beyond Core Scope)**

- Ideas or experiments not fully explored
- Include:
  - alternative approaches
  - partial experiments
  - speculative ideas
- **Output of this section should be:**
  - A **set of future exploration directions**

---

-

### **K. Design Tradeoffs (Expanded)**

- Deeper analysis of design decisions
- Include:
  - alternative design choices
  - why certain approaches were not chosen
  - tradeoff discussions
- **Output of this section should be:**
  - A **design reasoning log**

---

-

### **L. Ethical / Practical Considerations**

- Discuss broader implications
- Include:
  - potential misuse
  - bias considerations
  - deployment challenges
  - real-world constraints
- **Output of this section should be:**
  - A **responsibility and deployment perspective**

---

-

### **A. System Diagrams**

- **End-to-End Pipeline Diagram**
  - Bug Report → Retrieval → Patch Generation → Impact Slicing → Constraint Extraction → Symbolic Execution → Counterexample → Feedback → Refinement Loop
  - Shows full dataflow and interaction between components
- **CEGF Loop Diagram**
  - Focused visualization of:
    - patch → solver → counterexample → critique → refined patch
  - Highlights the closed-loop refinement mechanism
- **Artifact Flow Diagram**
  - Maps each pipeline stage to:
    - input artifacts
    - output artifacts
    - intermediate JSON schemas
  - Useful for understanding reproducibility and debugging
- **Program Slicing + Constraint Extraction Diagram**
  - Visualizes:
    - AST → slice → SMT constraints
  - Shows how code is reduced before symbolic execution

### **B. Dataflow Walkthrough (End-to-End Example)**

- A complete trace of a single task:
  1. Input bug report and failing test
  2. Retrieved code context
  3. Initial patch proposal
  4. Program slice
  5. Extracted constraints
  6. Solver output (SAT)
  7. Generated counterexample
  8. Feedback prompt
  9. Refined patch
  10. Final successful patch
- Includes:
  - actual JSON artifacts at each step
  - patch diffs across iterations
  - solver outputs and counterexamples

### **C. Artifact Schemas**

- Full definitions of:
  - task objects
  - patch objects
  - program slices
  - symbolic problem specs
  - solver results
  - counterexamples
  - critique objects
  - iteration trajectories
- Includes:
  - example JSON instances
  - schema versioning strategy
  - serialization contracts between components

### **D. Implementation Details**

- **Pipeline Modules**
  - retrieval module
  - patch generation module
  - slicing module
  - constraint extraction module
  - symbolic execution module
  - feedback generation module
- **Key Implementation Decisions**
  - AST parsing strategy
  - slicing granularity (function-level vs block-level)
  - constraint encoding format (SMT-LIB vs intermediate JSON)
  - solver timeout thresholds
  - prompt templates for critique injection
- **Supported Python Subset**
  - arithmetic operations
  - boolean expressions
  - conditionals
  - list operations (length, indexing)
  - assertions and type hints

### **E. Extended Experimental Results**

- Additional tables:
  - per-task performance breakdown
  - solver success vs failure distribution
  - runtime per pipeline stage
- Additional plots:
  - iteration count distributions
  - token usage histograms
  - solver latency distribution
- Subgroup analysis:
  - logic-heavy vs non-logic-heavy tasks
  - simple vs complex conditional bugs

### **F. Ablation Study Details**

- Expanded ablation results:
  - Neural-only vs partial vs full system
- Per-component impact analysis:
  - effect of slicing
  - effect of solver
  - effect of counterexample prompting
- Sensitivity analysis:
  - solver timeout
  - max iterations
  - retrieval top-k

### **G. Failure Case Analysis**

- Detailed examples where Symbiotic-SWE fails:
  - unsupported symbolic constructs
  - solver timeouts
  - incorrect constraint extraction
  - retrieval failures
  - semantic misunderstandings
- Comparison with baseline failures:
  - where both systems fail
  - where symbolic reasoning helps but is insufficient

### **H. Prompt Templates**

- Initial patch generation prompt
- Counterexample-guided refinement prompt
- Critique formatting template
- Optional LLM-based critique rewriting prompt

### **I. Reproducibility Details**

- Configuration files:
  - model settings
  - solver settings
  - retrieval parameters
- Random seed handling
- Artifact logging structure
- Instructions to reproduce experiments end-to-end

### **J. Exploratory Extensions**

- **Invariant Inference**
  - using LLMs or dynamic analysis to infer missing assertions
- **Hybrid Verification**
  - combining symbolic execution with concrete execution traces
- **Multi-Function / Multi-File Reasoning**
  - extending slicing beyond single-function scope
- **Adaptive Solver Invocation**
  - only triggering symbolic execution when uncertainty is high
- **Learning from Counterexamples**
  - storing past counterexamples to improve future repair
- **Integration with Static Analysis Tools**
  - combining type checkers or linters with symbolic constraints

### **K. Design Tradeoffs**

- accuracy vs latency
- slice size vs solver tractability
- prompt length vs token cost

### **L. Ethical / Practical Considerations**

- risk of incorrect patches in production
- trust in automated debugging systems

## **Timeline**

- **Purpose:**
  - Define a **structured execution plan** for the project
  - Translate the research idea into **phases, deliverables, and dependencies**
  - Phases → Dependencies → Execution Strategy → Parallelization → Risk Mitigation
- **Key Question:**
  - _What needs to be built, in what order, and how do we ensure progress and correctness?_
- **Constraints:**
  - Each phase must produce a **concrete deliverable**
  - Dependencies must be **explicitly defined**
  - Plan should support:
    - iteration
    - debugging
    - parallel work
  - Avoid vague tasks → prefer **actionable steps**

---

### **Phase-Based Plan (Milestone-Driven Execution)**

- Break the project into **phases**, each with:
  - clear goal
  - concrete deliverable
  - actionable tasks

---

- 👉 Repeat for each phase.

#### **Phase 1: [Name] (Week X)**

##### **Goal**

- What is the objective of this phase?

##### **Deliverables**

- What must be produced?
  - (code, artifacts, diagrams, results)

##### **Tasks**

- What specific steps are required?

##### **Success Criteria (NEW — VERY IMPORTANT)**

- How do you know this phase is complete?
- What must be verified?

### **Gantt-Style Dependency Overview (Execution Order)**

- Define **ordering constraints between phases**
- Example:
  - Week 1: Problem Formulation + Schemas
  - Week 2: Baseline System
  - Week 3: Core Mechanism (e.g., slicing)
  - Week 4: Feature / Signal Extraction
  - Week 5: Decision Module
  - Week 6: Feedback Loop
  - Week 7: Evaluation + Ablations
  - Week 8: Analysis + Writeup
- **Key Dependencies**
  - [Phase A] → required before [Phase B]
  - [Phase B] → required before [Phase C]
- **Output of this section should be:**
  - A **clear execution graph**

---

-

### **Execution Strategy (How will work progress?)**

- Define how you will iterate through phases
- **Output of this section should be:**
  - A **repeatable development loop**

---

#### **Iteration Loop**

- Design → Implement → Test → Analyze → Refine

---

-

#### **Validation Strategy**

- How will each phase be validated before moving on?

---

-

### **Parallelization Plan (What can be done simultaneously?)**

- Identify independent workstreams
- Examples:
  - data processing vs model development
  - baseline vs proposed method
  - evaluation scripts vs system design
- Structure:
  - Task A and Task B can run in parallel because…
  - Task C depends on Task A
- **Output of this section should be:**
  - A **parallel execution strategy**

---

-

### **Risk Assessment & Mitigation (VERY STRONG ADDITION)**

- Identify potential risks
- Types of risks:
  - technical (method doesn’t work)
  - data issues
  - compute limitations
  - time constraints
- For each risk:
  - Risk description
  - Impact
  - Mitigation plan
- **Output of this section should be:**
  - A **risk-aware plan**

---

-

### **Checkpoints & Milestones (Progress Tracking)**

- Define checkpoints to track progress
- Include:
  - weekly milestones
  - demo checkpoints
  - evaluation checkpoints
- **Output of this section should be:**
  - A **progress tracking system**

---

-

### **Stretch Goals (Optional Extensions)**

- Define additional goals if time permits
- Examples:
  - improved model
  - additional experiments
  - optimization
- **Output of this section should be:**
  - A **set of optional enhancements**

---

-

### **Phase 1: System Design & Setup (Week 1)**

#### Goals

- Finalize system architecture
- Define artifact schemas and interfaces
- Set up repo and pipeline scaffolding

#### Tasks

- Define full pipeline:
  - retrieval → patch → slicing → constraints → solver → feedback loop
- Implement:
  - task loader (SWE-bench format → internal schema)
- Define JSON schemas:
  - task, patch, slice, constraints, solver_result, etc.
- Set up logging + artifact directories

#### Deliverables

- `task.json` pipeline working
- artifact schema definitions complete
- basic repo structure

### **Phase 2: Neural Agent + Retrieval (Week 2)**

#### Goals

- Get baseline SWE-agent working

#### Tasks

- Implement:
  - context retrieval (RAG or simple file-based)
  - prompt construction
  - patch generation (LLM call)
- Store:
  - prompts
  - patch outputs
- Implement patch application + syntax validation

#### Deliverables

- End-to-end:
  task → context → patch → apply
- Baseline agent working (no solver yet)

### **Phase 3: Impact Slicing (Week 3)**

#### Goals

- Reduce program to solver-friendly slice

#### Tasks

- Build:
  - AST parser
  - modified function detection
- Construct:
  - basic CFG / dependency extraction
- Output:
  - `program_slice.json`

#### Deliverables

- Patch → affected function(s) extracted
- slice artifacts saved

### **Phase 4: Constraint Extraction (Week 4)**

#### Goals

- Convert code → logical constraints

#### Tasks

- Integrate:
  - CrossHair
- Extract:
  - type hints
  - assertions
  - path conditions
- Generate:
  - SMT constraints (`constraints.smt2` or JSON abstraction)

#### Deliverables

- slice → symbolic constraints pipeline working
- debug logs for unsupported constructs

### **Phase 5: Symbolic Execution + Counterexamples (Week 5)**

#### Goals

- Run solver and generate counterexamples

#### Tasks

- Integrate:
  - Z3 via CrossHair
- Handle:
  - SAT / UNSAT / UNKNOWN / TIMEOUT
- Extract:
  - model → counterexample
- Add:
  - concrete replay validation

#### Deliverables

- `solver_result.json`
- `counterexample.json`
- verified failing inputs

### **Phase 6: Feedback Loop (CEGF) (Week 6)**

#### Goals

- Close the loop with LLM

#### Tasks

- Convert:
  - counterexample → natural language critique
- Inject into prompt:
  - “Verification-as-Prompt”
- Implement:
  - iterative repair loop
- Track:
  - iteration history

#### Deliverables

- full loop working:
  patch → solver → counterexample → critique → refined patch

### **Phase 7: Evaluation + Ablations (Week 7)**

#### Goals

- Run experiments

#### Tasks

- Run:
  - baseline vs Symbiotic-SWE
- Implement:
  - ablations:
    - no solver
    - no slicing
    - no critique
- Collect:
  - metrics:
    - accuracy
    - iterations
    - tokens
    - runtime

#### Deliverables

- experiment logs
- metrics JSON
- aggregated results

### **Phase 8: Analysis + Writeup (Week 8)**

#### Goals

- Finalize results + paper

#### Tasks

- Create:
  - tables
  - plots
- Write:
  - results section
  - discussion
- Add:
  - appendix artifacts
- polish diagrams

#### Deliverables

- final report
- figures + tables
- reproducible pipeline

### **Gantt-Style Dependency Overview**

Week 1: Design + Schemas
Week 2: Neural Agent (Baseline)
Week 3: Slicing
Week 4: Constraint Extraction
Week 5: Solver + Counterexamples
Week 6: Feedback Loop (CEGF)
Week 7: Evaluation + Ablations
Week 8: Analysis + Writeup
Key dependencies:

- Slicing → required before constraints
- Constraints → required before solver
- Solver → required before feedback loop

### **Parallelization Plan**

What can run simultaneously:

- retrieval + baseline agent
- slicing + constraint extraction
- evaluation runs across tasks

### **Stretch Goals**

- multi-file reasoning
- invariant inference
- adaptive solver invocation
- caching counterexamples
