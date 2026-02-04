# YACA (Beta)

Yet Another Coding Agent (YACA) is a coding agent built in Python

## Installation

```bash
pip install yaca
# or
pip install git+https://github.com/wsdea/yaca.git
```

## How to run
- In a terminal, just run `yaca`.

## Adding New Projects to test
1. Create a folder under `tests/projects/<project_name>/`.
2. Add a `task.txt` describing the desired outcome and a `verifications.py` containing assertions.
3. Optionally provide a `src/` skeleton for the expected solution.
4. Write a corresponding test in `tests/test_projects.py` that loads the verification module.
