# Changelog

High-level, newest-first. `__version__` (package) and `__catalog_version__`
(data) move in lockstep and are CI-enforced equal (see
`tests/test_catalog_versioning.py`).

<!-- towncrier release notes start -->

## 1.1.0 (2026-10-19)

### Minor

- A material can now be derived from a catalog entry under a new id, inheriting its data without copying and recording every override with a reason.
- Materials can now carry temperature-dependent property tables and plastic flow curves, with a source on every point, plus solidus, liquidus, latent heat of fusion, and stress-relaxation temperature.


## 1.0.0 (2026-10-02)

### Major

- Open Source Launch
