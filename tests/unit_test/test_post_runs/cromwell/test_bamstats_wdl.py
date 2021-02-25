#!/usr/bin/env python3
# coding: utf-8
import json
import shlex
import subprocess
from time import sleep

from sapporo.type import RunId

from . import SCRIPT_DIR, TEST_HOST, TEST_PORT  # type: ignore


def post_runs_bamstats_wdl() -> RunId:
    script_path = \
        SCRIPT_DIR.joinpath("bamstats_wdl/post_runs.sh")
    proc = subprocess.run(shlex.split(f"/bin/bash {str(script_path)}"),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          encoding="utf-8",
                          env={"SAPPORO_HOST": TEST_HOST,
                               "SAPPORO_PORT": TEST_PORT})
    assert proc.returncode == 0
    res_data: RunId = json.loads(proc.stdout)

    return res_data


def test_bamstats_wdl(setup_test_server: None) -> None:
    res_data = post_runs_bamstats_wdl()
    assert "run_id" in res_data
    run_id = res_data["run_id"]

    from .. import get_run_id_status
    count = 0
    while count <= 120:
        get_status_data = get_run_id_status(run_id)
        if str(get_status_data["state"]) in \
                ["COMPLETE", "EXECUTOR_ERROR", "SYSTEM_ERROR", "CANCELED"]:
            break
        sleep(3)
        count += 1
    assert str(get_status_data["state"]) == "COMPLETE"

    from .. import get_run_id
    data = get_run_id(run_id)

    assert "bamstats_report.zip" in data["outputs"]
    assert "{\n  \"workflow_name\": \"dockstore-tool-bamstats-wdl\"\n}\n" == \
        data["request"]["tags"]
    assert len(data["request"]["workflow_attachment"]) == 2
    assert "cromwell" == data["request"]["workflow_engine_name"]
    assert "{}" == data["request"]["workflow_engine_parameters"]
    assert "dockstore-tool-bamstats-wdl" == data["request"]["workflow_name"]
    assert "WDL" == data["request"]["workflow_type"]
    assert "1.0" == data["request"]["workflow_type_version"]
    assert "./Dockstore.wdl" == data["request"]["workflow_url"]
    assert run_id == data["run_id"]
    assert data["run_log"]["exit_code"] == 0
    assert data["run_log"]["name"] == "dockstore-tool-bamstats-wdl"
    assert "Workflow bamstatsWorkflow complete." in data["run_log"]["stdout"]
    assert str(data["state"]) == "COMPLETE"
    assert data["task_logs"] is None