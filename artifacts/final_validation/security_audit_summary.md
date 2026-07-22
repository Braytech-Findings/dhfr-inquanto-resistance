# Security Audit Summary

Maintained tests and a filename/pattern audit found no tracked credential files,
private keys, bearer tokens, token assignments, populated `.env`, hard-coded
Nexus project IDs, or maintained absolute workstation paths. A suppressed-value
email-pattern scan matched only the placeholder package-maintainer field in
`analysis/DESCRIPTION`; matches in `tests/test_quantinuum_recovery.py` were
`@pytest` decorators, not email addresses. None is an account credential. The same
credential-pattern scan across accessible Git history found zero matching
files. Historical scientific JSON contains old absolute local output paths;
these are machine-specific provenance defects, not credentials, and were not
rewritten. Private project/group values remain environment variables. No secret
values were printed or copied into this package. Git-history rewriting is
neither needed nor authorized. The untracked dependency snapshot contains
package names/versions and no obvious credential assignment; it remains
uncommitted pending researcher decision.
