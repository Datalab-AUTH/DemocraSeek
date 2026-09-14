---
title: "Frontend and user experience"
doc_type: explanation
layer: architecture
audience: "frontend developer or product reviewer"
reader_goal: "understand the UI lifecycle and evidence presentation"
reader_state: "knows the product workflow"
source_of_truth: true
status: stable
canonical_sources:
  - "frontend/src/App.tsx"
  - "frontend/src/api/client.ts"
  - "frontend/src/components"
related_docs:
  - "docs/reference/api-contracts.md"
  - "docs/architecture/evidence-citations-and-figures.md"
rag_index: true
---

# Frontend and user experience

## Technology

- React 18;
- TypeScript 5.7;
- Vite 8;
- native `fetch`;
- one main stylesheet with CSS custom properties;
- nginx static serving and API proxy.

No onboarding question wording is hard-coded in the frontend.

## Lifecycle

1. `App.tsx` fetches onboarding configuration and corpus status in the background.
2. `Welcome.tsx` introduces the product at the start of a browser session.
3. `Start your conversation` reveals chat for a valid local profile or onboarding
   when no valid profile exists.
4. `useProfile` loads four codes and policy version from local storage.
5. `useOnboardingLocale` loads the persistent, non-identifying interface locale;
   the existing storage-key name is retained for backward compatibility and
   English is the validated default.
6. `UiProvider` localises the complete application shell, while
   `Onboarding.tsx` renders its four localised policy steps from backend
   configuration.
7. Previous selections remain visible as a compact summary while the user moves
   through later steps.
8. `ChatPanel.tsx` owns current in-memory conversation and request state.
9. `AnswerMessage.tsx` renders safe answer text and interactive markers.
10. `SourceDrawer.tsx` provides evidence, page context, image, and original file.
11. `Footer.tsx` renders the reviewed INNOVADE and EU funding marks plus legal
   copy across application states.
12. A new conversation clears chat context; reset profile also removes stored
   preference codes.

The welcome acknowledgement is stored in `sessionStorage`, so it is shown once
per browser-tab session. The interface locale is stored under
`democraseek.onboarding-locale.v1`; the five-string profile remains under
`democraseek.profile.v2`. Neither value is sent as identity data, and there is
no account, cookie, or user tracking.

## Data shown to non-technical users

The main chat interface prioritizes:

- the user's question;
- a readable answer;
- simple source labels;
- a clear "view source" action;
- progress, empty, failure, and insufficient-evidence states.

Technical fields such as raw chunk IDs, vector scores, and provider names are
not placed in the normal reader flow. They remain available in API responses,
logs, and documentation for operators.

## Citation drawer

The drawer separates:

- **Evidence:** the verified excerpt or derived figure description;
- **Page context:** surrounding cleaned page text;
- **Visual source:** figure preview when present;
- **Original source:** document and page access.

This prevents a long metadata block from overwhelming the answer while keeping
verification one action away.

## Scroll behavior and accessibility

The conversation area is independently scrollable while the composer remains
available. The responsive header condenses its controls on narrow screens and
the footer remains outside the main content region. Visual scrollbars can be
hidden in onboarding without disabling keyboard/wheel scrolling. Controls use
semantic buttons, visible focus states, labels, and light/dark theme support.
