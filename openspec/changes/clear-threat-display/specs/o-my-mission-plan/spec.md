## ADDED Requirements

### Requirement: Clear threat weather display and route exposure

The system SHALL render the threat-weather and route-exposure displays defined in the scenarios below, preserving the existing cell-size and hex-versus-square controls and the strict layer order. “Frequency band” SHALL mean only a threat or jammer RF band.

#### Scenario: Continuous solid field on the Plan tab

- **GIVEN** the cost field is toggled on
- **WHEN** the Plan map renders
- **THEN** neighbouring covered cells abut and form readable regional zones with solid opaque fills and no cell strokes
- **AND** routes and task markers remain crisp above the field

#### Scenario: Point-level route exposure in details

- **GIVEN** a selected route in the details drawer
- **WHEN** part of one leg enters threat coverage
- **THEN** only the impacted points and short sub-segments are marked jammed or lethal, while the rest of the leg remains clear
- **AND** selecting or hovering a threat draws only that threat's rings

#### Scenario: Frequency band is separate from exposure

- **GIVEN** a threat affecting a route
- **WHEN** exposure is displayed in a legend, tooltip, table, or side panel
- **THEN** exposure is labelled clear, jammed, or lethal
- **AND** the threat's RF frequency band is shown separately and is not used to mean a task or platform type
