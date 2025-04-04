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

# NOTE! THIS FILE IS AUTOMATICALLY GENERATED AND WILL BE OVERWRITTEN!
#
# IF YOU WANT TO MODIFY THIS FILE, YOU SHOULD MODIFY THE TEMPLATE
# `get_provider_info_TEMPLATE.py.jinja2` IN the `dev/breeze/src/airflow_breeze/templates` DIRECTORY


def get_provider_info():
    return {
        "package-name": "apache-airflow-providers-edge",
        "name": "Edge Executor",
        "description": "Handle edge workers on remote sites via HTTP(s) connection and orchestrates work over distributed sites\n",
        "state": "not-ready",
        "source-date-epoch": 1741121867,
        "versions": ["0.20.2b1"],
        "plugins": [
            {
                "name": "edge_executor",
                "plugin-class": "airflow.providers.edge.plugins.edge_executor_plugin.EdgeExecutorPlugin",
            }
        ],
        "executors": ["airflow.providers.edge.executors.EdgeExecutor"],
        "config": {
            "edge": {
                "description": "This section only applies if you are using the EdgeExecutor in\n``[core]`` section above\n",
                "options": {
                    "api_enabled": {
                        "description": "Flag if the plugin endpoint is enabled to serve Edge Workers.\n",
                        "version_added": None,
                        "type": "boolean",
                        "example": "True",
                        "default": "False",
                    },
                    "api_url": {
                        "description": "URL endpoint on which the Airflow code edge API is accessible from edge worker.\n",
                        "version_added": None,
                        "type": "string",
                        "example": "https://airflow.hosting.org/edge_worker/v1/rpcapi",
                        "default": None,
                    },
                    "job_poll_interval": {
                        "description": "Edge Worker currently polls for new jobs via HTTP. This parameter defines the number\nof seconds it should sleep between polls for new jobs.\nJob polling only happens if the Edge Worker seeks for new work. Not if busy.\n",
                        "version_added": None,
                        "type": "integer",
                        "example": "5",
                        "default": "5",
                    },
                    "heartbeat_interval": {
                        "description": "Edge Worker continuously reports status to the central site. This parameter defines\nhow often a status with heartbeat should be sent.\nDuring heartbeat status is reported as well as it is checked if a running task is to be terminated.\n",
                        "version_added": None,
                        "type": "integer",
                        "example": "10",
                        "default": "30",
                    },
                    "worker_concurrency": {
                        "description": "The concurrency defines the default max parallel running task instances and can also be set during\nstart of worker with the ``airflow edge worker`` command parameter. The size of the workers\nand the resources must support the nature of your tasks. The parameter\nworks together with the concurrency_slots parameter of a task.\n",
                        "version_added": None,
                        "type": "integer",
                        "example": None,
                        "default": "8",
                    },
                    "job_success_purge": {
                        "description": "Minutes after which successful jobs for EdgeExecutor are purged from database\n",
                        "version_added": None,
                        "type": "integer",
                        "example": None,
                        "default": "5",
                    },
                    "job_fail_purge": {
                        "description": "Minutes after which failed jobs for EdgeExecutor are purged from database\n",
                        "version_added": None,
                        "type": "integer",
                        "example": None,
                        "default": "60",
                    },
                    "push_log_chunk_size": {
                        "description": "Edge Worker uploads log files in chunks. If the log file part which is uploaded\nexceeds the chunk size it creates a new request. The application gateway can\nlimit the max body size see:\nhttps://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size\nA HTTP 413 issue can point to this value to fix the issue.\nThis value must be defined in Bytes.\n",
                        "version_added": None,
                        "type": "integer",
                        "example": None,
                        "default": "524288",
                    },
                },
            }
        },
        "dependencies": ["apache-airflow>=2.10.0", "pydantic>=2.11.0", "retryhttp>=1.2.0,!=1.3.0"],
        "optional-dependencies": {"fab": ["apache-airflow-providers-fab"]},
        "devel-dependencies": [],
    }
