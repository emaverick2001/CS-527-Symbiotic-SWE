Source run: `artifacts/runs/dev_ablation_gpt_5_3_codex_sympy_real_tests_v4`
## **6. Analysis (Why did it behave this way?)**
- **Purpose:**
    - Explain _why_ the system behaves as observed in evaluation
    - Provide **causal insights**, not just observations
    - Connect results back to hypothesis, design choices, problem formulation
	- Observations → Explanations → Failure Modes → Tradeoffs → Insights
- **Key Question:**
    - _Why did the method perform the way it did, and what does that reveal about the problem and design?_
- **Constraints:**
    - No new experiments (belongs to Evaluation)
    - No system description (belongs to Proposed Technique)
    - Must explain **observed results only**
    - Avoid repeating raw results → focus on **interpretation**
---
### **0. Key Visuals**
- Visual representations that help the reader understand:  
	1. The problem  
	2. The system  
	3. The artifacts  
	4. The experimental setup  
	5. The main results  
	6. The ablations  
	7. The qualitative behavior  
	8. The failure modes  
	9. The cost/efficiency tradeoffs  
- **Output of this section should be:**  
	- A visual understanding of the system, artifacts, evaluation, and evidence for the claims
---
- Must-have visuals
	1. System Overview/ Dataflow Diagram
		- Bug Report + Repo + Tests  
		- ↓  
		- Context Retrieval  
		- ↓  
		- Neural Patch Proposal  
		- ↓  
		- Impact Slicing  
		- ↓  
		- Constraint Extraction  
		- ↓  
		- Symbolic Verification  
		- ↓  
		- Counterexample Generation  
		- ↓  
		- Natural Language Critique  
		- ↓  
		- LLM Patch Refinement Loop
	2. **Closed-loop CEGF repair diagram**
		- shows the closed-loop interaction between the LLM and symbolic solver
	    - Shows the LLM-solver feedback loop.
	3. **Ablation/component matrix**
	    - Shows what neural_only, neural_slicing, neural_solver, and neural_cegf mean.
	4. Main/Overall performance comparisons
		- Main Comparison:  
			- neural_only  
			- neural_slicing  
			- neural_solver  
			- neural_cegf  
		- Metrics:  
			- task resolution rate  
			- hidden test pass rate  
			- logical regression rate  
			- average iterations  
			- token cost  
			- runtime overhead
- Strong secondary visuals
	1. Motivating failure example
		- Shows why neural-only repair is insufficient.
	2. Counterexample-guided case study trace
	    - Shows how the method actually fixes a bug.
	3. **Iteration vs success plot**
	    - Supports claims about convergence.
	4. **Solver outcomes histogram**
	    - Shows sat/unsat/timeout/error distribution.
	5. **Runtime/token overhead box plot**
	    - Supports cost-efficiency discussion.
	6. **Failure mode taxonomy table**
	    - Makes limitations concrete and research-grade.
##### **1. Problem / Motivation Visual**
- **Purpose:** Show why the problem matters.
	- Use this when you need to make the reader quickly understand the gap, pain point, or failure mode.
	- This is usually one of the strongest visuals for the **Introduction**.
- Examples
	- Current neural-only repair loop fails on logic-heavy bugs
	- Test-based feedback misses hidden logical errors
	- LLM repeats similar failed patches without stronger feedback
	- Execution feedback only works when tests expose the bug
- Possible formats
	- Failure example diagram
	- Before/after comparison
	- Small motivating example
	- Toy code snippet with hidden edge case
	- Problem taxonomy table
---
1. Success vs Failure Examples
	- Buggy function passes visible tests  
	- Hidden edge case fails  
	- Neural-only patch looks plausible  
	- Solver finds counterexample  
	- Counterexample guides correct repair
##### ==**2. System Overview Visual**==
- Purpose: Show the full architecture at a glance.
	- This is your “what did we build?” visual.
	- This should probably be one of your **main Method visuals**.
- Examples
	- End-to-end dataflow
	- System architecture
	- Module interaction diagram
	- Pipeline diagram
- Possible formats
	- Box-and-arrow diagram
	- Layered architecture diagram
	- Input/intermediate/output flow
---
##### ==**3. Algorithm / Loop Visual**==
- Purpose: Show the repeated decision process, not just the static system.
	- This is different from the system overview. A system overview shows components. A loop visual shows control flow over time.
	- This visual is especially important because your contribution is not just “using a solver.” It is using the solver **inside a repair feedback loop**.
- Examples
	- Repair loop
	- Agent loop
	- CEGF iteration loop
	- Verification-refinement loop
	- Planner-executor-verifier loop
- Possible formats
	- Circular loop diagram
	- State machine
	- Iterative flowchart
	- Pseudocode box
---
1. Core Algorithm
	```
	Algorithm: Symbiotic-SWE
	
	Input:
	  task x = <issue, repo, fail-tests, pass-tests>
	  iteration budget B
	
	1. c ← LocalizeAndExtractContext(x)
	2. h ← ∅
	3. for k = 1 ... B:
	4.     p ← LLM_Propose(c, h)
	5.     if not ApplyPatch(p):
	6.         h ← h ∪ {"Patch did not apply cleanly."}
	7.         continue
	8.     run target execution checks on fail-tests
	9.     s ← PatchCenteredSlice(p)
	10.    H ← BuildSymbolicHarness(s, type hints, asserts, test-derived expectations)
	11.    v ← VerifyWithCrossHairAndZ3(H)
	12.    if TestsPass(fail-tests, pass-tests) and v = UNSAT:
	13.         return SUCCESS, p
	14.    if v = SAT:
	15.         ce ← ExtractCounterexample(v)
	16.         q ← NaturalLanguageCritique(ce)
	17.    else:
	18.         q ← ExecutionOrVerifierFeedback(v)
	19.    h ← h ∪ {q}
	20.    if ContextSeemsInsufficient(q):
	21.         c ← ExpandContext(c)
	22. return FAILURE
	```
##### **4. Artifact / Data Structure Visual**
- Purpose: Show what objects exist inside the system.
	- This is useful when your method depends on intermediate artifacts that are not obvious.
	- This is useful in the **Method** or **Appendix** because it helps readers understand what your pipeline actually produces.
- Examples
	- Task schema
	- Patch object
	- Program slice
	- Symbolic specification
	- Solver result
	- Counterexample
	- Critique
	- Iteration history
- Possible formats
	- JSON/schema block
	- Entity relationship diagram
	- Artifact flow diagram
	- Table of artifacts
---
##### ==**5. Experimental Setup Visual**==
- Purpose: Show how the experiment is structured.
	- This is the “how did you evaluate it?” visual.
	- This helps separate your **method pipeline** from your **evaluation pipeline**.
- Examples
	- Dataset split
	- Evaluation pipeline
	- Benchmark construction
	- Logic-heavy bug filtering
	- Baseline comparison setup
	- Metrics flow
- Possible formats
	- Experiment pipeline diagram
	- Dataset table
	- Baseline matrix
	- Evaluation protocol diagram
---
1. Experiment Visual
	- SWE-bench / logic-heavy subset  
	- ↓  
	- Run each baseline  
	- ↓  
	- Collect patches + tests + solver traces  
	- ↓  
	- Measure:  
		- resolution rate  
		- logical correctness  
		- regressions  
		- iterations  
		- tokens  
		- runtime overhead
##### ==**6. Baseline / Ablation Visual**==
- Purpose: Show what each experimental variant includes or removes.
	- This is a component-contribution visual, not merely a table.
	- This belongs in the **Experimental Setup** section, not the qualitative results section.
---
1. Ablation Table
	- Rows:
		- neural_only
		- neural_slicing
		- neural_solver
		- neural_cegf
	- Columns:
		- LLM patching
		- slicing
		- solver
		- counterexample feedback
		- real tests
		- purpose
##### ==**7. Main Result Visual**==
- Purpose: Show the primary empirical claim.
	- This answers: “Did the method work?”
	- This is usually the most important **Quantitative Results** visual.
- Examples
	- Overall success rate
	- Resolved tasks
	- Logical correctness improvement
	- Regression reduction
	- Pass@1 / Pass@k
	- Task resolution by bug type
- Possible formats
	- Main results table
	- Bar chart
	- Grouped bar chart
	- Line plot
	- Scatter plot
---
##### **8. Convergence / Process Dynamics Visual**
- Purpose: Show how the system improves over iterations.
	- This is stronger than only reporting final success rate because your method is iterative.
- Examples
	- Iteration vs success probability
	- Number of failed patches before repair
	- Repeated failure reduction
	- Search entropy over time
	- Counterexample count per iteration
	- Patch diversity over iterations
- Possible formats
	- Line plot
	- Step plot
	- Trajectory plot
	- Sankey diagram
	- Timeline
---
1. Trajectory / Process Visualization
	- Iteration 0 → LLM produces plausible but incorrect patch  
	- Iteration 1 → solver finds counterexample: lst = []  
	- Iteration 2 → LLM handles empty list edge case  
	- Iteration 3 → tests pass and solver finds no violation

##### **9. Qualitative Case Study Visual**
- Purpose: Show one or two concrete examples deeply.
	- This answers: “What does success actually look like?”
- Examples
	- Successful repair trace
	- Failure trace
	- Counterexample-guided correction
	- Neural-only vs Symbiotic-SWE side-by-side
	- Patch evolution
- Possible formats
	- Annotated timeline
	- Side-by-side patch diff
	- Trace table
	- Before/after code snippet
	- Flow diagram with critique bubbles
---
- The case studies should show that Symbiotic-SWE is most useful when the bug is **local, logic-heavy, and expressible as a symbolic constraint**, while failures tend to arise from **missing context, weak symbolic encodings, or solver overhead that exceeds the benefit of refinement**.
- For each selected case, save:
	- `task_id`
	- `bug_type`
	- localized source snippet
	- failing tests (Tf)(T_f)(Tf​)
	- pass-to-pass tests (Tp)(T_p)(Tp​)
	- baseline patch
	- Symbiotic-SWE patch
	- solver result: `SAT`, `UNSAT`, `UNKNOWN`, or `TIMEOUT`
	- counterexample, if any
	- critique text
	- number of iterations
	- token usage
	- runtime breakdown
	- final outcome
###### **1. Successful Counterexample-Guided Repair**
- **Purpose**
    - Show the strongest version of your method working as intended.
- **What to look for**
    - Baseline produces an incorrect or incomplete patch.
    - Solver finds a concrete counterexample.
    - Counterexample critique causes the next LLM patch to fix the issue.
- **Why this is high insight**
    - Directly supports your core claim:
        - symbolic feedback improves logical repair.
- **Evidence to include**
    - original bug report
    - localized code snippet
    - baseline patch
    - solver result
    - counterexample
    - critique text
    - refined patch
- **Research questions supported**
    - RQ1: task resolution / logical correctness
    - RQ2: reduced repeated failures
    - RQ4: bug types where solver helps
---
###### **2. Baseline Passes Tests but Symbolic Solver Finds a Logical Flaw**
- **Purpose**
    - Demonstrate the limitation of execution-based feedback.
- **What to look for**
    - Neural-only patch passes `FAIL_TO_PASS` tests.
    - Patch either fails `PASS_TO_PASS` tests or violates symbolic constraints.
    - Solver identifies an untested edge case.
- **Why this is high insight**
    - This is the clearest example of:
        - passing tests ≠\neq= logical correctness
- **Evidence to include**
    - failing tests that now pass
    - previously passing tests or symbolic condition that breaks
    - solver-discovered counterexample
    - explanation of why tests missed it
- **Research questions supported**
    - RQ1: logical correctness beyond task success
    - RQ2: regression reduction
---
###### **3. Context Insufficiency Case**
- **Purpose**
    - Analyze cases where the model fails because local context was too small.
- **What to look for**
    - Localized snippet does not include helper function, class invariant, or caller context.
    - LLM makes a plausible local edit but misses broader dependency.
    - Solver feedback may identify failure, but critique is not enough without more code context.
- **Why this is high insight**
    - Tests your minimal-context-first methodology.
    - Motivates optional context expansion.
- **Evidence to include**
    - initial local context
    - missing dependency / helper
    - failed patch
    - critique
    - expanded context, if used
- **Research questions supported**
    - RQ2: repeated failure / wasted search
    - RQ4: failures caused by weak slicing or missing context
---
###### **4. Weak Symbolic Encoding Case**
- **Purpose**
    - Show where solver feedback fails because the symbolic representation is incomplete.
- **What to look for**
    - Solver returns `UNSAT`, but patch is still wrong.
    - Constraint extraction misses key semantic behavior.
    - Bug depends on library semantics, side effects, or complex object behavior not encoded.
- **Why this is high insight**
    - Distinguishes:
        - solver limitation
        - encoding limitation
        - LLM limitation
- **Evidence to include**
    - constraints extracted
    - missing constraint
    - solver result
    - actual failure
- **Research questions supported**
    - RQ4: where symbolic encoding is too weak
- **Example framing**
    - “The solver did not find a violation because the encoded slice omitted the library-specific semantic condition responsible for the failure.”
---
###### **5. Efficiency Win Case**
- **Purpose**
    - Show that symbolic critique can reduce wasted search.
- **What to look for**
    - Baseline takes several iterations or repeats similar wrong patches.
    - Symbiotic-SWE fixes the task in fewer iterations after receiving a counterexample.
- **Why this is high insight**
    - Supports your claim that CEGF improves convergence, not only correctness.
- **Evidence to include**
    - iteration-by-iteration patch summaries
    - token counts
    - critique text
    - final success iteration
- **Research questions supported**
    - RQ2: repeated failures and search waste
    - RQ3: overhead offset by convergence
---
###### **6. Runtime Overhead Case**
- **Purpose**
    - Provide a balanced systems-level analysis.
- **What to look for**
    - Solver adds significant time.
    - Either:
        - overhead is worthwhile because it prevents extra LLM iterations, or
        - overhead is not worthwhile because the task was simple.
- **Why this is high insight**
    - Makes your paper more credible as a systems project.
- **Evidence to include**
    - solver time
    - LLM time
    - total runtime
    - iteration count
    - tokens used
- **Research questions supported**
    - RQ3: overhead vs convergence tradeoff
###### **7. Solver Adds No Useful Signal**
- **Purpose**
    - Show a boundary case where Symbiotic-SWE does not help.
- **What to look for**
    - LLM patch already passes tests and solver returns `UNSAT`.
    - Or solver returns `UNKNOWN` / timeout without producing actionable feedback.
- **Why this is high insight**
    - Helps avoid overclaiming.
    - Shows symbolic reasoning has overhead and is not always necessary.
- **Evidence to include**
    - solver status
    - runtime overhead
    - final patch
    - whether CEGF changed anything
- **Research questions supported**
    - RQ3: runtime/token overhead
    - RQ4: where solver fails or is unnecessary
---
###### **8. Missing Guard / Invalid Predicate Case**
- **Purpose**
    - Show a bug type where symbolic reasoning is especially useful.
- **What to look for**
    - Bug caused by missing domain check before a predicate or comparison.
    - Example patterns:
        - comparing non-real values
        - checking ordering before verifying type/domain
        - missing `None` / empty input guard
- **Why this is high insight**
    - These cases are often small, local, and solver-expressible.
    - They match your logic-heavy task definition well.
- **Evidence to include**
    - original predicate
    - failing condition
    - symbolic counterexample
    - repaired guard condition
- **Research questions supported**
    - RQ4: which bug types benefit from solver feedback
- **Example framing**
    - “The original code assumed xxx was orderable, but the counterexample showed that xxx could be complex / null / empty. The critique pushed the model to add an explicit guard before evaluating the predicate.”
---
##### **10. Failure Mode / Error Analysis Visual**
- Purpose: Show where the method breaks.
	- This is often what makes a report feel research-grade rather than demo-grade.
	- This is great for **Discussion**, **Limitations**, or **Error Analysis**.
- **What to include for each case study:**
	- task identifier or anonymized label
	- bug type
	- input evidence
	    - problem statement
	    - failing test
	    - localized code
	- expected behavior
	- what the system did
	- where the failure occurred
	- diagnostic artifact
	- likely root cause
	- possible fix
- Examples
	- Solver timeout
	- Weak symbolic encoding
	- Incorrect slice
	- Unsupported Python feature
	- Counterexample not understandable
	- LLM ignores critique
	- Tests still insufficient
- Possible formats
	- Failure taxonomy table
	- Stacked bar chart
	- Confusion-style matrix
	- Diagnostic tree
	- Case study grid
---
1. Failure taxonomy table

|Failure Type|Cause|Example|Possible Fix|
|---|---|---|---|
|Weak slice|Relevant function omitted|Bug depends on helper function|Better call graph expansion|
|Solver timeout|Constraints too complex|Loop-heavy code|Timeout-aware fallback|
|Bad critique|Counterexample poorly translated|Critique too vague|Structured critique template|
|LLM ignores feedback|Model repeats same patch|Same bug remains|Memory of failed patches|
##### **11. Cost / Efficiency Visual**
- Purpose: Show the tradeoff between better reasoning and extra overhead.
	- This is important because your method adds symbolic verification, so you need to justify when the cost is worth it.
- Examples
	- Runtime overhead
	- Token overhead
	- Solver time
	- Iterations saved
	- Cost per resolved task
	- Overhead vs accuracy gain
- Possible formats
	- Box plot
	- Scatter plot
	- Cost-benefit table
	- Pareto frontier
	- Runtime breakdown chart
---
##### **12. Sensitivity / Robustness Visual**
- Purpose: Show whether the method depends too heavily on specific settings.
	- This is optional but useful if you have enough experiments.
	- This is usually an **Appendix** or secondary result.
- Examples
	- Solver timeout threshold
	- Number of repair iterations
	- Context retrieval size
	- Slice size
	- Counterexample critique format
	- Model temperature
- Possible formats
	- Line plot
	- Heatmap
	- Small multiples
	- Parameter sweep table
---

### **1. Key Observations (What patterns do we see?)**
- Purpose:
	- Summarize the most important empirical patterns from the evaluation before explaining why they happened.
	- This section should act as the “results snapshot” that tells the reader what changed across methods, tasks, metrics, and ablations.
	- What are the 3–5 most important patterns shown by the results?
- What to include:
	- High-level trends across metrics
		- Example: Symbiotic-SWE improves logical correctness more than raw task success.
	- Differences between methods or baselines
		- Example: The solver-guided system requires fewer repeated patch attempts than the neural-only baseline.
	- Differences across task categories
		- Example: Gains are largest on missing-guard and comparison-operator bugs.
	- Unexpected or surprising behaviors
		- Example: Solver feedback improves patch quality but increases runtime.
	- Stability or variance patterns
		- Example: Performance is consistent on small local bugs but unstable on multi-file bugs.
	- Any important failure pattern that appears repeatedly
		- Example: The solver times out when the extracted slice includes too many dependencies.
- What to exclude:
	- Do not deeply explain root causes yet. Save that for the discussion section.
	- Do not restate every number from every table.
	- Do not introduce new metrics that were not already defined.
	- Do not make claims that are not supported by a table, figure, or logged artifact.
	- Do not overclaim generality beyond the evaluated tasks.
- Level of abstraction:
	- Stay above individual implementation details.
	- Focus on behavioral patterns, not code-level debugging.
	- Use phrases like:
	    - “Across the logic-heavy subset…”
	    - “Compared to the neural-only baseline…”
	    - “The largest gains occur when…”
	    - “The system degrades when…”
	    - “A recurring failure mode is…”
- Output of this section should be:
	- A small set of **evidence-backed behavioral patterns** that prepare the reader for the deeper root-cause analysis.
	- Each observation must be backed by at least one result artifact: a table, figure, metric, ablation result, or case study. If an observation cannot be tied to evidence, move it to speculation or remove it.
---
1. **Impact slicing is the strongest raw real-test performer**
	- Evidence:
	- Main ablation metrics: `artifacts/runs/dev_ablation_gpt_5_3_codex_sympy_real_tests_v4/metrics.json`
	- `neural_slicing` resolves 6 of 7 tasks, compared with 4 of 7 for `neural_only`, 3 of 7 for `neural_cegf`, and 2 of 7 for `neural_solver`.
	- `neural_slicing` also evaluates all 7 tasks and records zero patch-apply failures.
	- Pattern:
	- Across the logic-heavy SymPy subset, localization through impact slicing is the clearest driver of raw test-passing repair performance.
	- Transition:
	- This motivates analyzing whether slicing improves the model's ability to focus edits on the correct code region before adding symbolic feedback.
2. **CEGF provides solver-backed logical correctness, but does not win raw task success**
	- Evidence:
	- Main ablation metrics: `metrics.json`
	- `neural_cegf` resolves 3 of 7 tasks and records a logical correctness rate of 3 of 7.
	- `neural_slicing` resolves more tasks, but has no solver coverage and therefore no solver-backed logical correctness confirmations under the defined metric.
	- Pattern:
	- CEGF is not the best raw success condition in the latest run. Its value is stronger on verification and diagnostics: successful CEGF patches are paired with symbolic outcomes.
	- Transition:
	- This motivates separating benchmark-facing success from logical correctness in the results discussion.
3. **Symbolic checking without feedback remains insufficient**
	- Evidence:
	- Main ablation metrics: `metrics.json`
	- `neural_solver` reaches full solver coverage but resolves only 2 of 7 tasks.
	- It terminates with `solver_sat_no_feedback` on 2 tasks and `tests_failed_after_solver` on 3 tasks.
	- Pattern:
	- The solver can identify or rule out symbolic issues, but checking alone does not reliably improve repair when the system cannot convert solver results into an updated patch.
	- Transition:
	- This motivates analyzing the feedback transformation step as a separate component from solver invocation.
4. **The methods solve different task subsets**
	- Evidence:
	- Per-task metrics: `artifacts/runs/dev_ablation_gpt_5_3_codex_sympy_real_tests_v4/*/*/metrics.json`
	- `neural_slicing` resolves every task except `sympy__sympy-23413`.
	- `neural_cegf` resolves `sympy__sympy-13031`, `sympy__sympy-19346`, and `sympy__sympy-24539`.
	- `neural_only` resolves `sympy__sympy-17318`, `sympy__sympy-19346`, `sympy__sympy-24213`, and `sympy__sympy-24539`.
	- Pattern:
	- Performance is task-dependent. Different ablations succeed on different repair problems, which suggests that localization, plain neural repair, and symbolic feedback help under different conditions.
	- Transition:
	- This motivates using qualitative case studies rather than relying only on aggregate success rates.
5. **Patch application is no longer a primary bottleneck**
	- Evidence:
	- Patch artifacts: `patch_manifest.json`
	- Error log: `errors.log`
	- `errors.log` is empty in the latest run.
	- Average patch-apply failures are low across all conditions: `neural_slicing` 0.00, `neural_solver` 0.00, `neural_only` 0.14, and `neural_cegf` 0.57.
	- Pattern:
	- The latest run mostly reaches real test evaluation instead of failing early during diff parsing or patch application.
	- Transition:
	- This motivates treating remaining failures as repair-quality or feedback-quality failures rather than harness failures.
6. **CEGF increases feedback activity and symbolic coverage at higher token cost**
	- Evidence:
	- Efficiency and feedback metrics: `metrics.json`
	- `neural_cegf` records 7 critique events, full solver coverage, and the highest average token usage among conditions.
	- `neural_cegf` also has higher tokens per success than `neural_only` and `neural_solver`.
	- Pattern:
	- Counterexample-guided repair produces richer feedback and verification artifacts, but the extra loop work increases model cost.
	- Transition:
	- This motivates reporting effectiveness and efficiency together rather than ranking methods only by real-test success.
7. **The latest run is stable enough for paper tables**
	- Evidence:
	- Run manifest: `run_manifest.json`
	- Aggregate metrics: `metrics.json`
	- Error log: `errors.log`
	- The manifest records the provider, model, all 7 task IDs, and all 4 conditions. The run has an empty error log and complete aggregate metrics.
	- Pattern:
	- The latest artifact set is cleaner than earlier smoke and dev runs, which were affected by patch-apply failures and local environment issues.
	- Transition:
	- This motivates using `dev_ablation_gpt_5_3_codex_sympy_real_tests_v4` as the primary result source for figures, tables, and discussion.
8. [Observation Name: Short Claim]
	- Evidence:  
		- Point to the relevant table, figure, metric, or case study.  
		- Mention the direction of change, not every raw value.  
	- Pattern:  
		- Describe the behavioral pattern in plain language.  
	- Transition:  
		- Briefly state what this observation motivates analyzing next.
### **2. Error Analysis (Where and how does it fail?)**
- **Purpose:**
    - Analyze the cases where the system fails, partially succeeds, or produces low-quality outputs.
    - Identify recurring failure modes across pipeline components, task types, and ablation settings.
    - Explain which failures are caused by the LLM, the solver, the context extractor, the feedback loop, or the evaluation setup.
    - When Symbiotic-SWE fails, what component failed, what evidence shows the failure, and what likely caused it?
- **What to include:**
    - A taxonomy of recurring error types
        - Example: localization failure, incorrect patch, solver timeout, weak critique, repeated failure loop.
    - Failure counts or frequencies when available
        - Example: 4/20 tasks failed due to unsupported symbolic constructs.
    - Component-level attribution
        - Example: failure occurred during context extraction, patch generation, symbolic verification, or feedback transformation.
    - Root-cause hypotheses
        - Example: solver failed because the slice contained dynamic Python features not expressible in SMT.
    - Diagnostic signals
        - Example: repeated counterexample, solver `TIMEOUT`, patch apply error, same diff regenerated across iterations.
    - Connection to assumptions
        - Example: this failure violates the assumption that the bug is local and solver-expressible.
- **What to exclude:**
    - Do not only list failed tasks without categorizing them.
    - Do not blame the LLM or solver generically without evidence.
    - Do not repeat all evaluation results from the previous section.
    - Do not introduce new success metrics here.
    - Do not over-explain every single failed example. Focus on representative patterns.
    - Do not claim a root cause as certain unless the logs directly support it.
- **Expected structure:**
	- Start with a short paragraph summarizing the overall failure profile.
	- Then provide:
	    1. **Error Taxonomy**
	    2. **Root Causes of Errors**
	    3. **Mitigation / Future Fixes**, optional but useful
	- **Recommended number of items:**
	    - **4–7 error categories**
	    - **3–5 root-cause themes**
- **Level of abstraction:**
    - More detailed than Key Observations, but still focused on system behavior.
    - Discuss failures at the level of:
        - task type
        - pipeline stage
        - artifact
        - solver status
        - refinement behavior
    - Avoid diving into irrelevant line-by-line implementation debugging unless it directly explains the failure.
- **Output of this section should be:**
    - A structured understanding of **where the system fails**, **how the failure appears in artifacts/logs**, and **why it likely occurs**.
---
- 
#### **Error Taxonomy**
- **Purpose:**
    - Group failures into a small number of recurring categories.
    - Make failures comparable across tasks rather than treating each failed task as unique.
- **Instructions:**
    - Each error category should include:
        - failure name
        - affected pipeline stage
        - description
        - diagnostic signal
        - likely cause
        - example task or artifact
---
1. [Error Name]
	- Pipeline Stage: [Where it occurs]  
	- Description: [What goes wrong]  
	- Diagnostic Signal: [How we detect it]  
	- Likely Cause: [Why it happens]  
	- Example: [Task/case/artifact]
#### **Root Causes of Errors**
- **Purpose:**
    - Move from surface failures to the deeper reasons the system breaks.
    - Tie failures back to assumptions, design tradeoffs, and method limitations.
- **Instructions:**
    - Root causes should explain multiple failure modes, not just one task.
    - Each root cause should connect to:
        - violated assumption
        - affected components
        - evidence pattern
        - possible mitigation
---
1. [Root Cause Name]  
	- Violated Assumption: [What assumption failed?]  
	- Affected Failures: [Which error types does this explain?]  
	- Evidence Pattern: [How it appears in logs/results]  
	- Mitigation: [What could fix or reduce it?]
### **3. Sensitivity & Robustness (When does it break?)**
- **Purpose:**
    - Analyze how stable the system is under changes to configuration, inputs, task difficulty, and execution constraints.
    - Identify which parts of the system are brittle versus reliable.
    - Determine the conditions under which Symbiotic-SWE provides value and the conditions where solver overhead or weak symbolic coverage causes degradation.
    - Under what settings does the system remain effective, and under what settings does performance degrade or fail?
- **What to include:**
    - Sensitivity to hyperparameters
        - solver timeout
        - max repair iterations
        - context window size
        - LLM temperature
        - token budget
    - Sensitivity to input quality
        - noisy bug reports
        - missing traceback
        - incomplete failing test names
        - ambiguous localization signals
    - Sensitivity to task type
        - predicate bugs
        - missing guard bugs
        - arithmetic bugs
        - multi-file bugs
        - API misuse bugs
    - Sensitivity to symbolic constraints
        - missing type hints
        - weak postconditions
        - unsupported Python constructs
        - large slices causing solver timeout
    - Stability across runs
        - repeated runs with same task and settings
        - variance due to LLM randomness
        - repeated patch patterns
    - Breakpoint conditions
        - where runtime becomes too high
        - where solver returns mostly `UNKNOWN` or `TIMEOUT`
        - where context extraction fails frequently
        - where symbolic feedback stops improving refinement
- **What to exclude:**
    - Do not repeat the main results table unless comparing across changed conditions.
    - Do not treat every failure as a robustness issue. Some failures belong in Error Analysis.
    - Do not change multiple variables at once unless clearly labeled as a stress test.
    - Do not claim robustness without showing variation across runs, settings, or task conditions.
    - Do not overgeneralize from one task. Robustness claims should use repeated patterns.
- **Recommended number of items:**
    - **3–5 sensitivity dimensions**
- **Output of this section should be:**
    - A clear robustness profile showing when the system is reliable, when it degrades, and which variables most affect performance.
---
1. Brief overview of the robustness dimensions tested.
#### **Sensitivity Dimensions**
- **Purpose:**
    - Identify which configuration choices most affect the system’s behavior.
    - Separate stable design choices from fragile ones.
---
- [Sensitivity Dimension Name]  
	- What is varied: [Range or conditions]  
	- Metric affected: [Success rate, runtime, solver status, etc.]  
	- Observed pattern: [What changed]  
	- Interpretation: [What this means]
#### **Breakpoint Analysis**
- **Purpose:**
    - Identify the point where the system stops being useful or cost-effective.
    - This is where you explain the practical limits of the method.
- **What to include:**
    - solver timeout threshold where counterexamples stop being found
    - context size threshold where prompt noise increases
    - iteration threshold where additional attempts no longer help
    - task complexity threshold where local symbolic reasoning becomes insufficient
---
- 
### **4. Cost Analysis (What is the tradeoff?)**
- **Purpose:**
    - Analyze the resource-performance tradeoff introduced by the proposed method.
    - Determine whether improved repair quality justifies extra solver/runtime/token cost.
    - Identify when Symbiotic-SWE is more efficient than the baseline and when the symbolic component becomes too expensive.
    - Does symbolic verification produce enough improvement in correctness or convergence to justify its added cost?
- **What to include:**
    - Resource usage introduced by each system stage:
        - LLM generation time
        - token usage
        - patch application time
        - test execution time
        - slicing time
        - constraint extraction time
        - solver verification time
        - feedback transformation time
    - Cost comparison against baselines:
        - neural-only repair loop
        - neural + solver without critique, if included
        - full Symbiotic-SWE
    - Cost-normalized performance:
        - success per token
        - success per minute
        - logical correctness per solver-second
        - tokens per successful repair
    - Tradeoff behavior:
        - when solver overhead is offset by fewer iterations
        - when solver overhead dominates
        - when extra critique context increases token cost
        - when higher correctness comes at acceptable runtime cost
    - Per-stage bottlenecks:
        - which pipeline stage consumes the most time/resources
        - whether the bottleneck changes across task types
    - Conditions where the method is cost-effective:
        - small local slices
        - logic-heavy bugs
        - high baseline iteration count
        - repeated neural-only failures
- **What to exclude:**
    - Do not report resource numbers without connecting them to performance.
    - Do not only say “solver adds overhead.” Explain whether the overhead changes the outcome.
    - Do not mix cost analysis with root-cause failure analysis unless cost is the failure cause.
    - Do not compare runtime across methods if they were run in different environments.
    - Do not claim efficiency gains if the method only improves accuracy by using much more budget.
- **Expected structure:**
    1. Brief summary of the main cost-performance finding.
    2. Resource usage breakdown.
    3. Cost vs performance tradeoff.
    4. Efficiency gains and when they occur.
    5. Practical recommendation about when to use the method.
- **Recommended number of items:**
    - 1 per-stage cost table
    - 1 cost-vs-performance comparison table or figure
    - 2–4 main tradeoff observations
    - 1 short practical takeaway paragraph
- **Output of this section should be:**
    - A clear explanation of whether the proposed method is worth its added cost, and under which conditions.
---
#### **Resource Usage**
- **Purpose:**
	- Show where time, tokens, compute, and solver cost are spent.
	- Identify the primary bottlenecks in the system.
---
1. Resource Category: [Latency / Tokens / Solver Time / Test Time]  
	- Where it occurs: [Pipeline stage]  
	- How measured: [Metric or logging field]  
	- Expected behavior: [Increase/decrease vs baseline]  
	- Why it matters: [Connection to practicality]
#### **Cost vs Performance Tradeoff**
- **Purpose:**
	- Connect resource usage to outcome quality.
	- Show whether additional symbolic cost buys better correctness, fewer iterations, or fewer regressions.
---
1. [Tradeoff Name]  
	- Cost increases because: [Resource source]  
	- Performance changes because: [Metric improvement/degradation]  
	- Interpretation: [Worth it / not worth it / conditional]
#### **Efficiency Gains**
- **Purpose:**
    - Identify where the system becomes more efficient despite added solver cost.
    - Explain when symbolic feedback reduces total search cost.
- **What to look for:**
    - fewer LLM calls
    - fewer repeated patches
    - lower tokens per success
    - lower average iterations
    - fewer failed test executions
    - fewer manual-style trial-and-error loops
---
1. [Efficiency Gain Name]  
	- Observed when: [Condition]  
	- Metric evidence: [Metric]  
	- Reason: [Why the system becomes more efficient]
### **5. Mechanistic Explanation (Why does this happen?)**
- **Purpose:**
    - Explain why the observed results occur by connecting evaluation patterns to specific system components and design decisions.
    - Turn empirical observations into a causal story about how the method works.
    - Show whether the results support, partially support, or challenge the project hypothesis.
    - What system mechanism best explains the observed behavior, and what evidence supports that explanation?
- **What to include:**
    - A small set of mechanism-level explanations for major results.
    - Direct links between:
        - observation
        - component responsible
        - mechanism
        - evidence
        - implication
    - Explanation of positive results:
        - why symbolic feedback improves refinement
        - why counterexamples reduce repeated failures
        - why local slices make verification tractable
    - Explanation of negative or mixed results:
        - why solver overhead increases runtime
        - why symbolic verification fails on broad or dynamic tasks
        - why vague critiques fail to guide patch updates
    - Explicit connection to the hypothesis:
        - Does CEGF reduce ambiguity?
        - Does it narrow the patch search space?
        - Does it improve logical correctness beyond tests?
    - Evidence from artifacts:
        - patch diffs
        - counterexamples
        - solver logs
        - critique text
        - iteration histories
        - ablation comparisons
- **What to exclude:**
    - Do not merely restate observations.
    - Do not speculate without linking to evidence.
    - Do not introduce new results that were not shown earlier.
    - Do not claim full causality if the experiment only supports correlation.
    - Do not explain every single task. Focus on mechanisms that explain recurring patterns.
    - Do not repeat the full method description. Only reference components needed to explain behavior.
- **Expected structure:**
    1. Brief paragraph stating the overall mechanism.
    2. 3–5 mechanism explanations.
    3. For each mechanism:
        - observed behavior
        - responsible component
        - causal explanation
        - evidence
        - hypothesis connection
    4. Short synthesis paragraph explaining what this means for the system design.
- **Recommended number of items:**
    - **3–5 mechanisms**
    - **1–2 examples or artifacts per mechanism**
    - **1 concluding synthesis paragraph**
- **Output of this section should be:**
    - A causal explanation of how the system’s design decisions produce the observed results, including where the hypothesis is supported and where it breaks down.
---
#### **Mechanism Explanation Template**
- **Purpose:**
    - Make each explanation precise and evidence-backed.
---
1. Mechanism: [Short mechanism name]  
	- Observed behavior:  
		- [What pattern appeared in the results?]  
	- Responsible component:  
		- [Which system stage or design choice caused/contributed to this?]  
	- Mechanistic explanation:  
		- [Why this component likely produced the behavior.]  
	- Evidence:  
		- [Which table, figure, trace, case study, solver output, critique, or artifact supports this?]  
	- Connection to hypothesis:  
		- [How this supports, weakens, or qualifies the hypothesis.]
### **6. Key Takeaways (What did we learn?)**
- **Purpose:**
    - Summarize the most important lessons from the evaluation, error analysis, robustness analysis, cost analysis, and mechanistic explanation.
    - Convert detailed results into a concise set of insights that explain when the method works, when it fails, and what design decisions matter most.
    - Provide the reader with the “so what?” of the evaluation.
    - What are the 3–5 most important lessons someone should remember from this evaluation?
    - Consider 
		1. Performance takeaway  
			- Did the method help?  
		2. Scope takeaway  
			- When does the method work best?  
		3. Limitation takeaway  
			- When does it fail?  
		4. Cost takeaway  
			- Is the method worth the overhead?  
		5. Design takeaway  
			- What design choice mattered most?
- **What to include:**
    - High-level conclusions supported by prior sections.
    - Conditions where the method works best.
    - Main limitations or failure boundaries.
    - Most important cost-performance tradeoff.
    - Most important design insight.
    - Practical implications for future systems.
    - Clear statements that connect back to:
        - hypothesis
        - research questions
        - metrics
        - failure analysis
- **What to exclude:**
    - Do not introduce new results or new evidence.
    - Do not restate every metric.
    - Do not include long explanations that belong in Mechanistic Explanation.
    - Do not make broad claims beyond the evaluation scope.
    - Do not phrase uncertain findings as definitive conclusions.
    - Do not repeat the abstract or conclusion section.
- **Expected structure:**
    - Write **3–5 numbered takeaways**.
    - Each takeaway should have:
        1. **Takeaway statement**
        2. **Evidence basis**
        3. **Actionable implication**
---
1. Takeaway: [Concise insight]  
	- Evidence basis:  
	- [Which result/error pattern/mechanism supports this?]  
	- Actionable implication:  
	- [What should future users/builders/evaluators do because of this?]
### **7. (If time permits) Design Tradeoffs & Implications**
- **Purpose:**
    - Reflect on the major design choices made in the system.
    - Explain which tradeoffs were worthwhile, which were costly, and which should be changed in future versions.
    - Translate the evaluation results into broader system design insights.
    - What did the project reveal about how to design neuro-symbolic SWE agents?
- **What to include:**
    - Major design choices:
        - local context first vs full repository retrieval
        - solver-after-proposal vs solver-before-proposal
        - symbolic critique vs execution-only feedback
        - small slices vs broad program analysis
        - structured critique vs free-form critique
        - fixed iteration budget vs adaptive stopping
    - Tradeoffs for each choice:
        - correctness vs runtime
        - local simplicity vs missing context
        - solver precision vs solver coverage
        - critique detail vs token cost
        - automation vs manual specification effort
    - What was worth it:
        - design choices that improved correctness, stability, or interpretability
    - What was not worth it:
        - design choices that added complexity without clear benefit
    - What you would change:
        - better context expansion
        - better critique schema
        - adaptive solver calls
        - stronger constraint extraction
        - improved task filtering
    - Broader implications:
        - when solver-guided agents are useful
        - what future SWE agents should measure
        - what system components are most important
- **What to exclude:**
    - Do not repeat the full methodology.
    - Do not introduce new experimental results.
    - Do not make claims that are not supported by previous sections.
    - Do not only say “future work should improve X” without explaining the tradeoff.
    - Do not frame every limitation as a failure. Some are intentional design choices.
    - Do not overgeneralize beyond your evaluated task types.
- **Expected structure:**
    1. Brief paragraph summarizing the main design lesson.
    2. 3–5 design tradeoffs.
    3. For each tradeoff:
        - design choice
        - benefit
        - cost
        - implication
        - future change
    4. Final paragraph connecting these tradeoffs to broader SWE-agent design.
- **Recommended number of items:**
    - 3–5 design tradeoffs.
    - 1 short implication paragraph.
    - 1 future-design recommendation list.
- **Output of this section should be:**
    - A set of design insights that explain what choices mattered most and how future systems should be built differently.
---
1. Tradeoff: [Short tradeoff name]  
	- Design choice:  
		- [What choice did we make?]  
	- Benefit:  
		- [What did this improve?]  
	- Cost:  
		- [What did this make worse or harder?]  
	- Implication:  
		- [What does this teach us about system design?]  
	- Future change:  
		- [What would we modify next time?]