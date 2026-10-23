# Reception Content Distinctness Update

The Reception Catering page was rewritten to remove the human-perceived template similarity with the Wedding Catering page.

## Verification
- Wedding vs Reception text similarity: 5.51%
- Wedding vs Reception text difference: 94.49%
- Normalized heading overlap: 3.31%
- Normalized heading difference: 96.69%
- Strict business-critical rule: PASS
- Full website uniqueness rule (>=50% difference): 1,262/1,262 pages PASS
- Local media audit: 0 broken local-media references

## Business-critical strict rule
In addition to the original site-wide requirement, key business pages are now checked using:
- phrase-level text similarity <= 35%
- normalized heading overlap <= 20%

The script is available at:
`tools/audit_business_page_distinctness.py`
