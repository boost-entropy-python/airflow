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
from contextlib import AsyncExitStack, asynccontextmanager
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from fastapi import FastAPI
from starlette.routing import Mount

from airflow.api_fastapi.core_api.app import (
    init_config,
    init_dag_bag,
    init_error_handlers,
    init_flask_plugins,
    init_middlewares,
    init_plugins,
    init_views,
)
from airflow.api_fastapi.execution_api.app import create_task_execution_api_app
from airflow.configuration import conf
from airflow.exceptions import AirflowConfigException

if TYPE_CHECKING:
    from airflow.api_fastapi.auth.managers.base_auth_manager import BaseAuthManager

log = logging.getLogger(__name__)

app: FastAPI | None = None
auth_manager: BaseAuthManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        for route in app.routes:
            if isinstance(route, Mount) and isinstance(route.app, FastAPI):
                await stack.enter_async_context(
                    route.app.router.lifespan_context(route.app),
                )
        app.state.lifespan_called = True
        yield


def create_app(apps: str = "all") -> FastAPI:
    apps_list = apps.split(",") if apps else ["all"]

    fastapi_base_url = conf.get("api", "base_url", fallback="")
    if fastapi_base_url and not fastapi_base_url.endswith("/"):
        fastapi_base_url += "/"
        conf.set("api", "base_url", fastapi_base_url)

    root_path = urlsplit(fastapi_base_url).path.removesuffix("/")

    app = FastAPI(
        title="Airflow API",
        description="Airflow API. All endpoints located under ``/public`` can be used safely, are stable and backward compatible. "
        "Endpoints located under ``/ui`` are dedicated to the UI and are subject to breaking change "
        "depending on the need of the frontend. Users should not rely on those but use the public ones instead.",
        lifespan=lifespan,
        root_path=root_path,
    )

    if "execution" in apps_list or "all" in apps_list:
        task_exec_api_app = create_task_execution_api_app()
        init_error_handlers(task_exec_api_app)
        app.mount("/execution", task_exec_api_app)

    if "core" in apps_list or "all" in apps_list:
        init_dag_bag(app)
        init_plugins(app)
        init_auth_manager(app)
        init_flask_plugins(app)
        init_views(app)  # Core views need to be the last routes added - it has a catch all route
        init_error_handlers(app)
        init_middlewares(app)

    init_config(app)

    return app


def cached_app(config=None, testing=False, apps="all") -> FastAPI:
    """Return cached instance of Airflow API app."""
    global app
    if not app:
        app = create_app(apps=apps)
    return app


def purge_cached_app() -> None:
    """Remove the cached version of the app in global state."""
    global app
    app = None


def get_auth_manager_cls() -> type[BaseAuthManager]:
    """
    Return just the auth manager class without initializing it.

    Useful to save execution time if only static methods need to be called.
    """
    auth_manager_cls = conf.getimport(section="core", key="auth_manager")

    if not auth_manager_cls:
        raise AirflowConfigException(
            "No auth manager defined in the config. "
            "Please specify one using section/key [core/auth_manager]."
        )

    return auth_manager_cls


def create_auth_manager() -> BaseAuthManager:
    """Create the auth manager."""
    global auth_manager
    auth_manager_cls = get_auth_manager_cls()
    auth_manager = auth_manager_cls()
    return auth_manager


def init_auth_manager(app: FastAPI | None = None) -> BaseAuthManager:
    """Initialize the auth manager."""
    am = create_auth_manager()
    am.init()

    if app and (auth_manager_fastapi_app := am.get_fastapi_app()):
        app.mount("/auth", auth_manager_fastapi_app)
        app.state.auth_manager = am

    return am


def get_auth_manager() -> BaseAuthManager:
    """Return the auth manager, provided it's been initialized before."""
    global auth_manager

    if auth_manager is None:
        raise RuntimeError(
            "Auth Manager has not been initialized yet. "
            "The `init_auth_manager` method needs to be called first."
        )
    return auth_manager
