# Proposed Fyron MCP Interface

Status: design only. No MCP server is shipped or enabled by this change.

An MCP adapter could make Fyron's inspected research operations available to AI
clients without duplicating the package's clinical logic. It should be an optional
extra and a thin interface over existing APIs, not a replacement workflow engine.

## First Scope

Start with a local stdio server, synthetic datasets, documentation lookup,
endpoint auditing, join auditing, and explicit statistical operations. Use named
workspace artifacts rather than arbitrary filesystem paths. Return bounded
summaries and artifact handles rather than raw research tables by default.

Keep network extraction disabled initially. A later read-only FHIR interface
should use administrator-configured server aliases, allowed resource types and
search parameters, bounded pages and result sizes, cancellation, and the existing
safe diagnostics. Never accept arbitrary endpoints or executable callbacks from
tool arguments. Do not expose arbitrary Python, SQL, shell commands, or FHIR writes.

## Trust Boundaries

- Credentials stay in server configuration, never in tool arguments or outputs.
- Local stdio avoids a listening port but does not prevent an AI host from sending
  tool results to a remote model. Even counts can disclose sensitive information.
- Apply output policy and authorization on the server. Client approval dialogs and
  tool annotations are not security boundaries. Patient-level access needs a
  separate institution-approved design and explicit permissions.
- Treat FHIR narratives and retrieved documents as untrusted content, never as
  instructions. Do not let their text change tool privileges or destinations.
- A remotely hosted MCP service needs its own authentication and authorization.
  Its access token is not interchangeable with an upstream FHIR token. Do not
  pass through client tokens as upstream credentials.

## Acceptance Before Shipping

Use the official MCP SDK and test protocol compatibility, resource limits,
cancellation and cleanup, path traversal and symlink escape, secret redaction,
untrusted resource content, authorization denial, and output-policy enforcement.
Keep dependencies optional and ensure importing Fyron never starts a server.
Begin with synthetic-only operations and a documented threat model before adding
clinical connectivity.

References: [MCP authorization](https://modelcontextprotocol.io/specification/latest/basic/authorization)
and [MCP security guidance](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices).
