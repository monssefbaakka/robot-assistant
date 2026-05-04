# CLAUDE.md

## Project Context

This project is a LOW to INTERMEDIATE complexity IoT robot / smart home system.

Main features:
- Control lights (ON/OFF)
- Control AC (ON/OFF + temperature)
- Detect gas leaks
- Check device status (lights, door)
- Lock/unlock doors (real or simulated)
- Communicate using MQTT
- Use simple edge computing logic

⚠️ This is NOT a production system. It must stay simple, realistic, and buildable with basic components.

---

## 🚫 Main Rule (CRITICAL)

DO NOT OVERENGINEER.

Avoid:
- Microservices
- Complex cloud systems
- Advanced architectures
- Unnecessary abstractions
- Heavy frameworks

Prefer:
- Simple structure
- Clear logic
- Minimal dependencies
- Fast implementation

---

## 🧠 Workflow (MANDATORY BEFORE ANY TASK)

1. Read AGENTS.md
2. Read `/docs/` files
3. Understand current system
4. Identify the task clearly
5. Determine impacted parts:
   - Firmware (ESP32)
   - MQTT communication
   - Backend (if exists)
   - Dashboard (if exists)
   - Documentation
6. Write a SHORT plan (mentally or in comments)
7. Then implement

---

## 📚 Documentation Rule (MANDATORY)

Every completed task MUST be documented.

Location:
```

/docs/task-log.md

````

Each task must include:
- What was built
- Why it was built
- How it works (simple explanation)
- Files modified
- MQTT topics used
- Hardware used (if any)
- How to test
- Limitations

⚠️ No task is complete without documentation.

---

## 📄 Task Documentation Template

```markdown
## Task: [Task Name]

### Status
Completed

### Goal
[Explain objective]

### What Was Implemented
[Explain what was added]

### How It Works
[Step-by-step simple explanation]

### Files Changed
- path/to/file
- path/to/file

### MQTT Topics
- topic/name

### Hardware Involved
- Component name

### How To Test
1. Step 1
2. Step 2
3. Expected result

### Notes / Limitations
[Any simplifications or simulations]
````

---

## 💾 Commit Rules

Before commit:

* Feature works
* Code runs
* Documentation updated
* No secrets included

Commit format:

```
feat: add light control via MQTT
fix: correct gas detection logic
docs: update task log for AC control
refactor: simplify MQTT topics
test: add basic device simulation
```

🚫 Forbidden:

* "update"
* "fix stuff"
* "final"
* unclear messages

---

## 🚀 Push Rules

Push ONLY if:

* Task is complete
* Docs updated
* Code tested
* No secrets

---

## 📁 Project Structure

```
iot-robot/
│
├── firmware/
│   └── esp32/
│
├── backend/ (optional)
│
├── dashboard/ (optional)
│
├── docs/
│   ├── architecture.md
│   ├── mqtt-topics.md
│   ├── hardware.md
│   ├── edge-computing.md
│   └── task-log.md
│
├── diagrams/
│
└── AGENTS.md
```

⚠️ Keep structure SIMPLE.

---

## 📡 MQTT Rules

Topic format:

```
home/{device}/{action}
home/{device}/status
home/{sensor}/data
home/alerts/{type}
```

Examples:

```
home/light/set
home/light/status
home/ac/set
home/ac/status
home/temperature/data
home/gas/status
home/door/set
home/door/status
home/alerts/gas
```

⚠️ Every new topic MUST be added to:

```
/docs/mqtt-topics.md
```

---

## 🧠 Edge Computing Rules

Decisions should be LOCAL when possible.

Examples:

```
IF temperature > threshold → AC ON
IF temperature < threshold → AC OFF
IF gas detected → alert immediately
IF motion detected → update status
```

⚠️ Keep logic SIMPLE (no AI, no prediction models).

---

## 🔌 Hardware Documentation Rule

Every component must be documented in:

```
/docs/hardware.md
```

Format:

```markdown
## Component Name

### Purpose
What it does

### Pins
- VCC →
- GND →
- DATA →

### Used For
Explain usage
```

---

## 🧪 Simulation Rule

Allowed if hardware not available.

Examples:

* Door → LED
* AC → Relay or LED
* Gas → Buzzer
* Light → LED

⚠️ MUST be mentioned in documentation.

---

## 🧹 Code Rules

Code must be:

* Simple
* Readable
* Minimal
* Well-named

Avoid:

* Long functions
* Complex patterns
* Dead code
* Over-splitting files

---

## 🔐 Security Rules

NEVER commit:

* WiFi credentials
* MQTT credentials
* API keys

Use:

```
.env.example
config.example.h
```

---

## 🧪 Testing Rule

Each feature must include a test:

Example:

```markdown
### Test Light Control

1. Start MQTT broker
2. Send "ON" → home/light/set
3. LED turns ON
4. Status published → home/light/status
```

---

## ✅ Definition of Done

A task is DONE only if:

* Code works
* Feature tested
* Docs updated
* MQTT topics documented
* Hardware documented (if any)
* Clean commit created

---

## ⚠️ Final Rule

This project must remain:

* Simple
* Clear
* Realistic
* Demo-ready

If something feels complex → simplify it.

```

---

If you want next level:
👉 I can generate all `/docs/*.md` files ready too (architecture, MQTT, hardware) so your repo is **100% setup in 2 minutes**.
```
