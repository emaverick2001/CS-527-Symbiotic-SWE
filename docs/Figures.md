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