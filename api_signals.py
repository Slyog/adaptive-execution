import re


NETWORK_ERROR_MARKERS = [
    "[errno -3] try again",
    "socket.gaierror",
    "connection refused",
    "name or service not known",
    "temporary failure in name resolution",
    "timed out",
    "could not resolve host: host.docker.internal",
    "failed to resolve host.docker.internal",
    "host.docker.internal resolution",
]


def _contains_ordered(sequence: list[int], expected: list[int]) -> bool:
    position = 0
    for item in sequence:
        if item == expected[position]:
            position += 1
            if position == len(expected):
                return True
    return False


def _has_later_status(sequence: list[int], status: int, later_status: int) -> bool:
    for index, item in enumerate(sequence):
        if item == status and later_status in sequence[index + 1 :]:
            return True
    return False


def extract_api_signals(stdout: str, stderr: str = "") -> dict:
    status_sequence = []
    for line in (stdout or "").splitlines():
        match = re.match(r"^\s*(401|400|200)\b", line)
        if match:
            status_sequence.append(int(match.group(1)))

    combined_output = "\n".join(part for part in (stdout or "", stderr or "") if part).lower()
    network_errors = [marker for marker in NETWORK_ERROR_MARKERS if marker in combined_output]
    is_infrastructure_failure = bool(network_errors)
    has_success_path = _contains_ordered(status_sequence, [401, 400, 200])

    if is_infrastructure_failure:
        failure_category = "network"
        success = False
    elif has_success_path:
        failure_category = "none"
        success = True
    elif 401 in status_sequence and not _has_later_status(status_sequence, 401, 200):
        failure_category = "auth"
        success = False
    elif 400 in status_sequence and not _has_later_status(status_sequence, 400, 200):
        failure_category = "validation"
        success = False
    else:
        failure_category = "unknown"
        success = False

    return {
        "network_reachable": not is_infrastructure_failure,
        "auth_failure_observed": 401 in status_sequence,
        "validation_failure_observed": 400 in status_sequence,
        "success_observed": 200 in status_sequence,
        "status_sequence": status_sequence,
        "final_success": success,
        "failure_category": failure_category,
        "is_infrastructure_failure": is_infrastructure_failure,
        "success": success,
    }


def extract_api_signals_from_outputs(outputs: list[dict]) -> dict:
    stdout = "\n".join(output.get("stdout", "") for output in outputs)
    stderr = "\n".join(output.get("stderr", "") for output in outputs)
    return extract_api_signals(stdout, stderr)
