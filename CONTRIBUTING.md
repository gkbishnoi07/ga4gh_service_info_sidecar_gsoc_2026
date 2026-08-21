# Contributing

Your contributions are welcome and necessary. Please use the
[GitHub issue tracker](https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/issues) to:

- Report bugs
- Propose or implement features
- Submit code changes / fixes
- Discuss proposed changes

See here for a [short tutorial for GitHub's issue tracking system](https://guides.github.com/features/issues/).

Please adhere to the [Code of Conduct](CODE_OF_CONDUCT.md).

Please *do not* ask usage questions, installation problems (unless they appear to be bugs) etc. via the GitHub issue tracker. Instead, please use the [GitHub Discussions forum](https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/discussions) to ask questions and start conversations.

---

## Reporting bugs

Please use the project's [issue tracker](https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/issues) to report bugs. If you have no experience in filing bug reports, see e.g., [these recommendations by the Mozilla Developer Network](https://developer.mozilla.org/en-US/docs/Mozilla/QA/Bug_writing_guidelines) first. Briefly, it is important that bug reports contain enough detail, background and, if applicable, _minimal_ reproducible sample code. Tell us what you expect to happen, and what actually does happen.

---

## Implementing features and submitting fixes

Kindly use pull requests to submit changes to the code base. But please note that this project is driven by a community that likes to act on consensus. So in your own best interest, before just firing off a pull request after a lot of work, please [open an issue](https://github.com/ga4gh/ga4gh_service_info_sidecar_gsoc_2026/issues) to **discuss your proposed changes first**. Afterwards, please stick to the following simple rules to make sure your pull request will indeed be merged:

1. Major changes to the core `ServiceInfo` data models should be discussed in an issue before implementation.
2. Fork the repo and create a feature branch from branch `main`.
3. If you've added code that should be tested, add tests alongside the source code in `*_test.go` files.
4. Ensure that all tests and quality checks pass locally:
   * `go test ./...` (runs the unit test suite)
   * `go test ./... -count=1` (reruns tests without cached results)
   * `golangci-lint run` (linter check)
   * `go vet ./...` (compilation and sanity checks)
5. Document your code and update all relevant documentation.
6. Stick to the code and documentation style (see below).
7. Issue the pull request.

> [!IMPORTANT]
> Note that all your contributions are understood to be covered by the [same Apache 2.0 license](LICENSE) that covers the entire project.

---

## Code & documentation style

### Go

Please use a recent version of Go 1.22 or higher. Go code, comment and docstring style must follow the standard Go guidelines.

Please run the following validation tools locally and ensure that no warnings or errors are reported before you commit:

- Run `go fmt ./...` to auto-format your Go source files.
- Run `golangci-lint run` to verify code quality, structure, and check style guidelines.
- Run `go vet ./...` to catch common code correctness bugs.