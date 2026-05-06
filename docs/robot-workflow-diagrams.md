# Robot Workflow And Sensor Control

This document explains how the robot assistant handles commands, how sensors produce data, and how actuators are controlled.

The project stays simple on purpose:
- The robot assistant parses the user command.
- MQTT carries the command or sensor update.
- The simulator or ESP32 applies the change.
- The shared state file and dashboard show the result.

---

## 1. Global Workflow

```mermaid
flowchart LR
    U[User<br/>chat or dashboard] --> A[agent.py]
    A --> P[iot_parser.py<br/>parse text to command]
    P --> C[iot_controller.py]
    C --> M[MQTT broker]

    M --> S[Simulator mode<br/>IoTMQTTSimulatorService]
    M --> H[Hardware mode<br/>ESP32 node]

    S --> ST[iot_state.json<br/>iot_events.json]
    H --> B[iot_hardware_bridge.py]
    B --> ST

    ST --> D[app_complet.py dashboard]
    C --> R[MQTT response]
    R --> A
    A --> U
```

### Simple Explanation
1. The user sends a command such as `turn on the light`.
2. `agent.py` sends the text to `iot_parser.py`.
3. The parser creates a structured command like `turn_on` for device `light`.
4. `iot_controller.py` publishes that command to MQTT.
5. The command is executed by either the Python simulator or the ESP32 node.
6. The new state is published back through MQTT.
7. The state is saved and shown in the dashboard.
8. The robot returns a final message to the user.

---

## 2. Command Control Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent as agent.py
    participant Parser as iot_parser.py
    participant Controller as iot_controller.py
    participant MQTT as MQTT broker
    participant Worker as Simulator or ESP32
    participant Store as iot_state.json

    User->>Agent: "unlock the door"
    Agent->>Parser: parse_iot_command()
    Parser-->>Agent: {action: unlock, device_type: door}
    Agent->>Controller: execute_command()
    Controller->>MQTT: publish robocompagnon/home/commands
    MQTT->>Worker: command payload
    Worker->>Worker: apply action
    Worker->>MQTT: publish device state
    Worker->>MQTT: publish response
    MQTT->>Store: state sync directly or via hardware bridge
    MQTT-->>Controller: response payload
    Controller-->>Agent: success message
    Agent-->>User: "Living Room Front Door unlocked."
```

---

## 3. Robot Control Map

```mermaid
flowchart TD
    RC[Robot assistant] --> LC[Light control]
    RC --> AC[AC control]
    RC --> DC[Door control]
    RC --> SQ[Sensor queries]
    RC --> GS[Gas simulation commands]

    LC --> L1[turn_on]
    LC --> L2[turn_off]
    LC --> L3[set_brightness]

    AC --> A1[turn_on]
    AC --> A2[turn_off]
    AC --> A3[set_temperature]

    DC --> D1[lock]
    DC --> D2[unlock]

    SQ --> S1[temperature]
    SQ --> S2[humidity]
    SQ --> S3[light_level]
    SQ --> S4[gas_ppm]

    GS --> G1[set_gas_state]
    GS --> G2[set_gas_level]
```

---

## 4. Sensor And Actuator Relationships

```mermaid
flowchart TD
    subgraph Inputs
        DHT[DHT22]
        MQ2[MQ-2 gas sensor]
        PIR[PIR occupancy sensor]
        LDR[LDR light sensor]
    end

    subgraph Processing
        SIM[Python simulator<br/>or ESP32 firmware]
        EDGE[Simple edge rules]
    end

    subgraph Outputs
        LIGHT[Light relay or LED]
        AC[AC relay or LED]
        SERVO[Door servo]
        ALERT[Gas alert topic]
    end

    DHT --> SIM
    MQ2 --> SIM
    PIR --> SIM
    LDR --> SIM

    SIM --> EDGE
    SIM --> LIGHT
    SIM --> AC
    SIM --> SERVO

    EDGE --> ALERT
```

---

## 5. Sensor Workflow

```mermaid
flowchart LR
    SR[Sensor reading] --> UP[Publish sensor topic]
    UP --> ST[Update iot_state.json]
    ST --> UI[Dashboard shows value]
    ST --> Q[Robot can answer sensor question]
```

### Sensor Topics In Use
- `robocompagnon/home/rooms/living_room/sensors/temperature`
- `robocompagnon/home/rooms/living_room/sensors/humidity`
- `robocompagnon/home/rooms/living_room/sensors/occupancy`
- `robocompagnon/home/rooms/living_room/sensors/light_level`
- `robocompagnon/home/rooms/living_room/sensors/gas_ppm`
- `robocompagnon/home/alerts/gas`

---

## 6. Temperature And Humidity Sensor

### What It Does
- The DHT22 measures room temperature and humidity on real hardware.
- In simulator mode, `iot_simulator.py` computes these values from room physics.

```mermaid
flowchart TD
    A[DHT22 or simulator state] --> B[temperature and humidity values]
    B --> C[Publish MQTT sensor topics]
    C --> D[Save into living_room sensors]
    D --> E{Robot asked for value?}
    E -- Yes --> F[Return temperature or humidity message]
    E -- No --> G[Dashboard still shows live values]
```

### How The Robot Uses It
- Temperature helps the robot report room conditions.
- Temperature also works with AC control logic.
- Humidity is reported to the user and updated over time.

---

## 7. Light Sensor

### What It Does
- The LDR measures ambient light on hardware.
- In simulator mode, light level is calculated from time of day and light brightness.

```mermaid
flowchart TD
    A[Time of day or LDR reading] --> B[base light level]
    C[Light device state] --> D[brightness boost]
    B --> E[final light_level]
    D --> E
    E --> F[Publish MQTT sensor topic]
    F --> G[Dashboard and robot status]
```

### How The Robot Uses It
- The robot answers `what is the light level?`
- The light actuator changes this sensor indirectly when the light turns on.

---

## 8. Gas Sensor And Alert Rule

### What It Does
- The MQ-2 sensor reads gas concentration in ppm.
- The robot can also simulate gas by command.
- If gas is above `400 ppm`, the system raises an alert.

```mermaid
flowchart TD
    A[MQ-2 reading or gas override command] --> B[gas_ppm updated]
    B --> C[Save sensor value]
    C --> D{gas_ppm > 400?}
    D -- No --> E[No alert]
    D -- Yes --> F[alerts.gas = true]
    F --> G[Publish robocompagnon/home/alerts/gas]
    G --> H[Dashboard alert]
    G --> I[Optional Telegram notifier]
```

### How The Robot Uses It
- The robot answers `what is the gas level?`
- The robot accepts commands such as `turn gas on`, `turn gas off`, and `set gas level to 300 ppm`.

---

## 9. Occupancy Sensor

### What It Does
- The PIR sensor detects motion on hardware.
- In the current simulator, occupancy is stored as a simple boolean.

```mermaid
flowchart TD
    A[PIR output or stored occupancy value] --> B[occupancy sensor state]
    B --> C[Save to room sensors]
    C --> D[Used by temperature simulation]
    D --> E[Small heat gain when room is occupied]
```

### How The Robot Uses It
- Occupancy affects temperature simulation.
- The dashboard displays occupancy status.
- It is not yet a main spoken command feature.

---

## 10. Actuator Control

```mermaid
flowchart LR
    CMD[MQTT command] --> DEV{Target device}
    DEV -->|light| L[GPIO26 relay or LED]
    DEV -->|ac| A[GPIO27 relay or LED]
    DEV -->|door| D[GPIO18 servo]
    L --> LS[Publish light state]
    A --> AS[Publish AC state]
    D --> DS[Publish door state]
```

### Device Details
- Light:
The robot sends ON, OFF, or brightness commands. The light state also affects `light_level`.
- AC:
The robot sends ON, OFF, or target temperature commands. The AC affects `temperature` and `humidity`.
- Door:
The robot sends `lock` or `unlock`. On hardware, the servo moves between lock positions.

---

## 11. Simulator Mode Vs Hardware Mode

```mermaid
flowchart LR
    C[iot_controller.py] --> M[MQTT broker]

    M --> S[Simulator mode]
    S --> S1[apply_command in iot_simulator.py]
    S1 --> S2[save state and publish topics]

    M --> H[Hardware mode]
    H --> H1[ESP32 handles GPIO and sensors]
    H1 --> H2[publish device and sensor topics]
    H2 --> H3[iot_hardware_bridge.py syncs JSON state]
```

### Practical Difference
- Simulator mode:
Python owns both device logic and sensor evolution.
- Hardware mode:
ESP32 owns the real pins and real sensor reads, while Python only syncs and displays the result.

---

## 12. Current Hardware List

- DHT22 on `GPIO4`
- MQ-2 gas sensor on `GPIO34`
- PIR occupancy sensor on `GPIO5`
- LDR on `GPIO35`
- Light output on `GPIO26`
- AC output on `GPIO27`
- Door servo on `GPIO18`

---

## 13. Summary

The robot does not control sensors directly. It controls actuators and reads sensor data through MQTT.

The main behavior is:
1. Parse command.
2. Publish MQTT message.
3. Simulator or ESP32 executes it.
4. Sensor and device state are published back.
5. JSON state and dashboard refresh.
6. The robot answers with a simple result.
