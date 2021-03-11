#!/usr/bin/env python3
# coding: utf-8
import json
import shlex
import subprocess
from time import sleep

from sapporo.type import RunId

from . import SCRIPT_DIR, TEST_HOST, TEST_PORT  # type: ignore


def post_runs_attach_all_files_registered() -> RunId:
    script_path = \
        SCRIPT_DIR.joinpath("attach_all_files_registered/post_runs.sh")
    proc = subprocess.run(shlex.split(f"/bin/bash {str(script_path)}"),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          encoding="utf-8",
                          env={"SAPPORO_HOST": TEST_HOST,
                               "SAPPORO_PORT": TEST_PORT})
    assert proc.returncode == 0
    res_data: RunId = json.loads(proc.stdout)

    return res_data


def test_attach_all_files_registered(
        setup_test_server_registered_only_mode: None) -> None:
    res_data = post_runs_attach_all_files_registered()
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

    assert len(data["outputs"]) == 6
    assert "{}" == data["request"]["tags"]
    assert len(data["request"]["workflow_attachment"]) == 3
    assert "cwltool" == data["request"]["workflow_engine_name"]
    assert "{}" == data["request"]["workflow_engine_parameters"]
    assert "cwltool_attach_all_files" == data["request"]["workflow_name"]
    assert "CWL" == data["request"]["workflow_type"]
    assert "v1.0" == data["request"]["workflow_type_version"]
    assert "./trimming_and_qc.cwl" == data["request"]["workflow_url"]
    assert run_id == data["run_id"]
    assert data["run_log"]["exit_code"] == 0
    assert data["run_log"]["name"] == "cwltool_attach_all_files"
    assert "Final process status is success" in data["run_log"]["stderr"]
    assert str(data["state"]) == "COMPLETE"
    assert data["task_logs"] is None