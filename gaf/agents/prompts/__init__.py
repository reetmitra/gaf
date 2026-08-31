"""Versioned prompt templates, one file per role and version.

A prompt is data, and its version id is recorded with every call it produces. A change
of wording is therefore a visible event in the audit log rather than silent drift
between runs.

Validation principle: **reliability**.
"""
