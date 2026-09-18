#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "  Cyber Defense: Zero-Trust Runtime Verification Suite     "
echo "=========================================================="

# 1. Python Harness
echo ""
echo "[1/3] Executing Python 3 Reference Harness..."
if command -v python3 &>/dev/null; then
    (cd "$DIR/python-harness" && python3 run_cyber_defense_tests.py)
elif command -v python &>/dev/null; then
    (cd "$DIR/python-harness" && python run_cyber_defense_tests.py)
else
    echo "  [SKIP] Python not found in PATH."
fi

# 2. .NET 6.0 C# Harness
echo ""
echo "[2/3] Executing C# .NET 6.0 Enterprise Harness..."
if command -v dotnet &>/dev/null; then
    (cd "$DIR/dotnet-harness" && dotnet run -v q)
else
    echo "  [SKIP] dotnet CLI not found in PATH."
fi

# 3. Rust Harness
echo ""
echo "[3/3] Executing Rust 2021 Performance Harness..."
if command -v cargo &>/dev/null; then
    (cd "$DIR/rust-harness" && cargo run --quiet)
else
    echo "  [SKIP] cargo/rustc not found in PATH (Rust code ready in rust-harness/)."
fi

echo ""
echo "[+] Cyber Defense verification run completed successfully."
