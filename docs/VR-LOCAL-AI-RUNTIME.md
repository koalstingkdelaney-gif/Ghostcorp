# VR local AI runtime

## What is implemented

The existing VR site now links to a separate `vr/chat.html` page. It uses a
dedicated Web Worker and a pinned WebLLM runtime to load
`SmolLM2-360M-Instruct-q4f32_1-MLC` after the user explicitly chooses
Initialize. The model is approximately 580 MB estimated VRAM in the WebLLM
model catalogue. It is a small starter model, not a frontier model.

The browser checks HTTPS and WebGPU before enabling initialization. Model
download progress is visible. Chat prompts are processed by the local
WebGPU runtime; there is no cloud fallback, paid API call, company database
access, or external tool execution in this page. Chat history is not persisted
by the page.

## Local research worker

After the backend is deployed and owner GitHub OAuth is configured, the owner
can provision a researcher agent and start a browser worker from the chat
page. It can claim only tasks assigned to that agent while the lifecycle mode
is WORKING, generate a bounded `research_summary` locally, and submit the
result through owner-authenticated task completion endpoints.

The worker:
- Runs only while the chat page and headset/browser remain active.
- Stops and moves the agent to SLEEPING when the owner stops it.
- Does not process arbitrary task types.
- Has no web search, outbound messaging, purchasing, publishing or deployment
  tools.
- Saves results to the private Action Center for review.

## Not implemented / not verified

- No actual Quest 3 hardware run, WebGPU model load, frame-rate or thermal test
  has been completed.
- Model availability does not guarantee the Quest browser can allocate enough
  memory. The estimated model VRAM is not a full memory budget.
- This is a small local assistant; it is not sentient and does not self-train.
- The local worker is not a background service. Closing or suspending the
  browser stops compute; a leased task will need to expire/retry.
- The existing wake/sleep/dream state machine now supports a manually triggered
  bounded dream session in the browser: SLEEPING -> DREAMING -> WAKING ->
  WORKING, with a reviewable proposal submitted to the owner queue. It is not
  an autonomous dream scheduler. There is no isolated dream-code execution
  runtime or automatic self-modification.
- The chat page is a separate VR page linked from the world; a persistent
  in-world floating chat panel is not yet implemented.
- The browser worker cannot browse the live web. Research results must label
  hypotheses and cannot invent competitor evidence.

## Hardware test checklist

On Quest 3, verify secure context, `navigator.gpu`, adapter availability,
model download/cache, successful short prompt, repeated prompts, headset
thermal behavior, browser memory stability, immersive WebXR coexistence,
controller operation, tab suspend/recovery, and task lease retry. Do not mark
the model runtime operational until these tests are completed on the actual
headset.
