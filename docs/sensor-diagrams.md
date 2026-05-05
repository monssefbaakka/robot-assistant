# Sensor Feature Diagrams

Mermaid diagrams for all implemented sensor features (Phase 1 + Phase 2).

---

## 1. Gas Detection

### Query Flow ("what is the gas level?")

```mermaid
sequenceDiagram
    participant User
    participant Agent as agent.py
    participant Parser as iot_parser.py
    participant Controller as iot_controller.py
    participant Simulator as iot_simulator.py
    participant Store as iot_state.json

    User->>Agent: "what is the gas level?"
    Agent->>Controller: try_handle_text()
    Controller->>Parser: parse_iot_command()
    Parser-->>Controller: {action: get_sensor, sensor_type: gas_ppm}
    Controller->>Simulator: apply_command()
    Simulator->>Store: load_state()
    Store-->>Simulator: gas_ppm = 120
    Simulator-->>Controller: {ok: true, message: "Gas level is 120 ppm."}
    Controller-->>Agent: result message
    Agent-->>User: "Gas level in the living room is 120 ppm."
```

### Edge Alert Flow (automatic, threshold-triggered)

```mermaid
flowchart TD
    A[Any MQTT command received] --> B[apply_command called]
    B --> C[advance_state runs]
    C --> D{gas_ppm > 400?}
    D -- No --> E[alerts.gas stays false]
    D -- Yes --> F[alerts.gas = True]
    F --> G[save_state to iot_state.json]
    G --> H{alerts.gas == True?}
    H -- Yes --> I[Publish to robocompagnon/home/alerts/gas]
    I --> J[payload: alert=true, message=Gas leak detected!]
    J --> K[Phase 5: Telegram notification]
    H -- No --> L[Continue normal flow]
```

---

## 2. Temperature Sensor

### Query Flow ("what is the temperature?")

```mermaid
sequenceDiagram
    participant User
    participant Agent as agent.py
    participant Controller as iot_controller.py
    participant Simulator as iot_simulator.py
    participant Store as iot_state.json

    User->>Agent: "what is the temperature?"
    Agent->>Controller: try_handle_text()
    Controller->>Simulator: apply_command()
    Simulator->>Store: load_state()
    Simulator->>Simulator: advance_state() — run physics
    Store-->>Simulator: temperature = 27.1
    Simulator-->>Controller: {ok: true, value: 27.1, unit: C}
    Controller-->>Agent: result
    Agent-->>User: "The current temperature in the living room is 27.1C."
```

### Physics Simulation (advance_state)

```mermaid
flowchart TD
    A[advance_state called] --> B[Compute elapsed seconds since last_update]
    B --> C[Split into 30-second steps]
    C --> D[For each step]

    D --> E[outside_drift = outside_temp - room_temp × 0.02 × 1-insulation × Δmin]
    D --> F[occupancy_heat = 0.03 × Δmin if occupied]
    D --> G{8h ≤ hour < 18h?}
    G -- Yes --> H[solar_gain = 0.05 × sun_exposure × Δmin]
    G -- No --> I[solar_gain = 0]

    D --> J{AC state == on?}
    J -- Yes --> K[ac_cooling = min 0.22×Δmin, temp-target]
    J -- No --> L[ac_cooling = 0]

    E & F & H & I & K & L --> M[new_temp = temp + drift + heat + solar - cooling]
    M --> N[Clamp to 16°C–35°C]
    N --> O[Save sensors.temperature]
```

---

## 3. Humidity Sensor

### Query Flow ("what is the humidity?")

```mermaid
sequenceDiagram
    participant User
    participant Agent as agent.py
    participant Controller as iot_controller.py
    participant Simulator as iot_simulator.py
    participant Store as iot_state.json

    User->>Agent: "what is the humidity?"
    Agent->>Controller: try_handle_text()
    Controller->>Simulator: apply_command()
    Simulator->>Store: load_state()
    Simulator->>Simulator: advance_state()
    Store-->>Simulator: humidity = 48
    Simulator-->>Controller: {ok: true, value: 48, unit: %}
    Controller-->>Agent: result
    Agent-->>User: "The current humidity in the living room is 48%."
```

### Humidity Physics

```mermaid
flowchart TD
    A[Per simulation step] --> B[humidity_drift = outside_humidity - room_humidity × 0.01 × Δmin]
    B --> C{AC state == on?}
    C -- Yes --> D[humidity -= 0.08 × Δmin — dehumidification]
    C -- No --> E[no dehumidification]
    D & E --> F[Apply humidity_drift]
    F --> G[Clamp to 25%–75%]
    G --> H[Save sensors.humidity]
```

---

## 4. Light Level Sensor

### Query Flow ("what is the light level?")

```mermaid
sequenceDiagram
    participant User
    participant Agent as agent.py
    participant Controller as iot_controller.py
    participant Simulator as iot_simulator.py
    participant Store as iot_state.json

    User->>Agent: "what is the light level?"
    Agent->>Controller: try_handle_text()
    Controller->>Simulator: apply_command()
    Simulator->>Store: load_state()
    Simulator->>Simulator: advance_state() — compute lux
    Simulator-->>Controller: {ok: true, value: 650, unit: lux}
    Controller-->>Agent: result
    Agent-->>User: "The current light level in the living room is 650 lux."
```

### Light Level Computation

```mermaid
flowchart TD
    A[Per simulation step] --> B[Get current hour]
    B --> C{Hour range?}
    C -- 7–9h --> D[daylight = 420 lux]
    C -- 10–15h --> E[daylight = 650 lux]
    C -- 16–18h --> F[daylight = 360 lux]
    C -- 19–21h --> G[daylight = 140 lux]
    C -- night --> H[daylight = 40 lux]

    D & E & F & G & H --> I{light_main state == on?}
    I -- Yes --> J[light_boost = 4.5 × brightness]
    I -- No --> K[light_boost = 0]

    J & K --> L[light_level = daylight + light_boost]
    L --> M[Save sensors.light_level]
```

---

## 5. Occupancy Sensor

### Query via State

```mermaid
flowchart TD
    A[sensors.occupancy in iot_state.json] --> B{Value?}
    B -- true --> C[Room is occupied — adds heat in simulation]
    B -- false --> D[Room is empty — no occupancy heat gain]
    C --> E[occupancy_heat = 0.03 × Δmin per step]
    D --> F[occupancy_heat = 0]
```

> **Note:** Occupancy is a static boolean set manually in `iot_state.json`. Auto-detection via HC-SR501 PIR sensor is planned for real hardware (GPIO5). No NL query command implemented yet.

---

## Summary: Sensor → MQTT Topic Map

```mermaid
flowchart LR
    subgraph Sensors
        T[temperature]
        H[humidity]
        L[light_level]
        G[gas_ppm]
        O[occupancy]
    end

    subgraph MQTT Topics
        ST[rooms/living_room/sensors/temperature]
        SH[rooms/living_room/sensors/humidity]
        SL[rooms/living_room/sensors/light_level]
        AG[alerts/gas]
        SN[home/snapshot]
    end

    T --> ST
    H --> SH
    L --> SL
    G -->|ppm > 400| AG
    T & H & L & G & O --> SN
```
