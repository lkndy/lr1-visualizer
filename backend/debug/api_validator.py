"""API request/response validator with comprehensive logging and debugging."""

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from debug.logger import get_logger

logger = get_logger(__name__)


class APIValidator:
    """Validates API requests and responses with detailed logging."""

    def __init__(self, log_dir: str = "logs"):
        """Initialize validator with logging directory."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.request_logs: List[Dict[str, Any]] = []
        self.max_logs = 1000  # Keep last 1000 requests

    def generate_request_id(self) -> str:
        """Generate unique request ID for tracing."""
        return str(uuid.uuid4())[:8]

    def log_request(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Log incoming API request with full details."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "method": method,
            "endpoint": endpoint,
            "data": data,
            "headers": headers,
            "data_size": len(json.dumps(data or {})) if data else 0,
        }

        self.request_logs.append(log_entry)
        if len(self.request_logs) > self.max_logs:
            self.request_logs.pop(0)

        # Console logging with colors
        logger.info(f"🌐 [REQ-{request_id}] {method} {endpoint}")
        if data:
            logger.debug(f"📦 [REQ-{request_id}] Data: {json.dumps(data, indent=2)}")
        if headers:
            logger.debug(f"📋 [REQ-{request_id}] Headers: {headers}")

    def log_response(
        self,
        request_id: str,
        status_code: int,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0,
        error: Optional[str] = None,
    ) -> None:
        """Log API response with validation results."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "status_code": status_code,
            "data": data,
            "duration_ms": duration_ms,
            "error": error,
            "data_size": len(json.dumps(data or {})) if data else 0,
        }

        # Find corresponding request log
        for req_log in reversed(self.request_logs):
            if req_log.get("request_id") == request_id and req_log.get("type") == "request":
                req_log["response"] = log_entry
                break

        # Console logging with colors
        emoji = "✅" if 200 <= status_code < 300 else "❌" if status_code >= 400 else "⚠️"
        logger.info(f"{emoji} [RESP-{request_id}] {status_code} ({duration_ms:.1f}ms)")

        if error:
            logger.error(f"💥 [RESP-{request_id}] Error: {error}")
        elif data:
            logger.debug(f"📦 [RESP-{request_id}] Data: {json.dumps(data, indent=2)}")

    def validate_grammar_request(self, data: Dict[str, Any]) -> List[str]:
        """Validate grammar validation request structure."""
        errors = []

        if not isinstance(data, dict):
            errors.append("Request data must be a dictionary")
            return errors

        if "grammar_text" not in data:
            errors.append("Missing required field: grammar_text")
        elif not isinstance(data["grammar_text"], str):
            errors.append("grammar_text must be a string")
        elif not data["grammar_text"].strip():
            errors.append("grammar_text cannot be empty")

        if "start_symbol" in data and not isinstance(data["start_symbol"], str):
            errors.append("start_symbol must be a string")

        return errors

    def validate_parsing_request(self, data: Dict[str, Any]) -> List[str]:
        """Validate parsing request structure."""
        errors = []

        if not isinstance(data, dict):
            errors.append("Request data must be a dictionary")
            return errors

        required_fields = ["grammar_text", "input_string"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(data[field], str):
                errors.append(f"{field} must be a string")
            elif not data[field].strip():
                errors.append(f"{field} cannot be empty")

        if "start_symbol" in data and not isinstance(data["start_symbol"], str):
            errors.append("start_symbol must be a string")

        return errors

    def validate_grammar_response(self, data: Dict[str, Any]) -> List[str]:
        """Validate grammar validation response structure."""
        errors = []

        if not isinstance(data, dict):
            errors.append("Response data must be a dictionary")
            return errors

        required_fields = ["valid", "errors"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "valid" in data and not isinstance(data["valid"], bool):
            errors.append("valid must be a boolean")

        if "errors" in data and not isinstance(data["errors"], list):
            errors.append("errors must be a list")

        if "grammar_info" in data and data["grammar_info"] is not None:
            grammar_info = data["grammar_info"]
            if not isinstance(grammar_info, dict):
                errors.append("grammar_info must be a dictionary")
            else:
                # Validate parsing table preview if present
                if "parsing_table_preview" in grammar_info:
                    preview = grammar_info["parsing_table_preview"]
                    if not isinstance(preview, dict):
                        errors.append("parsing_table_preview must be a dictionary")
                    else:
                        table_errors = self._validate_table_structure(preview, "parsing_table_preview")
                        errors.extend(table_errors)

        return errors

    def validate_parsing_response(self, data: Dict[str, Any]) -> List[str]:
        """Validate parsing response structure."""
        errors = []

        if not isinstance(data, dict):
            errors.append("Response data must be a dictionary")
            return errors

        required_fields = ["valid", "steps", "total_steps", "success"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "steps" in data and isinstance(data["steps"], list):
            for i, step in enumerate(data["steps"]):
                step_errors = self._validate_derivation_step(step, f"steps[{i}]")
                errors.extend(step_errors)

        return errors

    def _validate_table_structure(self, table_data: Dict[str, Any], prefix: str) -> List[str]:
        """Validate parsing table structure."""
        errors = []

        for table_type in ["action_table", "goto_table"]:
            if table_type not in table_data:
                continue

            table = table_data[table_type]
            if not isinstance(table, dict):
                errors.append(f"{prefix}.{table_type} must be a dictionary")
                continue

            if "headers" not in table:
                errors.append(f"{prefix}.{table_type} missing headers")
            elif not isinstance(table["headers"], list):
                errors.append(f"{prefix}.{table_type}.headers must be a list")

            if "rows" not in table:
                errors.append(f"{prefix}.{table_type} missing rows")
            elif not isinstance(table["rows"], list):
                errors.append(f"{prefix}.{table_type}.rows must be a list")
            else:
                # Validate each row
                for i, row in enumerate(table["rows"]):
                    if not isinstance(row, list):
                        errors.append(f"{prefix}.{table_type}.rows[{i}] must be a list")

        return errors

    def _validate_derivation_step(self, step: Dict[str, Any], prefix: str) -> List[str]:
        """Validate interactive derivation step structure."""
        errors = []

        required_fields = ["step_number", "stack", "input_remaining", "action", "explanation"]
        for field in required_fields:
            if field not in step:
                errors.append(f"{prefix} missing required field: {field}")

        if "stack" in step and not isinstance(step["stack"], list):
            errors.append(f"{prefix}.stack must be a list")

        if "action" in step and isinstance(step["action"], dict):
            action = step["action"]
            if "type" not in action:
                errors.append(f"{prefix}.action missing type")
            elif action["type"] not in ["shift", "reduce", "accept", "error"]:
                errors.append(f"{prefix}.action.type must be one of: shift, reduce, accept, error")

        return errors

    def export_logs(self, format: str = "json") -> str:
        """Export logs to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            filename = f"api_logs_{timestamp}.json"
            filepath = self.log_dir / filename

            with open(filepath, "w") as f:
                json.dump(self.request_logs, f, indent=2)

        elif format == "csv":
            filename = f"api_logs_{timestamp}.csv"
            filepath = self.log_dir / filename

            import csv

            with open(filepath, "w", newline="") as f:
                if self.request_logs:
                    writer = csv.DictWriter(f, fieldnames=self.request_logs[0].keys())
                    writer.writeheader()
                    writer.writerows(self.request_logs)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"📁 Logs exported to: {filepath}")
        return str(filepath)

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        return self.request_logs[-limit:]

    def clear_logs(self) -> None:
        """Clear all stored logs."""
        self.request_logs.clear()
        logger.info("🗑️ Logs cleared")


# Global validator instance
api_validator = APIValidator()
