# Lifecycle Monitor

A Home Assistant custom integration for tracking lifecycle events of devices and consumables — battery replacements, maintenance intervals, and fixed deadlines.

## Features

Three device types, each with dedicated sensors, binary sensors, and controls:

### Virtual Battery

Tracks a simulated battery charge level that decreases over time based on a configurable lifespan.

- **Sensor** — battery percentage (0–100%)
- **Binary sensor** — low battery warning (configurable threshold in days)
- **Button** — reset battery to 100%
- **Datetime** — last replacement date
- **Service** — `lifecycle_monitor.reset_battery`

### Maintenance Interval

Tracks days remaining until a repetitive task is due (e.g., water filter replacement every 90 days).

- **Sensor** — days remaining
- **Binary sensors** — warning (approaching) and overdue
- **Button** — mark maintenance as done (resets the timer)
- **Datetime** — last performed date
- **Service** — `lifecycle_monitor.mark_as_done`

### Fixed Date

Tracks days remaining until a specific deadline (e.g., insurance expiry).

- **Sensor** — days remaining
- **Binary sensors** — warning (approaching) and overdue
- **Datetime** — end date (editable)

## Attach to device

Each monitored item can operate standalone or be attached to an existing HA device. When attached, all entities appear under that device's card in the UI.

## Installation

### HACS (recommended)

Add this repository as a custom repository in HACS, then install "Lifecycle Monitor".

### Manual

Copy the `custom_components/lifecycle_monitor/` directory to your `<config>/custom_components/` and restart Home Assistant.

## Configuration

Go to **Settings > Devices & Services > Add Integration** and search for "Lifecycle Monitor".
