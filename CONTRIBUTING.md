# Contributing to KubeOpt

We welcome contributions. Please read this entire document before submitting a PR.

## Rules

1. **All changes go through PRs.** No direct pushes to main. No exceptions.
2. **One PR per change.** Don't bundle unrelated fixes. Keep PRs small and focused.
3. **No secrets, credentials, or API keys.** Ever. Not in code, comments, tests, or docs. PRs containing secrets will be rejected immediately.
4. **No new dependencies without discussion.** Open an issue first if you need to add a package.
5. **No breaking changes without an issue.** If your change alters API behavior, database schema, or configuration format, discuss it in an issue first.
6. **Tests must pass.** If you break existing tests, fix them in the same PR.

## Branch Naming

Use descriptive branch names:

```
fix/issue-number-short-description
feat/short-description
docs/what-changed
```

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

- Python: Follow existing patterns. No unnecessary abstractions.
- Frontend: TypeScript, functional components, Tailwind CSS.
- No emojis in code, comments, or commit messages.
- No AI-generated boilerplate comments or docstrings.
- Keep changes minimal. Don't refactor code you didn't need to touch.

## Commit Messages

Write clear, concise commit messages:

```
fix: correct HPA threshold calculation for multi-container pods
feat: add GKE autopilot cluster support
docs: update AWS setup guide with IAM role instructions
```

Prefix with `fix:`, `feat:`, `docs:`, `refactor:`, or `test:`.

Do not include `Co-Authored-By` lines or AI tool attributions.

## Pull Request Process

1. Fork the repo and create a branch from `main`.
2. Make your changes.
3. Run `python -m pytest` to verify tests pass.
4. Verify syntax: `python -c "import py_compile; py_compile.compile('your_file.py', doraise=True)"`
5. Open a PR using the template. Fill in all sections.
6. Wait for review. Address all feedback before requesting re-review.
7. A maintainer will merge once approved.

## What We Will Not Accept

- PRs that add complexity without clear value
- Large refactors without prior discussion
- Changes to security-sensitive files (auth, license validation) without thorough justification
- PRs with failing tests
- PRs that introduce hardcoded values where configuration exists
- PRs with AI-generated filler (unnecessary comments, verbose docstrings, type annotations on obvious code)

## Security Vulnerabilities

Report security issues privately to support@kubeopt.com. Do not open public issues for security bugs. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
