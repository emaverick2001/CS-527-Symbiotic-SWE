## **3. Experimental Setup + Evaluation (How do we test and evaluate it?)**

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

### **1. Research Questions (What are we testing?)**

- Define the **key questions your evaluation answers**
- Each should map to:
  - hypothesis
  - contribution
- **Output of this section should be:**
  - A **small set of testable evaluation questions**

---

- The evaluation is designed to answer one central question: does adding symbolic counterexample critique to an otherwise identical repair agent improve logical patch quality on logic-heavy bugs? To make that question concrete, the study is organized around four research questions:
  - RQ1: Does Symbiotic-SWE improve task resolution and logical correctness over a neural-only repair loop on logic-heavy repository bugs?
  - RQ2: Does symbolic critique reduce regressions, repeated failures, and wasted search iterations?
  - RQ3: What runtime and token overhead does symbolic verification introduce, and when is that overhead offset by better convergence?
  - RQ4: On which bug types does the solver provide actionable value, and where does it fail because the slice or symbolic encoding is too weak?

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

#### **Hypothesis (Driving Claim)**

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

### ==**2. Experiment Evaluation**==

#### **1. Objective Function (What does “good” mean?)**

- What are we optimizing for?
- Is the objective **explicit (mathematical)** or **implicit (proxy-based)**?

---

- We optimize for producing a **correct patch** for a bug-fixing task while minimizing unnecessary search, token usage, and runtime overhead.
- The objective is **hybrid**:
  - **Explicit / mathematical:** correctness and cost terms
  - **Implicit / proxy-based:** search quality, critique usefulness, and stability of refinement

```
maximize:
correctness(P')
- λ₁ · cost_tokens
- λ₂ · cost_time
- λ₃ · num_iterations
- λ₄ · regression_risk
```

- `P'` is the patched program
- `correctness(P')` measures whether the patch resolves the target bug and satisfies relevant correctness checks
- `cost_tokens` is total LLM token usage across the repair loop
- `cost_time` is total wall-clock runtime
- `num_iterations` is the number of repair/refinement steps
- `regression_risk` captures the risk that the patch passes target tests but introduces new logical errors or breaks previously correct behavior

#### **2. Primary Objective**

- Define the main goal

---

- The main goal is to produce a **valid repaired program** that fixes the bug and does not violate the intended logic of the task.
- Formally:

```
correctness(P') = 1 if Valid(P') else 0
```

where:

```
Valid(P') ⇔
    fixes_target_bug(P')
    ∧ passes_required_tests(P')
    ∧ no_symbolic_counterexample_found(P')
```

- ==In practice, this means a good solution is not just one that passes the failing tests, but one that also survives symbolic verification on the repaired local region. This is consistent with your proposal’s core claim that test-passing alone is insufficient for logic-heavy bugs and that symbolic counterexamples provide stronger feedback about correctness.==

#### **3. Efficiency Objectives**

---

- A good system should not only find a correct patch, but do so **efficiently**.
- **Token Efficiency**
  - minimize:

```
cost_tokens = total LLM tokens consumed across all iterations
```

- **Time Efficiency**
  - minimize:

```
cost_time = total wall-clock runtime
```

- **Search Efficiency**
  - minimize:

```
num_iterations = number of proposal/refinement rounds until termination
```

- **Solver Efficiency**
  - minimize symbolic overhead relative to total runtime:

```
solver_overhead = solver_time / total_runtime
```

- These efficiency terms reflect your proposal’s goal of reducing trial-and-error debugging and improving repair precision with fewer wasted attempts.

#### **4. Correctness Objectives**

---

- Since your project focuses on **logic-heavy bugs**, correctness should be defined more strongly than simple benchmark success.
- **Bug Resolution**
  - the patch should resolve the target failing behavior
- **Behavioral Correctness**
  - the patch should satisfy the required failing tests and preserve previously passing behavior where possible
- **Logical Correctness**
  - the patched local program region should admit **no solver-discovered violating input** under the extracted symbolic constraints
- **Regression Avoidance**
  - the patch should not fix the target bug by introducing a silent logical regression elsewhere
- In other words, the system is optimizing for:

```
correct repair > test-only repair
```

#### **5. Implicit Objectives**

---

- **Reduce search entropy**
  - the system should avoid exploring many redundant or low-quality patches

```
minimize |{distinct failed patches explored}|
```

- **Improve critique usefulness**
  - symbolic feedback should be specific enough to help the next iteration move toward a better patch
- **Promote refinement stability**
  - successive iterations should become more targeted rather than oscillating between unrelated fixes
- **Preserve minimal-context efficiency**
  - the system should solve tasks using the smallest local code region necessary, only expanding context if local context is insufficient

#### **6. Tradeoffs**

- What competing objectives exist?
- Examples:
  - Quality vs memory
  - Latency vs accuracy
  - Throughput vs personalization

---

- A good objective must acknowledge the competing goals in the system.
- **Correctness vs Runtime**
  - stronger symbolic verification can improve logical correctness, but increases latency
- **Correctness vs Token Cost**
  - more refinement iterations may improve patch quality, but increase token usage
- **Minimal Context vs Completeness**
  - small local context improves efficiency, but may omit supporting code needed for a correct patch
- **Refinement Depth vs Budget**
  - more iterations can recover from bad early proposals, but the loop must stop within a practical budget
- **Symbolic Precision vs Generality**
  - tighter symbolic reasoning improves guarantees, but only for bugs whose behavior can be encoded and checked tractably
- ==So in practice, the system is solving: find the most correct patch possible subject to limited tokens, limited iterations, and manageable symbolic overhead==

#### **7. Constraints**

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

-

#### **8. Assumptions**

- What assumptions are required to make the problem tractable?
- Examples:
  - Retrieval scores are available and meaningful
  - Attention reflects relevance
  - Data distribution is stationary
  - Errors are independent across steps
- **Output of this section should be:**
  - A **list of modeling assumptions**

---

-

#### **9. Metrics**

1. for each metric listed list what it measures, the formula, our hypothetical expected Direction of Change, why it matters.
2. rank the metrics based on highest impact and usability for this project

---

- The metric design distinguishes **benchmark success** from **logical success**. SWE-bench defines a task as resolved when the patch applies cleanly and the associated tests pass.
- That remains the benchmark-facing success criterion, but this paper adds a stricter measure: Real Test Success Rate which is quantified as follows: $\frac{\#\text{test resolved tasks}}{\#\text{logic-heavy tasks}}$. We also measure the Logical Correctness Rate which tells us whether the patch is **truly correct**, not just test-passing and is quantified by $\frac{\#\text{tasks where real tests pass AND solver status is unsat }}{\text{total tasks}}$. These two are our main effectiveness metrics to measure symbiotic swe's performance.
- The efficiency metrics are designed to capture whether symbolic reasoning reduces search waste enough to justify its overhead.
- The first is **Average Repair Iterations**, the mean number of proposal–refinement rounds until termination.
- The second is **Tokens per Success**, $\text{TPS} = \frac{\text{Total LLM Tokens Used}}{\#\text{Successful Tasks}}$ which measures how expensive successful repair is in model usage terms.
- The third is **Solver Overhead**, $\text{SolverOverhead} = \frac{\text{Symbolic Verification Time}}{\text{Total Runtime}}$ which separates the extra formal-analysis cost from the rest of the loop.
- The fourth is **total wall-clock runtime** and measures the total execution time per task. It is quantified as follows: $time_{end} - time_{start}$ .
- These are paired with behavioral diagnostics: counterexample detection rate, critique utility, repeated failure rate, and a failure-mode breakdown, so that the paper can explain not only whether the method helps, but how it changes the agent’s search behavior.

##### **1. Effectiveness (Primary Metrics)**

- These are your **most important metrics**.

---

1. ==**Logic-heavy Task Success Rate**==
   - What it measures
     - % of tasks successfully solved on logic-heavy subset
     - Your main benchmark comparison metric
   - Formula
     - SuccessRate_logic = (# tasks where failing tests pass AND patch accepted) / (# logic-heavy tasks)
   - Expected Direction of Change
     - ↑ higher than neural-only baseline
   - Why it matters
     - This is your headline number in the paper
2. ==**Logical Correctness Rate**==
   - **What it measures**
     - Whether the patch is **truly correct**, not just test-passing
     - Captures your **core contribution (symbolic verification + CEGF)**
   - **Formula**
     - LogicalCorrectnessRate = (# patches with NO solver counterexample AND passes tests) / (total tasks)
   - **Expected Direction of Change**
     - ↑ significantly vs baseline
   - **Why it matters**
     - Directly validates your hypothesis:
       - solver reduces **logical regressions + missed edge cases**
3. **Regression Rate (optional)**
   - What it measures
     - How often patches introduce new bugs
     - Captures weakness of test-only validation
   - Formula
     - RegressionRate =(# patches that pass failing tests BUT fail passing tests or solver) / (# successful patches)
   - Expected Direction of Change
     - ↓ lower than baseline
   - Why it matters
     - Shows symbolic reasoning prevents silent logical regressions (your key claim)

##### **2. Efficiency Metrics**

- These capture **cost vs benefit**.

---

- The efficiency metrics are designed to capture whether symbolic reasoning reduces search waste enough to justify its overhead.

1. ==**Tokens per Success**==
   - What it measures
     - Efficiency of solving bugs
   - Formula
     - TokensPerSuccess = TotalTokensUsed / \#SuccessfulTasks
   - Expected Direction of Change
     - ↓ significantly
   - Why it matters
     - Strong metric showing “we solve bugs cheaper”
2. ==**Average # of Repair Iterations**==
   - What it measures
     - How many refinement loops needed
   - Formula
     - AvgIterations = total_iterations / total_tasks
   - Expected Direction of Change
     - ↓ lower
   - Why
     - Counterexamples should guide faster convergence
3. **Token Consumption**
   - What it measures
     - Total LLM usage per task
   - Formula
     - TokenConsumption = sum(tokens_prompt + tokens_completion across all iterations)
   - Expected Direction of Change
     - ↓ or ≈ (ideally lower, but may slightly increase)
     - Might go up slightly due to critiques but should decrease if search becomes more efficient
4. ==**Solver Overhead**==
   - What it measures
     - Cost of symbolic reasoning
   - Formula
     - SolverOverhead = solver_time / total_runtime
   - Expected Direction of Change
     - ↑ (non-zero, controlled)
   - Why
     - Show overhead is worth it
5. ==**Wall-clock Runtime**==
   - What it measures
     - Total execution time per task
   - Formula
     - Runtime = time_end - time_start
   - Expected Direction of Change
     - ↑ slightly OR ≈
     - Solver adds overhead
     - But fewer iterations may compensate

##### **3. Behavioral Diagnostics (VERY valuable for analysis)**

- These help explain _why_ your method works.

---

1. **Counterexample Detection Rate**
   - What it measures
     - How often solver finds errors in patches
   - Formula
     - CER = (# patches where solver finds counterexample) / (# patches evaluated by solver)
   - Expected Direction of Change
     - High (non-trivial)
     - If high → solver is adding signal
     - If low → solver may be redundant
2. **Useful Critique Rate**
   - What it measures
     - Whether solver feedback actually helps
   - Formula
     - UsefulCritiqueRate = (# critiques that lead to a DIFFERENT next patch) / (# critiques generated)
   - Expected Direction of Change
     - High
   - Why
     - Validates CEGF loop effectiveness
3. **Repeated Failure Rate**
   - What it measures
     - How often LLM gets stuck
   - Formula
     - RepeatedFailureRate = (# iterations with same/similar failed patch) / (total iterations)
   - Expected Direction of Change
     - ↓ significantly
   - Why
     - Solver should break loops
4. **Patch Diversity**
   - What it measures
     - Variation across generated patches
   - Formula (example using edit distance)
     - PatchDiversity = avg(edit_distance(patch_i, patch_j))
   - Expected Direction of Change
     - ↑ moderate
     - More exploration, less collapse
5. **Failure Mode Breakdown**
   - What it measures
     - Type of bugs remaining
   - No strict formula
   - Categorization:
     - incorrect condition
     - missing guard
     - arithmetic mistake
   - Expected Direction of Change
     - Shift away from logic-related failures
   - Why
     - Confirms your system specifically improves predicates, invariants, edge cases

### ==**3. Experiment Structure**==

- What experiments are run?
- What variables are controlled vs varied?

---

#### **1. Benchmarks/Datasets**

- choose datasets / benchmarks and explain what it is + how it fits this project, how to setup,

---

- The primary benchmark is **SWE-bench Verified**, a 500-instance human-validated subset of SWE-bench intended for reliable evaluation of coding agents.
- From this pool, the study will curate up to 40 candidate tasks and report primary results on the 15–25 tasks that remain after filtering for logic-heavy, solver-expressible bugs.
- The inclusion rule is simple and implementation-oriented: keep tasks whose gold fixes primarily adjust conditionals, boolean expressions, comparison operators, arithmetic guards, or small-scope return logic; exclude tasks dominated by dependency changes, large refactors, file I/O, configuration edits, or architectural redesign. This restriction is scientifically motivated because the proposed verifier is local and predicate-focused, and practically motivated because whole-repository symbolic reasoning is out of scope.
- We treat this evaluation as a small logic-heavy dev subset intended to compare pipeline behavior and failure modes, not to establish statistically significant benchmark superiority.

##### SWE-bench Verified

###### **Scale**

- 500 + issues

###### **Structure & Format**

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

#### **2. Baselines**

- What is the structure of the baseline?
  1.  Different modeling (e.g., simplex flow, CTMC for discrete diffusion, VAE)
  2.  Different sampling (e.g., noise scheduler, temperature, self-condition)
  3.  Reference Test Set Statistics to compare against actual molecules
- What models are used (if any)?
  - Model name / architecture
  - Training
  - Version / checkpoint
  - Role in system (e.g., embedding, generation, scoring)

---

- Every system variant uses the same base LLM, the same prompt skeleton, the same budget on prompt tokens and output tokens, the same maximum number of repair iterations, the same localizer and context extractor, the same repository checkout process, and the same patch-application mechanism.
- The **baseline**
  - an iterative neural-only agent that receives the issue description, failing test names, and localized code context, proposes a patch, runs execution checks, and refines only from execution feedback.
-  The **full method**
  - Pipeline:
    1. load task
    2. localize relevant code
    3. build prompt from:
       - bug report
       - failing tests
       - local code
    4. LLM proposes patch
    5. apply patch
    6. run symbolic verification on patched region
    7. if solver finds violation:
       - generate counterexample
       - convert to critique
       - re-prompt LLM
    8. repeat until no counterexample or budget exhausted

#### **3. Tools**

##### Models

- gpt-5.2

##### Programs

- [[Z3]] -> [[CrossHair]]

#### **4. Experiment Controls/Fairness Setup**

##### **Controlled Variables**

- This step helps with coming up with ablation studies

---

- **LLM model**
  - same model across all runs (e.g., GPT-4o)
- **Prompt structure**
  - same base template
  - same sections:
    - bug report
    - failing tests
    - code context
  - only difference:
    - presence/absence of symbolic critique block
- **Token budget**
  - max input tokens
  - max output tokens
- **Iteration budget**
  - same max repair attempts (e.g., 3–5 iterations)
- **Context extraction strategy**
  - same localization + slicing method
  - same number of files / lines included
- **Task set**
  - same exact subset of SWE-bench + HumanEval tasks
  - identical ordering across runs
- **Execution environment**
  - same Python version
  - same dependencies
  - same test harness
- **Patch application mechanism**
  - same diff application logic
  - same rollback/reset behavior
- **Randomness / determinism**
  - fix seed if possible (or log it)
  - same temperature / decoding params

##### **Independent Variables (Varied)**

- This step helps with coming up with ablation studies

---

- **Symbolic verification (on/off)**
  - baseline: no solver
  - method: solver enabled
- **Counterexample-guided feedback (CEGF)**
  - whether solver outputs are fed back into the LLM
- **Feedback source type**
  - execution-only feedback (baseline)
  - symbolic counterexample feedback (method)
- **Impact slicing**
  - enabled vs disabled (optional ablation)
  - tests whether narrowing program scope matters
- **Solver configuration**
  - timeout
  - constraint depth / path exploration
  - determines strength vs cost tradeoff
- **Refinement loop type**
  - no refinement (optional)
  - execution-only refinement
  - symbolic-guided refinement

#### \*\*5. Ablation Studies

- List each experiment + its ablation

---

1. Neural Only
   - Baseline. Tests whether a normal LLM repair loop can solve the task without symbolic help.
2. Neural + slicing
   - Tests whether better localization / reduced context alone helps, without solver verification.
3. Neural + solver
   - Tests whether solver verification detects issues, but without letting the LLM use the critique to refine.
4. Neural + cegf
   - Full Symbiotic-SWE. Tests whether counterexample-guided feedback improves repair.

#### ==**6. Experiment Protocol (Explanation/Paragraphs)**==

- How is each experiment executed?
- Example:
  1.  Load input
  2.  Run system
  3.  collect outputs
  4.  compute metrics

---

- Every iteration logs the prompt, patch diff, patch-application result, execution feedback, symbolic status (`SAT`, `UNSAT`, `UNKNOWN`, or `TIMEOUT`), extracted counterexample if any, and critique text.

1. Issue + failing tests
   - Because LLM outputs are stochastic, the preferred analysis is paired across identical tasks and, if budget allows, repeated over multiple seeds or repeated API calls with fixed decoding parameters.
   - For each task, the system checks out the benchmark’s base commit into an isolated workspace, extracts the initial local context, and then runs either the baseline or full method for a fixed number of iterations, ideally three to five.
2. minimal bug localization
3. local context extraction
4. LLM patch proposal
5. patch application
6. patch-centered slicing
7. symbolic harness construction
8. CrossHair/Z3 verification
9. counterexample-to-critique transformation
   - For intermediate iterations, the system runs the fail-to-pass target tests and the symbolic verifier; on final acceptance, it also runs the pass-to-pass regression tests.
10. refined proposal

### **4. Threats to Validity (How could this be wrong?)**

- What could invalidate your conclusions?
- Types:
  - dataset bias
  - metric limitations
  - experimental setup bias
  - implementation artifacts
- **Output of this section should be:**
  - A **critical reflection on limitations of evaluation**

---

#### **1. [Name of Threat]**

- **Description**
  -
- **Potential Issues**
  -
- **Impact**
  -
- **Mitigation**
  -
