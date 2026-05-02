#### **High-Level Pipeline + Low-level Pipeline**

* Describe the system as a sequence of stages
* Remember to first create most simplistic working system then build ontop of it

1. First high-level then low-level
   1. for high-level mention the core data manipulations + actions + key system components + deliverables for respective section
   2. for low-level mention key datastructures + add implementation details to key components/deliverables for respective section so that you can implement the simplistic working system
   3. Once MVP is built add more details, optimizations, etc
   4. Optionally later on mention run artifacts produced + what datapoints to log

---

##### **0. Setup**

###### **Key Components / Deliverables**

1. local code environment setup
2. Setup Project Repository Structure
   1. Create top-level directories:
      * `assets/`
        * `diagrams/` - architecture and stage-flow diagrams
        * `figures/` - report figures derived from metrics
      * `artifacts/`
        * `runs/`
          * use this naming convention: `{YYYYMMDD_HHMMSS}_{agent}_{experiment}_{solver}_{seed}`
          * examples:
            * `20260502_132500_gpt4o_baseline_crosshair-z3_s0`
            * `20260502_140000_gpt4o_symbolic-feedback_crosshair-z3_s42`
            * `20260502_153000_gpt4o_ablation-no-symbolic_none_s42`
          * each completed run folder should contain:
            * `config.yaml` - exact resolved run config
            * `run_manifest.json` - command, git SHA, environment, timestamps
            * `task_manifest.json` - ordered tasks, split, filters, skipped tasks
            * `metrics.json` - aggregate run metrics
            * `stage_timings.csv` - one row per task/stage/iteration
            * `solver_queries.jsonl` - symbolic query envelopes
            * `solver_results.jsonl` - satisfiable/unsat/timeout/error results
            * `patch_manifest.json` - candidate patch ids and final selection
            * `evaluation_results.jsonl` - one task-level result per row
            * `errors.log` - human-readable failures
            * `summary.md` - short lab/report summary
          * task artifacts live in `tasks/{task_id}/iterations/iter_000/{stage}/`
        * `workspaces/` - temporary checked-out repositories for each run/task
        * `cache/`
          * `huggingface/` - dataset cache
          * `repositories/` - reusable repository clones or mirrors
          * `retrieval/` - indexes, symbol maps, chunk metadata
          * `solver/` - reusable symbolic summaries and constraint caches
        * `checkpoints/`
          * `patch_generator/` - learned patch-generation adapters if added later
          * `context_selector/` - learned retrieval/ranking checkpoints
          * `symbolic_models/` - learned symbolic abstractions if added later
        * `patches/`
          * `baseline/`
          * `symbolic_feedback/`
          * `ablations/`
        * `solver_outputs/`
          * `crosshair/`
          * `z3/`
          * `cvc5/`
        * `metrics/`
          * `baseline/`
          * `symbolic_feedback/`
          * `ablations/`
        * `logs/`
          * `pipeline/`
          * `evaluation/`
          * `solver/`
          * `errors/`
      * `configs/`
        * `global.yaml`
        * `baseline.yaml`
        * `evaluation.yaml`
        * `smoke.yaml`
        * `datasets/`
          * `swe_bench_verified.yaml`
        * `experiments/`
          * `baseline.yaml`
          * `symbolic_feedback.yaml`
          * `ablation_no_symbolic.yaml`
        * `solvers/`
          * `crosshair_z3.yaml`
          * `z3.yaml`
          * `cvc5.yaml`
      * `src/`
        * `dataset/` - benchmark loading, validation, preprocessing, manifests
        * `retrieval/` and `context_selection/` - logic-aware file/symbol/chunk selection
        * `patch_generation/` - candidate patch generation and refinement
        * `slicing/` - reduce candidate code to solver-relevant slices
        * `symbolic/` and `symbolic_reasoning/` - constraints, solver calls, counterexamples
        * `feedback/` - convert counterexamples into patch critiques
        * `evaluation/` - execute tests and aggregate metrics
        * `orchestration/` - run workspace and artifact management
        * `pipeline/` - public run entrypoints
        * `utils/` - shared config, paths, seeds, logging, I/O
      * `data/`
        * `benchmarks/swe_bench/` - downloaded benchmark exports
        * `raw/swe_bench/` - raw task snapshots or manual fixtures
        * `raw/repositories/` - raw repo snapshots if preservation is needed
        * `processed/swe_bench/manifests/` - normalized task manifests
        * `processed/swe_bench/splits/` - smoke/core/final evaluation splits
        * `processed/slices/` - reusable slice datasets
        * `processed/constraints/` - reusable symbolic constraint datasets
      * `tests/`
        * `test_dataset_preparation.py`
        * `test_filter_tasks_swebench.py`
        * `test_project_structure.py`
        * future tests:
          * `test_config_loading.py`
          * `test_artifact_logging.py`
          * `test_symbolic_constraints.py`
          * `test_solver_result_parsing.py`
          * `test_feedback_transformation.py`
      * `docs/`
        * `project_structure.md`
        * `experiments.md`
        * `high_low_pipeline.MD`
      * `notebooks/`
        * `01_data_exploration.ipynb`
        * `02_baseline_analysis.ipynb`
        * `03_solver_diagnostics.ipynb`
        * `04_results_visualization.ipynb`
      * `scripts/`
        * `download_swebench.py`
        * `visualize_task.py`
        * `validate_project_structure.py`
        * future shell wrappers:
          * `run_smoke.sh`
          * `run_baseline.sh`
          * `run_symbolic_feedback.sh`
          * `evaluate_run.sh`
   2. Validate the scaffold with:

      ```bash
      python scripts/validate_project_structure.py
      ```

      Add `--check-runs` after real experiment runs exist and should be checked for required run-level files.
   3. Follow [Software Implementation Guide](Software Implementation Guide) until 2. Working on the Frontend or 3. Working on the Backend
   4. Write README + developer documentation
      1. Include:
         * project overview
         * pipeline stages
         * setup instructions
         * how to run:
           * single task
           * benchmark
           * artifact structure
      2. Add:
         * expected outputs
         * common failure cases

##### **1. Data Processing + Task Loading

###### Datastructures

1. RawTask

   * stores the raw task

   ```python
   FAIL_TO_PASS: str # the target regression tests that should initially fail and later pass. repair target tests
   PASS_TO_PASS: str # the non-regression suite. 
   base_commit: str
   created_at: str
   difficulty: str
   environment_setup_commit: str
   hints_text: str
   instance_id: str
   patch: str # gold human code fix
   problem_statement: str # bug report, trace, repro, localization hints
   repo: str
   test_patch: str # gold behavioral spec / regression oracle for offline analysis
   version: str
   ```
2. TaskObject

   * stores the normalized task from the benchmark

   ```python
   @dataclass(frozen=True)
   class TaskObject:
   dataset: str
   dataset_source: str
   split: str
   source_path: str
   instance_id: str
   repo: str
   base_commit: str
   problem_statement: str
   failing_tests: tuple[str, ...]
   passing_tests: tuple[str, ...]
   patch: str | None
   test_patch: str | None # 
   hints_text: str
   difficulty: str | None
   execution_trace: tuple[str, ...]
   constraint_spec: dict[str, Any] | list[Any] | str | None
   raw_fields: dict[str, Any]
   ```
3. CandidateTask

   * used for ranking and selecting logic heavy tasks

   ```python
   @dataclass(frozen=True)
   class CandidateTask:
   raw: TaskObject
   score: int
   changed_lines: int
   changed_files: tuple[str, ...]
   labels: tuple[str, ...]
   logic_heavy: bool
   include_for_smoke: bool
   exclusion_reasons: tuple[str, ...]
   ```

###### Key Components / Deliverables

1. Task Loader
   1. Create a Task Loader Module in `~/dataset/task_loader.py`
      1. Load benchmark entries from:

         * SWE-bench Verified subset
         * optional synthetic HumanEval bug tasks later

         1. Normalize benchmark row
         2. Validate missing_required_fields
         3. Extract raw fields from each task and populate `TaskObject`
            1. Validate required fields before further processing
            2. Skip or log malformed tasks
      2. Score tasks

         1. Score based on patch hits, text hits, negative text hits, negative patch hits, changed line count, changed file list, repo score, repo exclusions, patch size score
         2. Restrict to selected repositories if needed:
            * sympy
            * pandas
            * numpy
            * scikit-learn
            * matplotlib
         3. Apply logic-heavy heuristics:
            * patch modifies conditional logic or comparisons
            * issue text suggests edge cases / wrong logic / assertions
         4. Remove tasks with:
            * dependency changes
            * import fixes
            * config changes
            * large refactors
      3. Create task subsets:

         * smoke tasks
         * final evaluation tasks

##### 2. **Local Bug Localization + Context Extraction**

###### Datastructures

1. LocalizationEvidence

   * Stores the raw signals used to localize

   ```python
   @dataclass(frozen=True)  
   class LocalizationEvidence:  
   traceback_files: tuple[str, ...]  
   traceback_functions: tuple[str, ...]  
   traceback_line_numbers: tuple[int, ...]  
   mentioned_symbols: tuple[str, ...]  
   failing_test_names: tuple[str, ...]  
   mentioned_paths: tuple[str, ...]  
   error_types: tuple[str, ...]
   ```
2. LocalizationCandidate

   * stores one candidate source region with a score

   ```python
   @dataclass(frozen=True)  
   class LocalizationCandidate:  
   file_path: str  
   function_name: str | None  
   class_name: str | None  
   start_line: int | None  
   end_line: int | None  
   score: int  
   evidence: tuple[str, ...]
   ```
3. LocalizedRegion

   * Final chosen region before prompt construction

   ```python
   @dataclass(frozen=True)  
   class LocalizedRegion:  
   primary_file: str  
   primary_function: str | None  
   line_start: int  
   line_end: int  
   source_snippet: str  
   selection_reason: tuple[str, ...]
   ```
4. ContextPackage

   * actual output for the next stage

   ```python
   @dataclass(frozen=True)  
   class ContextPackage:  
   task: TaskObject  
   localized_region: LocalizedRegion  
   failing_test_snippets: tuple[str, ...]  
   helper_snippets: tuple[str, ...]  
   prompt_ready_context: str
   ```

###### Key Components / Deliverables

* LocalContextSelector

  * avoid full repo-wide retrieval unless needed

  1. Read 1 task from `smoke_tasks.jsonl` into `task`
  2. Create main function `def localize_and_extract_context`
     1. Extract the underlying TaskObject:
        * task = candidate_task.raw
     2. Read key fields from TaskObject:
        * task.instance_id
        * task.repo
        * task.problem_statement
        * task.failing_tests
        * task.passing_tests
        * task.base_commit
        * task.source_path
        * task.execution_trace
     3. Build `LocalizationEvidence` with `def build_localization_evidence`
        1. Parse traceback from `problem_statement` with `def extract_traceback_evidence`

           * Write a helper that extracts:
             * file paths
             * line numbers
             * function names
             * exception location

           1. Search for traceback-like patterns, for example:
              1. `File "...", line N, in function_name`
              2. repo-relative file paths like `sympy/simplify/fu.py`
              3. function names like `_TR56`, `_f`
              4. exception class names like `TypeError`, `ZeroDivisionError`
           2. Extract and normalize:
              1. `traceback_files: tuple[str, ...]`
              2. `traceback_line_numbers: tuple[int, ...]`
              3. `traceback_functions: tuple[str, ...]`
              4. `error_types: tuple[str, ...]`
           3. If multiple traceback frames exist:
              1. keep them in order from outermost to innermost
              2. also mark the deepest frame as highest-priority localization evidence
           4. Store these in `LocalizationEvidence`.
           5. If no traceback is present:
              1. return empty tuples, not `None`
           6. Persist optional debug artifact:
              1. `artifacts/tasks/<instance_id>/traceback_evidence.json
        2. Extract Failing and passing Test Names from TaskObject with `def extract_test_evidence`

           1. Read:
              1. `task.failing_tests`
              2. `task.passing_tests`
           2. Normalize test names:
              1. strip whitespace
              2. remove duplicates
              3. preserve original order
           3. Add failing tests into `LocalizationEvidence.failing_test_names`.
           4. Optionally include `passing_tests` only if `include_passing_tests=True`.
        3. Extract issue text hints from `problem_statement` with `extract_issue_text_hints`

           1. Parse `TaskObject.problem_statement` for likely hint tokens:
              1. function names
              2. module names
              3. API names
              4. exception words
              5. symbolic/math expressions
              6. obvious identifiers in backticks or code fences
           2. Extract possible:
              1. symbol names
              2. mentioned file/module substrings
              3. suspicious expressions like `rv.exp < 0`
           3. Add these to:
              1. `LocalizationEvidence.mentioned_symbols`
              2. `LocalizationEvidence.mentioned_paths`
           4. Deduplicate while preserving order.
           5. Persist optional artifact:
              1. `artifacts/tasks/<instance_id>/issue_text_hints.json`
        4. Merge all extracted signals into one `LocalizationEvidence`.
        5. Ensure every field is populated with tuples, never `None`.
        6. Return a fully constructed `LocalizationEvidence`.
  3. Generate localization candidates
  4. If candidate list is empty or weak:
     1. Fallback Local scan

        * If the above are weak, do a small local scan:
          * grep-like symbol search
          * filename match
          * function name match

        1. Only run this if:
           1. traceback evidence is weak or absent
           2. candidate list is empty or low-confidence
        2. Fallback strategies:
           1. Filename match
              1. search for files whose path contains substrings from mentioned_paths
           2. Function name match
              1. grep-like search for symbol definitions matching mentioned_symbols
           3. String search in source
              1. search for suspicious expressions or keywords from issue text
           4. Test-to-source heuristic
              1. if a failing test file is known, infer same module / neighboring source file
           5. Produce LocalizationCandidates with weaker evidence labels like:
              1. "fallback_symbol_search"
              2. "fallback_filename_search"
              3. "fallback_issue_text_match"
  5. Rank candidates by score and evidence strength.
     1. Score candidates using evidence weights:
        1. traceback file match: highest weight
        2. traceback function match: high weight
        3. failing test linkage: medium-high weight
        4. issue text symbol match: medium weight
        5. fallback matches: lower weight
     2. Prefer:
        1. smaller local regions
        2. directly implicated functions
        3. files appearing in traceback
     3. Penalize:
        1. very large files
        2. generic utility modules with weak evidence
     4. Sort descending by score.
     5. Keep:
        1. top-1 for normal pipeline
        2. top-3 for debugging artifacts if desired
     6. Persist ranking artifact:
        1. `artifacts/tasks/<instance_id>/localization_candidates.json`
  6. Select best candidate
  7. Extract `LocalizedRegion`
     1. Extract a small surrounding window
        1. Open `candidate.file_path` from the local repo.
        2. If `candidate.function_name` is known and can be located:
           1. extract the full enclosing function definition
        3. Else if `candidate.start_line` is known:
           1. extract a bounded window around the line:
              1. for example `line - 15` to `line + 15`
        4. If both are available:
           1. prefer enclosing function
           2. fallback to line window if function extraction fails
        5. Store the final snippet in:
           1. `LocalizedRegion.source_snippet`
        6. Also store:
           1. `primary_file`
           2. `primary_function`
           3. `line_start`
           4. `line_end`
           5. `selection_reason`
        7. Persist optional artifact:
           1. `artifacts/tasks/<instance_id>/localized_region.json`
  8. Extract the failing test snippet(s) if available with `def locate_test_snippets`
     1. Traverse likely test files under the repo:
        1. prioritize paths containing:
           1. `tests/`
           2. `test_*.py`
     2. For each failing test name in `task.failing_tests`:
        1. search for definitions like:
           1. `def test_name(...):`
     3. If found:
        1. extract the enclosing test function body
        2. preserve exact source text
     4. Return a tuple of extracted test snippets.
     5. If a failing test cannot be found:
        1. log the missing test name
        2. continue without failing the pipeline
     6. Persist optional artifact:
        1. `artifacts/tasks/<instance_id>/failing_test_snippets.json`
  9. Persist:
     * artifacts/tasks/<instance_id>/context_package.json
     * artifacts/tasks/<instance_id>/prompt_ready_context.txt
  10. Write debug artifacts

##### 3. **Prompt + Neural Proposal**

1. Prompt Builder

   * Role:
     * Construct structured prompts for the LLM using task + context + feedback
   * Input → Output:
     * Input:
       * Task
       * Context
       * optional Critique
       * optional previous Patch
     * Output:
       * Prompt
   * Interaction:
     * Feeds into Neural Patch Generator
     * Updated every iteration

   1. Build `ContextPackage`
      1. Use:
         1. `task.problem_statement`
         2. `localized_region.source_snippet`
         3. `failing_test_snippets`
         4. optional `helper_snippets`
      2. Build `prompt_ready_context` in a stable order:
         1. bug report / problem statement
         2. failing test names
         3. failing test snippet(s)
         4. localized source snippet
         5. optional helper snippet(s)
      3. Keep context minimal:
         1. do not include entire file unless necessary
         2. do not include unrelated passing tests by default
      4. Construct and return ContextPackage
   2. LLM generates candidate patch
2. Neural Patch Generator (LLM Agent)

   * Role:
     * Generate candidate patches using the LLM
   * Input → Output:
     * Input:
       * Prompt
     * Output:
       * Patch
   * Interaction:
     * Feeds into:
       * Patch Applier
       * Impact Slicer
     * Receives feedback via updated prompts

##### 5. **Patch Application**

* apply the candidate patch to an isolated working copy of the repository
* prepare patched code for validation

###### Datastructures

###### **Key Components / Deliverables**

1. Patch Applier
   * Role:
     * Apply candidate patches to a temporary working copy of the repository
   * Input → Output:
     * Input:
       * Patch
       * Task.repo_path
     * Output:
       * patched repository state
   * Interaction:
     * Feeds into:
       * Impact Slicer
       * optional test execution
     * Ensures isolation via per-task workspace

##### 6. **Impact Slicing**

* isolate the patched program region that should be analyzed
* identify relevant variables, predicates, and local conditions

1. Impact Slicer (Post-Patch Localization)
   * Role:
     * Identify the program region affected by the patch for analysis
   * Input → Output:
     * Input:
       * patched code
       * RepoIndex
       * Patch
     * Output:
       * ProgramSlice
   * Interaction:
     * Feeds into Constraint Extractor
     * Reduces symbolic reasoning scope

###### Datastructures

###### **Key Components / Deliverables**

##### 6. **Constraint Extraction**

* convert the sliced patched code into symbolic / logical constraints
* extract:
  * domain assumptions
  * path conditions
  * postconditions / expected behavior

###### Datastructures

###### **Key Components / Deliverables**

1. Constraint Extractor
   * Role:
     * Convert program behavior into a formal symbolic representation
   * Input → Output:
     * Input:
       * ProgramSlice
     * Output:
       * SymbolicProblem
   * Interaction:
     * Feeds into Symbolic Verifier
     * Encodes logic for solver reasoning

##### 7. **Symbolic Verification**

* run the solver on the patched local region
* determine whether there exists a violating input or invalid logical condition

###### Datastructures

###### **Key Components / Deliverables**

1. Symbolic Verifier (Solver Engine)
   * Role:
     * Check whether the patch satisfies logical constraints
   * Input → Output:
     * Input:
       * SymbolicProblem
     * Output:
       * SolverResult (sat / unsat / unknown / timeout)
   * Interaction:
     * If sat → passes to Counterexample Generator
     * If unsat → signals termination

##### 8. **Counterexample Generation**

* if the solver finds a violation, convert it into a concrete failing input or failing logical condition

###### Datastructures

###### **Key Components / Deliverables**

1. Counterexample Generator
   * Role:
     * Convert solver output into a concrete failing input
   * Input → Output:
     * Input:
       * SolverResult
     * Output:
       * Counterexample
   * Interaction:
     * Feeds into Feedback Generator
     * Bridges symbolic → concrete domain

##### 9. **Feedback Transformation**

* convert the symbolic failure into a concise natural-language critique for the LLM

###### Datastructures

###### **Key Components / Deliverables**

1. Feedback Generator (Critique Builder)
   * Role:
     * Translate counterexamples into natural-language critiques
   * Input → Output:
     * Input:
       * Counterexample
     * Output:
       * Critique
   * Interaction:
     * Feeds back into Prompt Builder
     * Drives the CEGF loop

##### 10. **Patch Refinement (CEGF Loop)**

* feed the critique back into the next prompt
* generate a refined patch
* repeat verification and refinement as needed

###### Datastructures

###### **Key Components / Deliverables**

1. Iteration Controller (CEGF Loop Manager)
   * Role:
     * Manage iterative refinement and termination conditions
   * Input → Output:
     * Input:
       * IterationState
       * SolverResult
     * Output:
       * updated IterationState
       * final termination decision
   * Interaction:
     * Coordinates:
       * patch generation
       * symbolic verification
       * feedback loop
     * Enforces:
       * max iterations
       * convergence criteria

##### 11. **Termination**

* stop when:
  * no counterexample is found
  * tests pass and local logic checks succeed
  * iteration budget is exhausted

###### Datastructures

###### **Key Components / Deliverables**

1. Evaluation Engine
   * Role:
     * Measure system performance across tasks and runs
   * Input → Output:
     * Input:
       * FinalResult
       * run artifacts
     * Output:
       * metrics (accuracy, iterations, tokens, runtime)
   * Interaction:
     * Consumes outputs from Iteration Controller
     * Produces results for analysis
