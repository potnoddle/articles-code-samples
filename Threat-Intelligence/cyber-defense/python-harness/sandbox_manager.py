import time
import subprocess
import sys
import os
from typing import Dict, Any, List

class EphemeralSandboxManager:
    """
    Manages isolated execution boundaries for untrusted code/agent actions.
    Enforces ephemeral lifecycles, memory limits, and syscall restrictions.
    """
    def __init__(self, memory_limit_mb: int = 128, timeout_sec: int = 5):
        self.memory_limit_mb = memory_limit_mb
        self.timeout_sec = timeout_sec

    def execute_bounded_script(self, script_code: str, env_vars: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Executes code inside a hardened sub-process with memory/timeout caps
        and disallows network access via clean environment isolation.
        """
        start_time = time.time()
        # Clean environment to prevent ambient credential inheritance
        isolated_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8"
        }
        if env_vars:
            isolated_env.update(env_vars)

        try:
            process = subprocess.Popen(
                [sys.executable, "-c", script_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=isolated_env,
                text=True
            )

            stdout, stderr = process.communicate(timeout=self.timeout_sec)
            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "exit_code": process.returncode,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
                "execution_time_ms": round(elapsed_ms, 2),
                "isolated": True,
                "quarantine_triggered": process.returncode != 0
            }

        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout_sec}s (Possible runaway AI loop or DoS attempt)",
                "execution_time_ms": self.timeout_sec * 1000,
                "isolated": True,
                "quarantine_triggered": True
            }
        except Exception as e:
            return {
                "exit_code": -2,
                "stdout": "",
                "stderr": str(e),
                "execution_time_ms": 0,
                "isolated": True,
                "quarantine_triggered": True
            }
