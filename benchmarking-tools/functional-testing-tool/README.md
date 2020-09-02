# functional-testing-tool

## Installation
```bash
git clone https://github.com/shreyasnagare/functional-testing-tool.git
cd functional-testing-tool
npm install
```

## Configuration
- Open `./config.json`
- Update uri
- Update credentials

## Example Usage
### Running all functional test suites in the ./tests directory recursively
```bash
npm test
```

### Running all functional test suites in a specific directory recursively
```bash
npm test ./tests/OAuth
```

### Running a specific functional test suite
```bash
npm test ./tests/all.js
```
