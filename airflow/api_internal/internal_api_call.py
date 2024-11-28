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

import logging
from functools import wraps
from http import HTTPStatus
from typing import Callable, TypeVar

from airflow.exceptions import AirflowException
from airflow.typing_compat import ParamSpec

PS = ParamSpec("PS")
RT = TypeVar("RT")

logger = logging.getLogger(__name__)


class AirflowHttpException(AirflowException):
    """Raise when there is a problem during an http request on the internal API decorator."""

    def __init__(self, message: str, status_code: HTTPStatus):
        super().__init__(message)
        self.status_code = status_code


def internal_api_call(func: Callable[PS, RT]) -> Callable[PS, RT]:
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
