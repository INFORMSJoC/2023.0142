#!/bin/bash

commands=(
    "python3 -m venv .venv"
    "source ./.venv/bin/activate"
    "pip install -r ./scripts/requirements.txt"
)

for command in "${commands[@]}"; do
    echo "Executing command: $command"
    eval "$command"
    if [[ $? -ne 0 ]]; then
        echo "The command '$command' failed"
        exit 1
    fi
done

echo "All commands executed successfully"