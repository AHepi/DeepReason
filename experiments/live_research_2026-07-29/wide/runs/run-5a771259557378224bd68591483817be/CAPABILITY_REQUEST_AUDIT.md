# Capability Request Audit

Manifest: `5f25d072f10846a9119812cff8df1d80b34742e2cb2e97bcd7b739459205fe87`

Every entry below is reconstructed from typed Capability events and immutable records.

## rfc9110-method-definitions

Proposal: `sha256:6d2eb816256047bad2448ed67fa21f25a18ad13d4dbd17df00147d840d647a3e`  
Origin work: `sha256:73a96253c395c8765b59f0e0014f6f42fec1d0f66eb88ab63c68c916aa7b5ef5`  
Source call sequence: `11`  
Purpose: Fetch the exact definitions of 'safe' and 'idempotent' from RFC 9110 to cite verbatim. The target section defines safe methods as read-only and idempotent methods as repeatable, and states whether safe methods are a subset of idempotent methods.  
Requested URLs: `https://www.rfc-editor.org/rfc/rfc9110#section-9.2`, `https://www.rfc-editor.org/rfc/rfc9110#section-9.2.1`, `https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2`  
Lifecycle: proposed → validated → granted → compiled → dispatched → failed → result_packaged  
Terminal reason: `fetched_material_packaged`

## rfc9110_sec92

Proposal: `sha256:970a3e667d351d2b720202d09d1b5864638489c05f583b9dbbb7c4d78d49ae0a`  
Origin work: `sha256:a80fb39fc8c45a1056d443afbb9c60db7c2cdfcdb7ae807e71e6c9354cc4c60d`  
Source call sequence: `110`  
Purpose: Obtain verbatim definitions of 'safe' and 'idempotent' methods from RFC 9110 §9.2 to confirm the safe ⊂ idempotent hierarchy and the exact definitional language (client-expectation component, side-effect vs. intended-effect framing).  
Requested URLs: `https://www.rfc-editor.org/rfc/rfc9110#section-9.2`  
Lifecycle: proposed → validated → denied  
Terminal reason: `requests_budget_exhausted`

## rfc9110_sec921_safe

Proposal: `sha256:4a407fefc6ae33e2c8f52eeb495c4dbb424586e5af7696f31cb41c8d57bd293d`  
Origin work: `sha256:a80fb39fc8c45a1056d443afbb9c60db7c2cdfcdb7ae807e71e6c9354cc4c60d`  
Source call sequence: `110`  
Purpose: Obtain the verbatim text of RFC 9110 §9.2.1 (Safe Methods) to verify whether the definition includes the client-expectation dimension ('client does not request, and does not expect, any state change') or is purely server-side.  
Requested URLs: `https://www.rfc-editor.org/rfc/rfc9110#section-9.2.1`  
Lifecycle: proposed → validated → denied  
Terminal reason: `requests_budget_exhausted`

