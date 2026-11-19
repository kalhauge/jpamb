# Project information

Explanations and design notes for the project belong here.

- [Dynamic analyzer](../solutions/dynamic/README.md): fuzzer flags, combined results,
  deterministic seeds, interpreter support, and experimental corrected scoring.
- [Branch refinement](branch_refinement.md): current implementation, paired scores,
  interpreter validation, and reproducible evaluation commands.
- [Why analysis scores can be similar](score_similarity.md): pre-refinement results,
  reasons for similar predictions, and proposed Java examples to test differences.
- [How the analyzer is implemented](static_analysis.md): the domain and array
  explanations moved from the static solution README, including limitations.

The [static solution README](../solutions/static/README.md) retains installation,
execution, report-generation, and test commands. The original JPAMB guides remain
in [docs](../docs). Generated reports and logs remain separate from documentation.

See the [project README](../README.md) for the current research direction and
commands. Historical scores in the notes describe their stated configurations;
they should not be treated as current results for every analyzer.
