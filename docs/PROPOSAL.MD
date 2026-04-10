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

#### **System Components**

- Define:
  - components
  - dataflow
  - interactions

---

##### **1. Context Retrieval Module**

- **Role:**
  - identify relevant code regions for patch generation
- **Input → Output:**
  - (repo, bug_report) → retrieved_context (code chunks)
- **Interaction:**
  - feeds into LLM prompt construction

##### **2. Neural Patch Generator**

- **Role:**
  - propose candidate fixes using LLM
- **Input → Output:**
  - (prompt) → patch (diff)
- **Interaction:**
  - receives critique from feedback module
  - outputs patch for analysis

##### **3. Impact Slicing Module**

- **Role:**
  - reduce program to relevant subset
- **Input → Output:**
  - (patch, AST) → program_slice
- **Interaction:**
  - feeds into constraint extraction
- **Why important:**
  - reduces solver complexity

##### **4. Constraint Extraction Module**

- **Role:**
  - translate program behavior into logical constraints
- **Input → Output:**
  - (program_slice) → symbolic_constraints
- **Includes:**
  - preconditions
  - postconditions
  - invariants
- **Interaction:**
  - feeds into symbolic execution

##### **5. Symbolic Execution Engine**

- **Role:**
  - explore input space and validate constraints
- **Input → Output:**
  - (symbolic_constraints) → solver_result
- **Outputs:**
  - SAT → counterexample exists
  - UNSAT → patch is logically valid
- **Interaction:**
  - feeds into feedback module

##### **6. Counterexample Generator**

- **Role:**
  - extract concrete failing input from solver
- **Input → Output:**
  - (solver_result) → counterexample

##### **7. Feedback Transformation Module**

- **Role:**
  - convert symbolic failure into LLM-understandable critique
- **Input → Output:**
  - (counterexample, constraints) → critique
- **Example:**
  - "Your patch fails when lst is empty due to division by zero"

##### **8. Iteration Controller (CEGF Loop)**

- **Role:**
  - manage iterative refinement process
- **Input → Output:**
  - (patch, critique) → refined_patch
- **Responsibilities:**
  - track iteration count
  - enforce termination conditions

##### **9. Execution Validator (Optional but Important)**

- **Role:**
  - run tests to confirm behavioral correctness
- **Input → Output:**
  (patch) → test_results
- **Interaction:**
  - complements symbolic verification

#### **High-Level Pipeline**

- Describe the system as a sequence of stages:
- Example:
  1.  Input processing
  2.  Feature extraction
  3.  Decision module
  4.  Output generation

---

1. Define Code Metadata + Repo Structure
   - fill out the readme
   - setup repo + project folders
   - download dependencies
2. **Input Processing**
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

### **Execution Details (HOW it works)**

- Provide a **step-by-step breakdown**
- **Output of this section should be:**
  - A **fully specified execution process**

---

- **Solver Integration:**
  - We use a custom Python harness around [[CrossHair]] and [[Z3]] to convert selected Python functions, their [[PEP 484]] type hints, assertions, and inferred contracts into symbolic constraints. This makes the solver usable as a callable tool inside the debugging loop instead of as a separate offline analysis step. This matches your project goal of adding a symbolic validation step to the agent’s inner loop.
- **Prompt Engineering:**
  - We use a **Verification-as-Prompt** strategy, where solver output is treated as a high-fidelity tool observation rather than raw logs. Counterexamples are normalized into short, structured critiques that explain the failing input, violated condition, and affected function before being reintroduced into the next repair prompt.
- **Dataset Note:**
  - Replace SWE-bench with a less contaminated benchmark or a filtered subset for final evaluation. Keep the pipeline dataset-agnostic so the implementation can swap benchmark loaders without changing downstream stages.
- **Core Pipeline Contract:**
  - Each iteration should transform:
    - `task instance -> retrieved repo context -> candidate patch -> impacted program slice -> symbolic constraints -> solver result -> counterexample critique -> refined patch`
- **State Contract:**
  - Keep one canonical runtime object for the whole loop, for example:
  ```python
  state = {
      "task": {},
      "repo": {},
      "context": [],
      "prompt": "",
      "patch": None,
      "slice": None,
      "constraints": None,
      "solver_result": None,
      "counterexample": None,
      "critique": None,
      "history": [],
      "metrics": {},
  }
  ```

#### **Dataflow Example**

- Bug: division by zero when list is empty
- Repo contains:

```python
def sum_list(lst):
    return sum(lst)/len(lst)
```

- **Bug report:** `"Function fails when list is empty"`
- **Expected behavior:** return `0` when `lst == []`

#### **End-to-end dataflow for this example**

1. Load task and repo snapshot
2. Retrieve `sum_list`
3. Ask LLM for patch
4. Apply patch and locate affected function
5. Translate function behavior into symbolic constraints
6. Ask solver for violating input
7. If violating input exists, convert it into critique
8. Re-prompt LLM with critique
9. Repeat until solver finds no violating input or budget is exhausted

#### **0. Setup + Data Preparation + Processing**

##### **0. Setup + Repo Structure**

###### Low-level Pipeline Steps

1. **Initialize repository layout and execution entrypoints**
   1. Create the top-level folders for:
      - source code
      - configs
      - data
      - artifacts
      - tests
      - docs
   2. Separate code into:
      - pipeline orchestration
      - retrieval
      - patch generation
      - slicing
      - symbolic reasoning
      - evaluation
   3. Define one main entrypoint for:
      - single-task execution
      - benchmark execution
      - ablation execution
   4. Create placeholder modules for each pipeline stage so the repo structure matches the conceptual pipeline early
   5. Decide where temporary working repos will live during task execution
   6. Decide where output artifacts will be written and how iteration folders are organized
2. **Set up environment configuration and dependency management**
   1. Create dependency manifest:
      - Python packages
   2. Add a reproducible environment setup path:
      - venv/ Docker
   3. Define version tracking for:
      - Python version
      - dependency versions
      - prompt versions
      - schema versions
3. **Set up logging, caching, and reproducibility infrastructure**
   1. Define where logs are written:
      - run logs
      - error logs
      - solver logs
      - patch logs
   2. Define cache directories for:
      - retrieval embeddings
      - retrieved context
      - solver outputs
      - prompt outputs
   3. Create run-level metadata file storing:
      - run id
      - config used
      - task ids
      - timestamp
4. **Write README and developer-facing documentation**
   1. Fill out the README with:
      - project overview
      - pipeline stages
      - setup instructions
      - how to run one task
      - how to run all tasks
      - artifact structure

###### Key Components (Psuedocode + Conceptual Steps) + Stepwise ouput artifacts

- [[Symbiotic-SWE-README]]

##### **1. Dataset Preparation + Setup**

- Do **not** parse only the currently retrieved files here. Parse and index the repo once, then retrieve/slice from that cached structure later.

###### Low-level Pipeline Steps

- [Fill out once Key Components is squared away]

1. [Main Step during this stage Name - there can be multiple of these]
   1. [Substeps of Main step - used to understand code implementation better/ really understand what is happening during this Main step]

- (Repeat for each stage)

1. First, the system receives a bug instance from SWE-bench
   1. Load task JSON or benchmark row
   2. Materialize the target repository snapshot locally
   3. Parse relevant Python files into ASTs
   4. Build repository-level metadata such as imports and call graph
   5. Load failing tests, traces, and issue text
   6. Normalize everything into a single task object
   7. Persist initial artifacts before any retrieval or patch generation

###### Key Components (Psuedocode + Conceptual Steps) + Stepwise ouput artifacts

- [[AST Parsing]]
- [[Repository Graph Construction]]
- [[Static Program Analysis]]
- [[Test Harness Execution]]
- benchmark task JSON or dataset row
- local cloned repository snapshot
- failing test files
- optional execution traces/logs
- issue description / bug report text
- `workspace/repo_snapshot/`
- `workspace/task.json`
- `workspace/ast_map.pkl`
- `workspace/call_graph.json`
- `workspace/import_graph.json`
- `workspace/failing_tests.json`
- [[]] or `filename`
  - key function

###### Failure Modes

- [mitigations]

###### Tests

- `filename`
  - tests to conduct

###### Algorithms + Key Data Manipulations

-

###### Data Structures

```python
repo = {
"files": Dict[str, str], # filepath -> source code
"ast_map": Dict[str, AST], # filepath -> parsed AST
"call_graph": Dict[str, List[str]],
"import_graph": Dict[str, List[str]],
}

task = {
"task_id": str,
"bug_report": str,
"repo_path": str,
"failing_tests": List[Dict],
"execution_trace": Optional[List[str]],
}
```

###### Input Example

```python
task = {
"task_id": "toy_sumlist_001",
"bug_report": "Function fails when list is empty",
"repo_path": "/workspace/repo_snapshot",
"failing_tests": [
{"name": "test_sum_list_empty", "input": [], "expected": 0, "actual": "ZeroDivisionError"}
],
"execution_trace": None,
}
```

###### Output Example

```python
state = {
"task": task,
"repo": repo,
"context": [],
"patch": None,
"slice": None,
"constraints": None,
"solver_result": None,
"counterexample": None,
"critique": None,
"history": [],
"metrics": {"iteration": 0},
}
```

#### **1. Pipeline**

##### **1. Context Retrieval (RAG over Codebase)**

- Pure semantic retrieval is often not enough for debugging. Your own framing emphasizes repository-level dependencies and logic-heavy bugs, so retrieval should support both **semantic** and **structural** expansion.

###### Key Components (Psuedocode + Conceptual Steps) + Stepwise ouput artifacts

- [[Code Embeddings]]
- [[Retriever]]
- [[Vector Database]]
- [[Cosine Similarity]]
- [[Call Graph]]
- [[Context Expansion]]
- repo snapshot
- AST map
- call graph
- bug report
- optional failing test names / traces
- `retrieval/chunks.jsonl`
- `retrieval/embeddings.npy`
- `retrieval/ranked_candidates.json`
- `retrieval/topk_context.json`
- [[]] or `filename`
  - key function

###### Tests

- `filename`
  - tests to conduct

###### Data Structures

```python
code_chunk = {
"chunk_id": str,
"filepath": str,
"symbol": str,
"text": str,
"embedding": Optional[List[float]],
}

retrieved_context = {
"query": str,
"topk": List[Dict],
"expanded_neighbors": List[Dict],
}
```

###### Input Example

```python
query = "Function fails when list is empty"

candidate_chunks = [
{"chunk_id": "c1", "filepath": "utils/math.py", "symbol": "sum_list", "text": "def sum_list(lst): return sum(lst)/len(lst)"},
{"chunk_id": "c2", "filepath": "tests/test_math.py", "symbol": "test_sum_list_empty", "text": "def test_sum_list_empty(): assert sum_list([]) == 0"},
]
```

###### Output Example

```python
retrieved_context = {
"query": "Function fails when list is empty",
"topk": [
{"chunk_id": "c1", "filepath": "utils/math.py", "symbol": "sum_list"},
{"chunk_id": "c2", "filepath": "tests/test_math.py", "symbol": "test_sum_list_empty"},
],
"expanded_neighbors": [],
}
```

###### Failure Modes

- [mitigations]

###### Implementation Steps

1. **Relevant code context is retrieved from the repository**
   1. Split repository files into retrievable code units such as functions, classes, and possibly methods
   2. Build metadata for each code chunk:
      1. filepath
      2. symbol name
      3. docstring
      4. imports
      5. callers/callees if available
   3. Embed the bug report and the code chunks
   4. Rank candidate chunks with similarity search
   5. Expand retrieval with structural neighbors when needed:
      1. same file
      2. caller/callee
      3. imported helper
   6. Build the final retrieved context package
   7. Persist ranked candidates and chosen context

##### **2. Neural Proposal (LLM Patch Generation)**

- Separate:
  - raw model output
  - parsed patch
  - applied patch state
- Those are different failure points.

###### Key Components (Psuedocode + Conceptual Steps) + Stepwise ouput artifacts

- [[LLM Inference]]
- [[Prompt Engineering]]
- [[Unified Diff]]
- [[Patch Validation]]
- retrieved context
- bug report
- failing test summary
- repository metadata
- `patches/iteration_0.diff`
- `prompts/iteration_0.txt`
- `llm_outputs/iteration_0.json`
- `patches/iteration_0_apply_log.txt`
- [[]] or `filename`
  - key function

###### Failure Modes

- [mitigations]

###### Tests

- `filename`
  - tests to conduct

###### Data Structures

```python
prompt = {
"system": str,
"user": str,
}

patch = {
"raw_text": str,
"diff": str,
"target_files": List[str],
"parse_ok": bool,
"syntax_ok": bool,
}
```

###### Input Example

```python
prompt = {
"system": "You are a software repair agent. Return a unified diff only.",
"user": """
Bug report: Function fails when list is empty.
Relevant code:
def sum_list(lst):
return sum(lst)/len(lst)

Failing test:
sum_list([]) should return 0
"""
}
```

###### Output Example

```python
patch = {
"raw_text": """--- a/utils/math.py
+++ b/utils/math.py
@@
def sum_list(lst):
- return sum(lst)/len(lst)
+ if len(lst) == 0:
+ return 0
+ return sum(lst)/len(lst)
""",
"diff": "...",
"target_files": ["utils/math.py"],
"parse_ok": True,
"syntax_ok": True,
}
```

###### Implementation Steps

1. \*\*The LLM generates a patch from Context + Bug
   1. Build a prompt using:
      - bug report
      - retrieved code context
      - failing test summary
      - patch format instructions
   2. Ask the LLM for a unified diff or exact replacement
   3. Parse the response into a patch object
   4. Validate patch syntax
   5. Attempt dry-run application to the local repo
   6. Record model output even if patch parsing fails
   7. Store the patch candidate and prompt for traceability

##### **3. Impact Slicing (Static Analysis)**

- Do not slice only by changed lines. Slice by **semantic effect**: changed conditions, returned values, raised exceptions, accessed collections, and divisions/indexing operations.

###### Key Components (Psuedocode + Conceptual Steps) + Stepwise ouput artifacts

- [[Program Slicing]]
- [[Static Program Analysis]]
- [[Control Flow Graph]]
- [[Data Flow Analysis]]
- [[Call Graph]]
- repo AST
- call graph
- patch diff
- patched working tree
- `analysis/modified_nodes.json`
- `analysis/program_slice.json`
- `analysis/cfg.json`
- `analysis/dfg.json`
- `analysis/slice_debug.txt`
- [[]] or `filename`
  - key function

###### Failure Modes

- [mitigations]

###### Tests

- `filename`
  - tests to conduct

###### Data Structures

```python
program_slice = {
"target_functions": List[str],
"modified_nodes": List[Dict],
"affected_variables": List[str],
"path_conditions": List[str],
"related_tests": List[str],
}
```

###### Input Example

```python
patched_function = """
def sum_list(lst):
if len(lst) == 0:
return 0
return sum(lst)/len(lst)
"""
```

###### Output Example

```python
program_slice = {
"target_functions": ["sum_list"],
"modified_nodes": [{"type": "If", "lineno": 2}],
"affected_variables": ["lst"],
"path_conditions": ["len(lst) == 0", "len(lst) > 0"],
"related_tests": ["test_sum_list_empty"],
}
```

###### Implementation Steps

- [Fill out once Key Components is squared away]

1. [Main Step during this stage Name - there can be multiple of these]
   1. [Substeps of Main step - used to understand code implementation better/ really understand what is happening during this Main step]

- (Repeat for each stage)

1. **Then, we identify what parts of the program are affected by the patch**
   1. Apply the candidate patch to a temporary working tree
   2. Reparse modified files
   3. Detect changed AST nodes
   4. Map changed nodes back to enclosing symbols
   5. Traverse local CFG/DFG to identify:
      1. affected variables
      2. branch conditions
      3. dependent statements
   6. Expand to related functions if there are direct callers/callees
   7. Extract the smallest slice sufficient for symbolic reasoning
   8. Persist both the raw impacted region and the reduced slice

##### **4. Constraint Extraction (Program → Logic)**

- You need a clearly defined **supported subset of Python** for v1. For example:
  - arithmetic
  - boolean predicates
  - comparisons
  - list length checks
  - simple loops if CrossHair can handle them
- Without that boundary, implementation can sprawl.

###### Key Components (Psuedocode + Conceptual Steps) + Stepwise ouput artifacts

- [[SMT Encoding]]
- [[CrossHair]]
- [[Z3]]
- [[First Order Logic]]
- [[PEP 484]]
- sliced program
- type hints
- assertions
- patched source code
- `constraints/constraints.smt2`
- `constraints/variables.json`
- `constraints/spec.json`
- `constraints/unsupported_nodes.json`
- [[]] or `filename`
  - key function

###### Failure Modes

- [mitigations]

###### Tests

- `filename`
  - tests to conduct

###### Data Structures

```python
symbolic_problem = {
"function_name": str,
"variables": Dict[str, str],
"path_constraints": List[str],
"postconditions": List[str],
"unsupported_nodes": List[str],
}
```

###### Algorithms + Key Data Manipulations

-

###### Input Example

```python
function_signature = "def sum_list(lst: list[int]) -> float"
path_conditions = ["len(lst) == 0", "len(lst) > 0"]
```

###### Output Example

```python
symbolic_problem = {
"function_name": "sum_list",
"variables": {"lst": "List[Int]"},
"path_constraints": ["len(lst) == 0", "len(lst) > 0"],
"postconditions": [
"len(lst) == 0 -> result == 0",
"len(lst) > 0 -> result == sum(lst)/len(lst)"
],
"unsupported_nodes": [],
}
```

###### Implementation Steps

- [Fill out once Key Components is squared away]

1. [Main Step during this stage Name - there can be multiple of these]
   1. [Substeps of Main step - used to understand code implementation better/ really understand what is happening during this Main step]

- (Repeat for each stage)

1. **Now, the sliced program is converted into logical SMT constraints**
   1. Read the target function signature and type hints
   2. Collect explicit assertions and guards
   3. Infer basic preconditions from code patterns when possible
   4. Normalize path conditions from the slice
   5. Convert supported Python constructs into solver expressions
   6. Build a specification object:
      1. variables
      2. domains
      3. path constraints
      4. desired properties
   7. Serialize the resulting symbolic problem
   8. Record unsupported constructs for debugging/fallback

##### **5. Symbolic Execution (Search over Input Space)**

1. **Then, the solver tries to break the patch**
   1. Load the symbolic problem into CrossHair/Z3
   2. Formulate the negation of the desired property
   3. Search for a satisfying assignment
   4. If SAT, extract the solver model
   5. If UNSAT, mark the current patch as solver-safe under modeled assumptions
   6. If UNKNOWN or timeout, record partial status
   7. Persist the raw solver response and summary status

##### Key Components

- [[Symbolic Execution]]
- [[Constraint Solving]]
- [[Path Exploration]]
- [[Satisfiability]]
- [[CrossHair]]
- [[Z3]]

##### Input Artifacts

- SMT constraints
- symbolic problem spec
- solver config

##### Data Structures

```python
solver_result = {
"status": "sat" | "unsat" | "unknown" | "timeout",
"model": Optional[Dict[str, Any]],
"violated_property": Optional[str],
"solver_time_ms": int,
}
```

##### Input Example

```python
symbolic_problem = {
"function_name": "sum_list",
"variables": {"lst": "List[Int]"},
"postconditions": ["len(lst) == 0 -> result == 0"]
}
```

##### Output Example

```python
solver_result = {
"status": "sat",
"model": {"lst": []},
"violated_property": "function raises division by zero for empty list",
"solver_time_ms": 47,
}
```

##### Output Artifacts

- `solver/model.json`
- `solver/solver_result.json`
- `solver/log.txt`

##### Important implementation note

- Treat `unknown` and `timeout` as first-class outcomes, not failures of your code. They are normal solver states.

##### **6. Counterexample Generation (CEGF Core)**

1. **If the solver finds a violation, it produces a counterexample**
   1. Interpret the solver model into Python-level input values
   2. Replay the patched function or patched repo behavior with those inputs
   3. Confirm the failure is reproducible concretely
   4. Capture:
      1. failing input
      2. failing branch/path
      3. observed exception or violated assertion
   5. Format a normalized counterexample object
   6. Store both structured and human-readable versions

##### Key Components

- [[Counterexample Guided Feedback]]
- [[Concrete Replay]]
- [[Constraint Violation Detection]]

##### Input Artifacts

- solver model
- solver result
- patched working tree
- constraints/spec

##### Data Structures

```python
counterexample = {
"inputs": Dict[str, Any],
"violated_property": str,
"observed_failure": str,
"affected_function": str,
}
```

##### Input Example

```python
solver_result = {
"status": "sat",
"model": {"lst": []},
"violated_property": "len(lst)==0 should imply result==0"
}
```

##### Output Example

```python
counterexample = {
"inputs": {"lst": []},
"violated_property": "empty list should return 0",
"observed_failure": "ZeroDivisionError",
"affected_function": "sum_list",
}
```

##### Output Artifacts

- `counterexamples/iteration_0.json`
- `counterexamples/iteration_0_replay.txt`

##### Important implementation note

- Always replay the counterexample concretely when possible. Solver-generated examples are useful, but concrete replay gives you a cleaner critique and catches encoding mistakes.

##### **7. Feedback Transformation (Symbolic → Natural Language)**

1. **Now, convert formal failure into LLM-readable critique**
   1. Read the structured counterexample
   2. Extract:
      1. failing input
      2. violated condition
      3. affected symbol
      4. likely cause
   3. Fill a fixed explanation template
   4. Optionally ask an LLM to lightly rewrite for clarity
   5. Keep the critique short, factual, and grounded
   6. Save both machine-readable and final prompt-ready versions

##### Key Components

- [[Verification-as-Prompt]]
- [[Prompt Engineering]]
- [[Program Explanation]]
- [[LLM Tool Feedback]]

##### Input Artifacts

- counterexample
- patch
- symbolic problem spec

##### Data Structures

```python
critique = {
"short_text": str,
"structured": Dict[str, Any],
}
```

##### Input Example

```python
counterexample = {
"inputs": {"lst": []},
"observed_failure": "ZeroDivisionError",
"affected_function": "sum_list"
}
```

##### Output Example

```python
critique = {
"short_text": "Your patch still fails in sum_list when lst = []. The function divides by len(lst), which is 0, causing ZeroDivisionError.",
"structured": {
"function": "sum_list",
"inputs": {"lst": []},
"error": "ZeroDivisionError"
}
}
```

##### Output Artifacts

- `feedback/iteration_0.txt`
- `feedback/iteration_0.json`

##### Important implementation note

- Keep the critique bounded. Do not dump raw solver output into the prompt.

##### **8. CEGF Loop (Closed Feedback System)**

1. **Now, feed this back into the LLM**
   1. Build a refinement prompt containing:
      1. original bug report
      2. relevant code context
      3. previous patch
      4. critique
   2. Ask the LLM for a revised patch
   3. Parse and validate the revised patch
   4. Append this iteration to trajectory history
   5. Increment metrics
   6. Route back into slicing and solver validation

##### Key Components

- [[Iterative Refinement]]
- [[Feedback Loop]]
- [[Agent Memory]]
- [[Repair Trajectory]]

##### Input Artifacts

- previous patch
- critique
- previous prompt
- retrieved context

##### Data Structures

```python
iteration_record = {
    "iteration": int,
    "prompt_path": str,
    "patch_path": str,
    "critique_path": str,
    "solver_status": str,
}
```

##### Input Example

```python
refinement_prompt = {
    "bug_report": "Function fails when list is empty",
    "previous_patch": "...",
    "critique": "Your patch still fails when lst = [] ..."
}
```

##### Output Example

```python
refined_patch = """--- a/utils/math.py
+++ b/utils/math.py
@@
def sum_list(lst):
- return sum(lst)/len(lst)
+ if len(lst) == 0:
+ return 0
+ return sum(lst)/len(lst)
"""
```

##### Output Artifacts

- `patches/iteration_k.diff`
- `prompts/iteration_k.txt`
- `history/trajectory.json`

##### Important implementation note

- You should keep the whole repair trajectory. This helps with debugging, ablations, and later analysis of whether counterexamples reduce search entropy, which is one of your stated contributions.

##### **9. Convergence / Termination**

1. Loop continues until ✅ No counterexamples found OR ⛔ iteration budget exceeded
   1. If solver result is `unsat`, mark success under current model assumptions
   2. If iterations exceed max budget, stop
   3. If solver repeatedly returns `unknown` or timeout, optionally fall back to test-only validation
   4. Aggregate metrics after every iteration
   5. Write a final run summary

##### Key Components

- [[Stopping Criteria]]
- [[Evaluation Metrics]]
- [[Tokens-per-Success]]

##### Input Artifacts

- solver results
- iteration history
- token usage log

##### Data Structures

```python
metrics = {
"num_iterations": int,
"tokens_used": int,
"success": bool,
"termination_reason": str,
}
```

##### Input Example

```python
history = [
{"iteration": 0, "solver_status": "sat"},
{"iteration": 1, "solver_status": "unsat"},
]
```

##### Output Example

```python
metrics = {
"num_iterations": 2,
"tokens_used": 1200,
"success": True,
"termination_reason": "solver_unsat"
}
```

##### Output Artifacts

- `metrics/run_summary.json`
- `logs/full_trace.json``

## **Artifact Information**

- **Purpose:**
  - Define all **artifacts** used, produced, and evaluated in the system
  - Ensure **reproducibility, traceability, and clarity of data flow**
  - Inputs → Transformations → Intermediate Artifacts → Outputs → Evaluation Artifacts
- **Key Question:**
  - _What concrete objects (data, models, files, outputs) flow through the system, and how are they structured, versioned, and used?_
- **Constraints:**
  - No algorithmic explanations (belongs to Proposed Technique)
  - No performance claims (belongs to Evaluation)
  - Must clearly distinguish:
    - **Inputs**
    - **Intermediate artifacts**
    - **Outputs**
  - Every artifact should be:
    - identifiable
    - reproducible
    - versionable

---

### **Input Artifacts (What the system consumes)**

- Define all external inputs to the system
- **Output of this section should be:**
  - A **fully specified input environment**

---

#### <b>Data</b>

- What datasets are used?
- What is their structure and format?
- What preprocessing is applied?
- Inlcude:
  - Dataset name + source
  - Size / scale
  - Format (JSON, CSV, text, etc.)
  - Access method (local, API, repo)

---

##### Datasets #TODO

- SWE-bench
- Source: [https://github.com/SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench)
- Provides:
  - real-world GitHub issues
  - repository snapshots
  - failing test cases

##### Structure & Format

- Raw format:
  - JSON + repository directories
- Each task includes:

```python
task = {
    "task_id": str,
    "repo_path": str,
    "bug_report": str,
    "failing_tests": list,
    "execution_trace": list | None,
}
```

- Associated inputs:
  - repository snapshot (local file tree)
  - test files
  - optional logs / traces

##### Scale

- Full dataset:
  - hundreds of real-world tasks
- Experimental subset:
  - logic-heavy filtered subset (≈20–100 tasks)
  - optionally manually annotated

#### Models

- What models are used (if any)?
- Include:
  - Model name / architecture
  - Version / checkpoint
  - Role in system (e.g., embedding, generation, scoring)

---

1. Repair / Generation Model
   - **Model:** GPT-4o
   - **Role:**
     - generate initial patches
     - refine patches using counterexample-guided feedback
     - optionally rewrite critiques into prompt-friendly format
2. Optional Judge Model
   - **Model:** GPT-4o (or similar LLM)
   - **Role:**
     - evaluate feedback quality
     - compare baseline vs Symbiotic-SWE outputs
3. Symbolic Reasoning Model
   - **Framework:** CrossHair
   - **Backend Solver:** Z3
   - **Role:**
     - convert program behavior → logical constraints
     - explore input space symbolically
     - generate counterexamples
4. Optional Retrieval / Embedding Model
   - **Model:** Code embedding model (configurable)
   - **Role:**
     - encode code chunks
     - enable similarity-based retrieval for context

#### Tools / Infrastructure

- What external tools are required?
- Examples:
  - vector databases
  - solvers
  - APIs
  - frameworks
- **Output of this section should be:**
  - A **fully specified input environment**

---

##### 1. Core Tools

- [[GPT-4o]]
  - LLM API for patch generation and refinement
- [[CrossHair]]
  - symbolic execution framework for Python
- [[Z3]]
  - SMT solver for constraint satisfaction and counterexample generation

##### 2. Program Analysis Utilities

- [[AST Parsing]]
  - extract program structure
- [[Control Flow Graph]]
- [[Data Flow Analysis]]
  - used for impact slicing and dependency tracking
- **Additional Utilities**
  - diff parsing (unified diff → AST updates)
  - function boundary detection
  - dependency traversal (call graph expansion)

##### 3. Environment Configuration

- Python version
- dependency list (requirements.txt)
- API keys / environment variables

---

- Runtime Requirements
  - Python runtime (>=3.9)
  - access to LLM API
  - local filesystem for repo snapshots
  - sufficient memory for symbolic execution
- Optional Enhancements
  - virtual environment (venv / conda)
  - Docker container for reproducibility

##### 4. Testing Environment

- Python test runner (pytest / unittest)
- sandboxed execution environment:
  - isolated working directory per task
  - prevents state leakage between runs
- test replay system:
  - rerun failing tests after patch application
  - validate counterexample concretely
- Key Capabilities
  - patch application + rollback
  - deterministic test execution
  - timeout handling for long-running tests
- Artifacts
  - test logs
  - pass/fail traces
  - runtime errors

##### 5. Data Validation

- verify repo integrity
- ensure tests reproduce failure
- validate task schema

---

- confirm patch applies cleanly to repo
- ensure AST parses after patch
- validate symbolic extraction coverage
- detect unsupported constructs early

##### 6. Logging & Reproducibility

- artifact storage:
  - JSON logs for:
    - patches
    - slices
    - constraints
    - solver outputs
  - configuration files:
    - model settings
    - solver parameters
    - evaluation configs

##### 7. Database Infrastructure

- vector store (e.g., FAISS / Chroma)
- embedding pipeline for code retrieval

##### 8. Caching

- cache embeddings
- cache solver results
- cache retrieved context
- prompt caching (avoid repeated LLM calls)
- patch evaluation caching (same patch → skip recompute)
- slice caching (unchanged code regions)

##### 9. Orchestration / Pipeline Management

- pipeline controller:
  - manages stage execution:
    - retrieval → patch → slice → constraints → solver → feedback
- state management:
  - centralized `state` object passed between stages
- iteration controller:
  - handles CEGF loop
  - enforces max iteration budget

### **System Artifacts (Intermediate / Runtime Objects)**

- Define artifacts produced during execution
- **Output of this section should be:**
  - A **clear map of runtime state + intermediate objects**

---

#### **Intermediate Iteration Artifacts**

- What artifacts are produced at each step/iteration?
- Examples:
  - chunked inputs
  - feature vectors
  - attention statistics
  - constraint sets
  - intermediate predictions

---

-

#### **Runtime State**

- What state is maintained across steps?
- Examples:
  - KV cache
  - memory buffers
  - execution traces
  - feedback signals

---

-

### **Output Artifacts (What the system produces)**

- Define final outputs used for evaluation or downstream tasks
- **Output of this section should be:**
  - A **well-defined output space**

---

#### **Primary Outputs**

- What is the main output?
- Examples:
  - predictions
  - generated sequences
  - decisions

---

-

#### **Auxiliary Outputs**

- Additional outputs for analysis:
- Examples:
  - logs
  - traces
  - confidence scores
  - explanations

---

-

#### **File-Level Outputs**

##### Files Modified:

-

##### Files Added:

-

### **Artifact Schema / Serialization Contract**

- Define how artifacts are structured and stored
- **Output of this section should be:**
  - A **reproducible artifact specification**

---

#### **Object Definitions**

##### **1. [Artifact Name]**

- Fields:
- Type:
- Description:

#### **Serialization Format**

- JSON / binary / database schema
- Key naming conventions
- Versioning format

---

-

#### **Versioning Strategy**

- How are artifacts versioned?
- Examples:
  - dataset version
  - model checkpoint version
  - experiment ID

---

-

### **Diagrams (System Visualization Layer)**

- Visual representations of the system
- **Output of this section should be:**
  - A **visual understanding of system + artifacts**

---

#### **System Overview Diagram**

- Bug Report → Context Retrieval → Neural Proposal → Impact Slicing → Constraint Extraction → Symbolic Execution → Counterexample Generation → Feedback Transformation → CEGF Loop

#### **Dataflow Diagram**

- task instance → repo context → patch diff → program slice → SMT constraints → solver result → critique → refined patch

#### **Repair Loop Diagram**

- shows the closed-loop interaction between the LLM and symbolic solver

#### **Artifact Flow Diagram**

- maps which files are consumed and produced at each stage

#### **Failure Mode Diagram**

- shows branching outcomes such as:
  - patch parse failure
  - unsupported symbolic construct
  - solver SAT / UNSAT / UNKNOWN / TIMEOUT

#### **Ablation Diagram**

- full Symbiotic-SWE vs. stripped variants:
  - neural only
  - neural + slicing
  - neural + solver without critique
  - neural + critique without slicing
  - full system

### **Benchmarks & Evaluation Artifacts**

- Define the evaluation environment
- **Output of this section should be:**
  - A **clear evaluation interface**

---

#### **Benchmarks**

- Primary benchmark
- Subsets (e.g., logic-heavy)

---

-

#### **Evaluation Outputs**

- What outputs are compared?
- Examples:
  - predicted vs ground truth
  - performance metrics
  - system traces

---

-

### **Ablation Grid (Experimental Design Space)**

- Define variations of the system
- **Output of this section should be:**
  - A **structured experimental grid**

---

#### **Baseline Systems**

- Vanilla SWE-agent
- Chain-of-Thought-only repair agent

#### **System Variants**

- Neural-only agent
- Neural + Impact Slicing
- Neural + Symbolic Verification (no critique injection)
- Neural + Counterexample Guided Feedback (no slicing)
- Full Symbiotic-SWE

#### **Constraint Source Variants**

- Assertions only
- Type hints only
- Assertions + type hints
- Assertions + type hints + inferred contracts
- Assertions + type hints + inferred contracts + optional LLM-generated invariants

#### **Retrieval Variants**

- Semantic retrieval only
- Semantic retrieval + structural expansion

#### **Termination / Budget Variants**

- max iterations = 1, 2, 3, 5
- solver timeout thresholds

#### **Critique Variants**

- raw solver output
- structured critique template
- structured critique + light LLM rewrite

### Benchmarks #TODO

#### **Primary benchmark**

- SWE-bench or a cleaned / filtered substitute benchmark

#### **Logic-heavy subset**

- arithmetic predicate bugs
- relational operator bugs
- assertion-violation bugs
- multi-conditional reasoning bugs
- bugs whose fixes primarily modify conditionals rather than large structural rewrites
- That logic-heavy subset is already central to your proposal and should be explicitly repeated here because it determines which artifact traces you need to save for later analysis.

#### **Benchmark outputs to compare**

- task resolution rate
- number of repair iterations
- token consumption
- wall-clock runtime
- solver overhead
- critique quality
- regression behavior / repeated failure rate

### Runtime / Intermediate Artifacts

#### <b>Intermediate Iteration Artifacts</b>

- `workspace/task.json`
- `workspace/repo_snapshot/`
- `workspace/ast_map.pkl`
- `workspace/call_graph.json`
- `retrieval/chunks.jsonl`
- `retrieval/ranked_candidates.json`
- `retrieval/topk_context.json`
- `prompts/iteration_k.txt`
- `patches/iteration_k.diff`
- `patches/iteration_k_apply_log.txt`
- `analysis/modified_nodes.json`
- `analysis/program_slice.json`
- `analysis/cfg.json`
- `analysis/dfg.json`
- `constraints/spec.json`
- `constraints/constraints.smt2`
- `constraints/unsupported_nodes.json`
- `solver/solver_result.json`
- `solver/model.json`
- `counterexamples/iteration_k.json`
- `counterexamples/iteration_k_replay.txt`
- `feedback/iteration_k.txt`
- `feedback/iteration_k.json`
- `history/trajectory.json`
- `logs/full_trace.json`

### Output Artifacts

#### Files Modified

- repository files patched during candidate repair iterations
- benchmark task working tree used for patch application and replay
- configuration files for solver and evaluation settings
- trajectory / metrics files updated after each iteration

#### Files Added

- `workspace/task.json`
- `workspace/ast_map.pkl`
- `workspace/call_graph.json`
- `retrieval/chunks.jsonl`
- `retrieval/embeddings.npy`
- `retrieval/ranked_candidates.json`
- `retrieval/topk_context.json`
- `prompts/iteration_k.txt`
- `llm_outputs/iteration_k.json`
- `patches/iteration_k.diff`
- `analysis/modified_nodes.json`
- `analysis/program_slice.json`
- `analysis/cfg.json`
- `analysis/dfg.json`
- `constraints/spec.json`
- `constraints/constraints.smt2`
- `constraints/variables.json`
- `constraints/unsupported_nodes.json`
- `solver/solver_result.json`
- `solver/model.json`
- `solver/log.txt`
- `counterexamples/iteration_k.json`
- `counterexamples/iteration_k_replay.txt`
- `feedback/iteration_k.txt`
- `feedback/iteration_k.json`
- `history/trajectory.json`
- `metrics/run_summary.json`
- `logs/full_trace.json`

### Artifact Schema / Serialization Contract

#### **1. Task Object**

- Represents a single benchmark instance (input to the system)

```python
{
  "schema_version": "1.0",
  "task_id": "string",
  "repo_path": "string",
  "repo_commit": "string",
  "bug_report": "string",
  "failing_tests": [
    {
      "name": "string",
      "input": "any",
      "expected": "any",
      "actual": "any",
      "error": "string"
    }
  ],
  "execution_trace": ["string"],
  "metadata": {
    "dataset": "string",
    "difficulty": "string",
    "tags": ["string"]
  }
}
```

#### **2. Patch Object**

- Represents an LLM-generated or refined code patch

```python
{
  "schema_version": "1.0",
  "patch_id": "string",
  "iteration": 0,
  "raw_text": "string",
  "diff": "string",
  "target_files": ["string"],
  "parse_ok": true,
  "syntax_ok": true,
  "apply_ok": true,
  "errors": ["string"],
  "metadata": {
    "model": "string",
    "prompt_path": "string"
  }
}
```

#### **3. Program Slice**

- Represents the reduced portion of the program used for symbolic reasoning

```python
{
  "schema_version": "1.0",
  "slice_id": "string",
  "iteration": 0,
  "target_functions": ["string"],
  "modified_nodes": [
    {
      "type": "string",
      "lineno": 0,
      "code": "string"
    }
  ],
  "affected_variables": ["string"],
  "path_conditions": ["string"],
  "related_tests": ["string"],
  "source_files": ["string"],
  "unsupported_nodes": ["string"]
}
```

#### **4. Symbolic Problem Spec**

- Represents the SMT-encodable abstraction of the program slice

```python
{
  "schema_version": "1.0",
  "problem_id": "string",
  "iteration": 0,
  "function_name": "string",
  "variables": {
    "var_name": "type"
  },
  "path_constraints": ["string"],
  "preconditions": ["string"],
  "postconditions": ["string"],
  "invariants": ["string"],
  "encoding_status": "success | partial | failed",
  "unsupported_constructs": ["string"]
}
```

#### **5. Solver Result**

- Represents the output of symbolic execution / SMT solving

```python
{
  "schema_version": "1.0",
  "solver_id": "string",
  "iteration": 0,
  "status": "sat | unsat | unknown | timeout",
  "model": {
    "var_name": "value"
  },
  "violated_property": "string",
  "solver_time_ms": 0,
  "constraints_checked": 0,
  "error": "string"
}
```

#### **6. Counterexample Object**

- Concrete failure instance derived from solver output

```python
{
  "schema_version": "1.0",
  "counterexample_id": "string",
  "iteration": 0,
  "inputs": {
    "var_name": "value"
  },
  "violated_property": "string",
  "observed_failure": "string",
  "affected_function": "string",
  "replay_success": true,
  "trace": ["string"]
}
```

#### **7. Critique Object**

- Natural language feedback used for refinement

```python
{
  "schema_version": "1.0",
  "critique_id": "string",
  "iteration": 0,
  "short_text": "string",
  "structured": {
    "function": "string",
    "inputs": {
      "var_name": "value"
    },
    "error": "string",
    "violated_property": "string"
  },
  "source": "template | llm",
  "prompt_ready": true
}
```

#### **8. Iteration History / Trajectory**

- Tracks the full repair loop

```python
{
  "schema_version": "1.0",
  "task_id": "string",
  "iterations": [
    {
      "iteration": 0,
      "prompt_path": "string",
      "patch_id": "string",
      "slice_id": "string",
      "problem_id": "string",
      "solver_id": "string",
      "counterexample_id": "string",
      "critique_id": "string",
      "solver_status": "sat | unsat | unknown | timeout",
      "tokens_used": 0,
      "time_ms": 0
    }
  ],
  "final_status": "success | failure | timeout",
  "termination_reason": "string",
  "total_tokens": 0,
  "total_time_ms": 0
}
```

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

#### **Dataset**

- What data is used?
- Size, distribution, splits

---

##### **Primary Dataset**

- SWE-bench (or filtered/cleaned subset)
- Each task includes:
  - repository snapshot
  - bug report
  - failing tests

##### **Logic-Heavy Subset (Core Evaluation Focus)**

- Arithmetic predicate bugs
- Conditional logic errors
- Assertion violations
- Edge-case handling bugs (empty inputs, boundary values)
- Multi-step reasoning bugs (nested conditionals)

##### **Dataset Filtering Strategy**

- Filter tasks where:
  - fixes primarily modify conditionals or expressions
  - failure traces involve incorrect logical reasoning
- Optional: manually annotate ~20–50 tasks to validate subset quality

#### **Baselines**

- What methods are you comparing against?
- Why are they relevant?

---

##### **Primary Baseline**

- Vanilla SWE-agent (same model, same prompt budget)

##### **Additional Baselines**

- **Chain-of-Thought Agent**
  - reasoning-only, no verification
- **Execution-Only Agent**
  - test feedback, no symbolic reasoning
- **Ablation Variants**
  - Neural + slicing (no solver)
  - Neural + solver (no counterexample feedback)
  - Neural + CEGF (no slicing)

##### **Fairness Constraints**

- Same:
  - LLM model (GPT-4o)
  - max tokens
  - max iterations
  - retrieval setup
- Only difference:
  - presence/absence of symbolic validation + CEGF

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

#### **Ablation Studies**

- What components are removed or modified?
- Why?

---

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
