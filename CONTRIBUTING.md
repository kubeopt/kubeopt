# Contributing to KubeOpt

We welcome contributions. Here's how to get started.

## Development Setup

```bash
git clone https://github.com/kubeopt/kubeopt.git
cd kubeopt
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

Run locally:
```bash
LOCAL_DEV=true python main.py
```

Frontend dev server (hot reload):
```bash
cd frontend && npm run dev
```

## Code Style

- Python: Follow existing patterns. No type stubs or docstrings on obvious methods.
- Frontend: TypeScript, functional components, Tailwind CSS.
- No emojis in code or comments.
- Keep changes focused. One PR per feature or fix.

## Pull Requests

1. Fork the repo and create a branch from `main`.
2. Make your changes.
3. Run `python -m pytest` to verify nothing breaks.
4. Open a PR with a clear description of what changed and why.

## Reporting Issues

Open a GitHub issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Cloud provider and cluster size (if relevant)

## Security

Report security vulnerabilities privately to security@kubeopt.com. Do not open public issues for security bugs.
