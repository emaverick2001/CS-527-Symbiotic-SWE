**Figure: Cost-effectiveness tradeoff on the held-out SymPy final evaluation.**

Each point is one ablation condition from `artifacts/runs/final_eval_gpt_5_3_codex_sympy_real_tests/metrics.json`. The x-axis reports average
LLM tokens per task, the y-axis reports real-test success rate, and bubble size encodes
average wall-clock runtime. In this run, `neural_cegf` increases real-test success from 14.3% to 35.7%, while average token use rises from 16,746.6 to 30,025.9 and average runtime rises from 8.6s to 16.6s. The figure supports the RQ3 conclusion that
counterexample-guided feedback is more effective but not globally more efficient: its
overhead is justified mainly when it recovers tasks that the neural baseline does not solve.
