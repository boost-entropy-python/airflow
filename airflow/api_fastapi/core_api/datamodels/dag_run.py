# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import AwareDatetime, Field, NonNegativeInt, model_validator

from airflow.api_fastapi.core_api.base import BaseModel, StrictBaseModel
from airflow.models import DagRun
from airflow.utils import timezone
from airflow.utils.state import DagRunState
from airflow.utils.types import DagRunTriggeredByType, DagRunType


class DAGRunPatchStates(str, Enum):
    """Enum for DAG Run states when updating a DAG Run."""

    QUEUED = DagRunState.QUEUED
    SUCCESS = DagRunState.SUCCESS
    FAILED = DagRunState.FAILED


class DAGRunPatchBody(StrictBaseModel):
    """DAG Run Serializer for PATCH requests."""

    state: DAGRunPatchStates | None = None
    note: str | None = Field(None, max_length=1000)


class DAGRunClearBody(StrictBaseModel):
    """DAG Run serializer for clear endpoint body."""

    dry_run: bool = True
    only_failed: bool = False


class DAGRunResponse(BaseModel):
    """DAG Run serializer for responses."""

    dag_run_id: str = Field(validation_alias="run_id")
    dag_id: str
    logical_date: datetime | None
    queued_at: datetime | None
    start_date: datetime | None
    end_date: datetime | None
    data_interval_start: datetime | None
    data_interval_end: datetime | None
    run_after: datetime
    last_scheduling_decision: datetime | None
    run_type: DagRunType
    state: DagRunState
    external_trigger: bool
    triggered_by: DagRunTriggeredByType
    conf: dict
    note: str | None


class DAGRunCollectionResponse(BaseModel):
    """DAG Run Collection serializer for responses."""

    dag_runs: list[DAGRunResponse]
    total_entries: int


class TriggerDAGRunPostBody(StrictBaseModel):
    """Trigger DAG Run Serializer for POST body."""

    dag_run_id: str | None = None
    data_interval_start: AwareDatetime | None = None
    data_interval_end: AwareDatetime | None = None
    logical_date: AwareDatetime | None
    run_after: datetime = Field(default_factory=timezone.utcnow)

    conf: dict = Field(default_factory=dict)
    note: str | None = None

    @model_validator(mode="after")
    def check_data_intervals(cls, values):
        if (values.data_interval_start is None) != (values.data_interval_end is None):
            raise ValueError(
                "Either both data_interval_start and data_interval_end must be provided or both must be None"
            )
        return values

    ## when logical date is null, the run id should be generated from run_after + random string.
    # TODO: AIP83: we need to modify this validator after https://github.com/apache/airflow/pull/46398 is merged
    @model_validator(mode="after")
    def validate_dag_run_id(self):
        if not self.dag_run_id:
            self.dag_run_id = DagRun.generate_run_id(
                run_type=DagRunType.MANUAL, logical_date=self.logical_date, run_after=self.run_after
            )
        return self


class DAGRunsBatchBody(StrictBaseModel):
    """List DAG Runs body for batch endpoint."""

    order_by: str | None = None
    page_offset: NonNegativeInt = 0
    page_limit: NonNegativeInt = 100
    dag_ids: list[str] | None = None
    states: list[DagRunState | None] | None = None
    logical_date_gte: AwareDatetime | None = None
    logical_date_lte: AwareDatetime | None = None
    start_date_gte: AwareDatetime | None = None
    start_date_lte: AwareDatetime | None = None
    end_date_gte: AwareDatetime | None = None
    end_date_lte: AwareDatetime | None = None
