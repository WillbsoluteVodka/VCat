# Notes: LLM Integration + UI/UX

## Sources

### LLM_INTEGRATION_SPEC.md
- Key points:
  - Introduce LLM module with provider abstraction, config, session, personality, security.
  - Add UI: settings panel, setup wizard, gear icon entry, streaming responses.
  - Store config in llm_config.json with encrypted API keys and multiple providers.
  - Support OpenAI-compatible endpoints (OpenAI/Ollama/LM Studio/vLLM) with streaming.
  - Command system: /help, /new, /memory, /settings (Phase 1).
  - Errors: show blocking errors and force configuration for missing/invalid API.

### Codebase scan
- Key points:
  - Chat dialog uses synchronous ChatHandler with hardcoded commands.
  - No existing LLM module; configs are stored in repo JSON (behavior_config.json).
  - UI uses PyQt with custom-drawn bubbles and glass styling.
  - Settings window exists for behavior and chat entry; uses emoji icons.
  - Chat dialog header currently has close button + emoji title, no settings entry.

## Synthesized Findings

### Integration Requirements
- Replace hardcoded replies with LLM provider when configured.
- Add streaming response plumbing from provider to UI.
- Persist config with encryption and multi-provider switching.
- Implement setup wizard and settings panel in PyQt.

### UI/UX Guidance
- Product guidance: productivity tools favor minimal/flat style with clear hierarchy and micro-interactions.
- Style: glassmorphism works (subtle blur, light borders), AI-native patterns (streaming text, typing indicator).
- Color: productivity palette suggests blue primary with warm CTA (orange) and high contrast text.
- UX: avoid continuous animations; keep easing on transitions; ensure text contrast and explicit error messaging.
