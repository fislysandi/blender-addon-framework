# Addon Documentation

Document what/why/how for this addon.

## Roadmap

- Investigate an alternative green-screen strategy using a VSE Adjustment Strip with compositor effects applied to the adjustment layer.
- Early observation: this approach appears to cause much less lag than applying heavy compositor logic directly to source strips.
- Current status: promising performance, but there are unresolved behavior issues that still need debugging before production use.
- Next step: prototype the adjustment-strip pipeline, document failure cases, and compare quality/performance against the current non-green-character fast path.
