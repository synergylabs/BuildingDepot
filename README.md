# bd-benchmarking-tool

## Installation
```bash
git clone --single-branch -b develop https://github.com/IoT-Expedition/BD-Performance-Test.git
cd BD-Performance-Test
npm install
```

## Configuration
- Open `./config.json`
- Update uri
- Update credentials

## Initializing BuildingDepot
```bash
node run ./testSuites/initialize.json
```

## Creating Sensors
- **_(optional)_** Modify the amount of sensors to create in `./testSuites/createSensors.json`
```bash
node run ./testSuites/createSensors.json
```

## Example
Running a benchmark for time-series APIs for different number of sensors
```bash
node run ./testSuites/post-time-series.json
```

