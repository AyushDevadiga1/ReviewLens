# OpenCode — New Project Onboarding Prompt

Use this prompt to bootstrap a new project that follows the same blueprint as
FedLedger (Federated Learning + Blockchain audit trail, or any modular
Python + Node.js project that ships with reference docs).

Execute the steps below in order. **Do not commit, do not `git init`, do not
push anything** — the user reviews the repo size and state first.

---

## 1. Read the reference material first

- Scan the workspace for reference docs (`.md`, `.docx`, skeleton/canvas files
  such as `docs/fedledger_skeleton.md`).
- Extract from them: what the project does, the intended repo layout, the tech
  stack and pinned versions, and what each module is responsible for.

## 2. Propose the module layout, then create it

Confirm the folder layout with the user before writing any file. A good default:

```
data/            data partitioning + private node partitions
fl_nodes/        Flower client node(s)
fl_server/       orchestration server, aggregation, blockchain bridge
blockchain/      smart contract, deploy script, hardhat config, config json
app/             Streamlit dashboard views
tests/           unit test skeletons per module
requirements.txt / package.json / README.md
```

## 3. Create template/stub files only

- Every function: complete docstring (purpose, args, returns) + `pass` body
  with a `TODO:` list describing the exact implementation approach.
- Keep real imports at the top so every file `py_compile`s cleanly.
- Include the module-level structure exactly as described in the reference docs.

## 4. Minimize the tree before writing anything

- Fold near-duplicate scripts into ONE parametrized entry point, e.g. the
  skeleton's `node1.py / node2.py / node3.py` became a single `fl_nodes/node.py`
  launched with `--node 1|2|3` (registry dict `NODE_CONFIG`).
- Drop `__init__.py` unless the test suite needs package imports.
- Keep config placeholders (e.g. `contract_config.json`) but ignore generated
  output/artifacts via `.gitignore` (`*.npy` partitions, `artifacts/`, `node_modules/`,
  virtualenv, tooling folders).

## 5. Root manifests + README policy

- `requirements.txt` with pinned versions from the reference docs.
- `package.json` for the Node/Hardhat side.
- `README.md`: short intro + module table + repo structure ONLY.
- **Do NOT add setup/run instructions or implementation-order docs while the
  project is still un-implemented.** Those get added once work actually starts.

## 6. Environment setup (Python 3.11 venv) + verification

1. Check installed Pythons: `py -0` and `python --version`.
2. Create the venv with the Python version the project TARGETS — not the
   newest available (FedLedger targets 3.11, which also matches the pinned
   numpy/scikit-learn/streamlit era):
   `py -3.11 -m venv .venv`
3. Install: `.venv\Scripts\python.exe -m pip install -r requirements.txt`
4. If pinned deps conflict (known case: `flwr==1.5.0` needs `protobuf<4`,
   `web3>=6.8` needs `protobuf>=4.21.6`), resolve by bumping the independent
   package and keeping the era consistent — `flwr` 1.5.0 → `flwr==1.7.0`
   (protobuf `>=4.25.2,<5`), same NumPyClient / start_numpy_client /
   start_server API. Pull wheel metadata with `pip download --no-deps` to check
   `Requires-Dist` before editing pins. Re-run install until it resolves.
5. Verify the pain points that `py_compile` alone cannot: imports used by the
   skeleton (e.g. `flwr`, `web3`, sklearn, streamlit views) actually import in
   the venv. If any module is intentionally not implemented yet, that's fine —
   do not implement it here.

## 7. Stop point

- Hand the venv + skeleton over to the user.
- Do NOT create commits, branches, or push. Do NOT re-add setup steps to the
  README. The user decides next steps after inspecting the project.