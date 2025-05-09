#!/bin/bash
# If you get a "permission denied" error, run: chmod +x start_apps.sh

# Get the absolute path of the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Function to run a command in a new Terminal tab (macOS specific)
run_in_new_tab() {
    local work_dir="$1"
    local cmd_to_run="$2"
    local tab_title="$3"
    
    # Escape for AppleScript string: backslashes and double quotes
    local escaped_cmd_to_run=$(echo "$cmd_to_run" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
    local escaped_work_dir=$(echo "$work_dir" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
    local escaped_tab_title=$(echo "$tab_title" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')

    osascript \
        -e "tell application \"Terminal\"" \
        -e "  if not (exists window 1) then reopen" \
        -e "  activate" \
        -e "  tell application \"System Events\" to keystroke \"t\" using {command down}" \
        -e "  delay 0.5" \
        -e "  set command_to_execute to \"cd \\\"${escaped_work_dir}\\\" && ${escaped_cmd_to_run}\"" \
        -e "  set current_tab to (do script command_to_execute in front window)" \
        -e "  set custom title of current_tab to \"${escaped_tab_title}\"" \
        -e "end tell" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "Failed to open new tab for '$tab_title'. Check Terminal app permissions for script execution if applicable."
        return 1
    fi
    return 0
}

# Check if on macOS
if [[ "$(uname)" == "Darwin" ]]; then
    echo "Detected macOS. Attempting to start services in new Terminal tabs."

    # Start frontend client in a new tab
    CLIENT_DIR_MAC="$SCRIPT_DIR/client"
    CLIENT_CMD_MAC="npm run dev"
    echo "Starting frontend client in a new tab..."
    run_in_new_tab "$CLIENT_DIR_MAC" "$CLIENT_CMD_MAC" "Frontend Client"
    CLIENT_SUCCESS=$?

    # Start backend service in a new tab
    SERVICE_DIR_MAC="$SCRIPT_DIR/service"
    # Command to activate venv and run fastapi
    SERVICE_ACTIVATION_CMD_MAC="if [ -f .venv/bin/activate ]; then echo 'Activating .venv...'; source .venv/bin/activate; elif [ -f venv/bin/activate ]; then echo 'Activating venv...'; source venv/bin/activate; else echo 'No venv found (.venv or venv), proceeding...'; fi"
    SERVICE_RUN_CMD_MAC="fastapi dev main.py"
    FULL_SERVICE_CMD_MAC="${SERVICE_ACTIVATION_CMD_MAC}; ${SERVICE_RUN_CMD_MAC}"
    
    echo "Starting backend service in a new tab..."
    run_in_new_tab "$SERVICE_DIR_MAC" "$FULL_SERVICE_CMD_MAC" "Backend Service"
    SERVICE_SUCCESS=$?

    if [ $CLIENT_SUCCESS -eq 0 ] && [ $SERVICE_SUCCESS -eq 0 ]; then
        echo "Applications are starting in new Terminal tabs."
        echo "To stop the services, close their respective Terminal tabs or use Ctrl+C in them."
    else
        echo "There was an issue starting one or both services in new tabs. Check Terminal output."
    fi
    # The script can exit here as processes are in other tabs.
    exit 0
fi

# Fallback for non-macOS systems (original backgrounding method with improvements)
echo "Not on macOS (or new tab method failed). Starting services in the background of this terminal."

CLIENT_PID=""
SERVICE_PID=""

cleanup() {
    echo "" # Newline after ^C
    echo "Stopping applications..."
    if [ -n "$CLIENT_PID" ]; then
        echo "Stopping client (PID: $CLIENT_PID)..."
        kill "$CLIENT_PID" 2>/dev/null
    fi
    if [ -n "$SERVICE_PID" ]; then
        echo "Stopping service (PID: $SERVICE_PID)..."
        kill "$SERVICE_PID" 2>/dev/null
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start frontend client
echo "Starting frontend client in the background..."
cd "$SCRIPT_DIR/client"
npm run dev &
CLIENT_PID=$!
cd "$SCRIPT_DIR"

# Start backend service
echo "Starting backend service in the background..."
cd "$SCRIPT_DIR/service"
( # Start a subshell for the service command to isolate venv activation
    if [ -f .venv/bin/activate ]; then
        echo "Activating .venv for service..."
        source .venv/bin/activate
    elif [ -f venv/bin/activate ]; then
        echo "Activating venv for service..."
        source venv/bin/activate
    else
        echo "No virtual environment found for service (checked .venv and venv). Attempting to run directly."
    fi
    fastapi dev main.py
) &
SERVICE_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "Frontend client (PID: $CLIENT_PID) and backend service (PID: $SERVICE_PID) are starting."
echo "Client output will be mixed with service output below."
echo "Client available at http://localhost:5173 (or similar)"
echo "Service available at http://localhost:8000 (or similar)"
echo ""
echo "Press [CTRL+C] to stop both applications."

# Wait for background processes to complete
wait
