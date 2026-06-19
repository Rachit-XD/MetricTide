"""Application ports: abstractions for external services the use cases depend on.

Distinct from ``domain/repositories`` (persistence ports): these describe
gateways to third-party systems such as Reddit. Implementations live in the
infrastructure layer.
"""
