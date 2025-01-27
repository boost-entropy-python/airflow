/*!
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { useQueryClient } from "@tanstack/react-query";

import {
  UseDagRunServiceGetDagRunKeyFn,
  useDagRunServiceGetDagRunsKey,
  UseTaskInstanceServiceGetTaskInstanceKeyFn,
  useTaskInstanceServiceGetTaskInstancesKey,
  useTaskInstanceServicePostClearTaskInstances,
} from "openapi/queries";
import type { ClearTaskInstancesBody, TaskInstanceCollectionResponse } from "openapi/requests/types.gen";
import { toaster } from "src/components/ui";

const onError = () => {
  toaster.create({
    description: "Clear Task Instance request failed",
    title: "Failed to clear the Task Instance",
    type: "error",
  });
};

export const useClearTaskInstances = ({
  dagId,
  dagRunId,
  onSuccessConfirm,
}: {
  dagId: string;
  dagRunId: string;
  onSuccessConfirm: () => void;
}) => {
  const queryClient = useQueryClient();

  const onSuccess = async (
    _: TaskInstanceCollectionResponse,
    variables: { dagId: string; requestBody: ClearTaskInstancesBody },
  ) => {
    // deduplication using set as user can clear multiple map index of the same task_id.
    const taskInstanceKeys = [
      ...new Set(
        (variables.requestBody.task_ids ?? [])
          .filter((taskId) => typeof taskId === "string" || Array.isArray(taskId))
          .map((taskId) => {
            const actualTaskId = Array.isArray(taskId) ? taskId[0] : taskId;
            const runId = variables.requestBody.dag_run_id;

            if (runId === null || runId === undefined) {
              return undefined;
            }

            const params = { dagId, dagRunId: runId, taskId: actualTaskId };

            return UseTaskInstanceServiceGetTaskInstanceKeyFn(params);
          })
          .filter((key) => key !== undefined),
      ),
    ];

    const queryKeys = [
      [useTaskInstanceServiceGetTaskInstancesKey],
      ...taskInstanceKeys,
      UseDagRunServiceGetDagRunKeyFn({ dagId, dagRunId }),
      [useDagRunServiceGetDagRunsKey],
    ];

    await Promise.all(queryKeys.map((key) => queryClient.invalidateQueries({ queryKey: key })));

    onSuccessConfirm();
  };

  return useTaskInstanceServicePostClearTaskInstances({
    onError,
    onSuccess,
  });
};
