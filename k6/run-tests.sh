#!/bin/bash
# Helper script to run k6 load tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
BASE_URL="${BASE_URL:-http://localhost:8050}"
SCENARIO="${1:-smoke}"

echo -e "${GREEN}Running k6 load test: ${SCENARIO}${NC}"
echo -e "${YELLOW}Base URL: ${BASE_URL}${NC}"
echo ""

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo -e "${RED}Error: k6 is not installed${NC}"
    echo "Please install k6 from https://k6.io/docs/getting-started/installation/"
    exit 1
fi

# Check if scenario file exists
SCENARIO_FILE="scenarios/${SCENARIO}.js"
if [ ! -f "$SCENARIO_FILE" ]; then
    echo -e "${RED}Error: Scenario file not found: ${SCENARIO_FILE}${NC}"
    echo "Available scenarios: smoke, load, stress, spike, e2e"
    exit 1
fi

# Run the test
export BASE_URL
k6 run --env BASE_URL="$BASE_URL" "$SCENARIO_FILE"

echo -e "${GREEN}Test completed!${NC}"


