from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "agent" / "kzabbix_evidence.py"
SPEC = spec_from_file_location("kzabbix_evidence", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_parse_loadavg_labels_linux_intervals():
    result = MODULE.parse_loadavg("2.89 2.91 2.81 5/4292 12345")

    assert result == {
        "load_1m": 2.89,
        "load_5m": 2.91,
        "load_15m": 2.81,
        "running_processes": 5,
        "total_processes": 4292,
        "last_pid": 12345,
    }
