<!-- Thanks for the PR. Please fill this in. -->

## Summary

<!-- One or two sentences. What changes and why. -->

## Type

- [ ] Bug fix
- [ ] New feature
- [ ] Docs / housekeeping
- [ ] Refactor (no behaviour change)

## Test plan

<!-- How did you verify this works? Distro + desktop env + steps. -->

## Checklist

- [ ] One logical change in this PR.
- [ ] `python3 -c "import ast; ast.parse(open('codexbar-tray.py').read())"` succeeds.
- [ ] Tested live with `systemctl --user restart codexbar-tray` and the tray still opens / refreshes.
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`.
- [ ] Any new config knob is documented in the README **Configure** table.
