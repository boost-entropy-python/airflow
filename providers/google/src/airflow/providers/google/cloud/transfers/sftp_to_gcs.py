#
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
"""This module contains SFTP to Google Cloud Storage operator."""

from __future__ import annotations

import os
from collections.abc import Sequence
from functools import cached_property
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from airflow.exceptions import AirflowException
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.version_compat import BaseOperator
from airflow.providers.sftp.hooks.sftp import SFTPHook

if TYPE_CHECKING:
    from airflow.utils.context import Context


WILDCARD = "*"


class SFTPToGCSOperator(BaseOperator):
    """
    Transfer files to Google Cloud Storage from SFTP server.

    .. seealso::
        For more information on how to use this operator, take a look at the guide:
        :ref:`howto/operator:SFTPToGCSOperator`

    :param source_path: The sftp remote path. This is the specified file path
        for downloading the single file or multiple files from the SFTP server.
        You can use only one wildcard within your path. The wildcard can appear
        inside the path or at the end of the path.
    :param destination_bucket: The bucket to upload to.
    :param destination_path: The destination name of the object in the
        destination Google Cloud Storage bucket.
        If destination_path is not provided file/files will be placed in the
        main bucket path.
        If a wildcard is supplied in the destination_path argument, this is the
        prefix that will be prepended to the final destination objects' paths.
    :param gcp_conn_id: (Optional) The connection ID used to connect to Google Cloud.
    :param sftp_conn_id: The sftp connection id. The name or identifier for
        establishing a connection to the SFTP server.
    :param mime_type: The mime-type string
    :param gzip: Allows for file to be compressed and uploaded as gzip
    :param move_object: When move object is True, the object is moved instead
        of copied to the new location. This is the equivalent of a mv command
        as opposed to a cp command.
    :param impersonation_chain: Optional service account to impersonate using short-term
        credentials, or chained list of accounts required to get the access_token
        of the last account in the list, which will be impersonated in the request.
        If set as a string, the account must grant the originating account
        the Service Account Token Creator IAM role.
        If set as a sequence, the identities from the list must grant
        Service Account Token Creator IAM role to the directly preceding identity, with first
        account from the list granting this role to the originating account (templated).
    :param sftp_prefetch: Whether to enable SFTP prefetch, the default is True.
    :param use_stream: Determines the transfer method from SFTP to GCS.
        When ``False`` (default), the file downloads locally
        then uploads (may require significant disk space).
        When ``True``, the file streams directly without using local disk.
        Defaults to ``False``.
    """

    template_fields: Sequence[str] = (
        "source_path",
        "destination_path",
        "destination_bucket",
        "impersonation_chain",
    )

    def __init__(
        self,
        *,
        source_path: str,
        destination_bucket: str,
        destination_path: str | None = None,
        gcp_conn_id: str = "google_cloud_default",
        sftp_conn_id: str = "ssh_default",
        mime_type: str = "application/octet-stream",
        gzip: bool = False,
        move_object: bool = False,
        impersonation_chain: str | Sequence[str] | None = None,
        sftp_prefetch: bool = True,
        use_stream: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.source_path = source_path
        self.destination_path = destination_path
        self.destination_bucket = destination_bucket
        self.gcp_conn_id = gcp_conn_id
        self.mime_type = mime_type
        self.gzip = gzip
        self.sftp_conn_id = sftp_conn_id
        self.move_object = move_object
        self.impersonation_chain = impersonation_chain
        self.sftp_prefetch = sftp_prefetch
        self.use_stream = use_stream

    @cached_property
    def sftp_hook(self):
        return SFTPHook(self.sftp_conn_id)

    def execute(self, context: Context):
        self.destination_path = self._set_destination_path(self.destination_path)
        self.destination_bucket = self._set_bucket_name(self.destination_bucket)
        gcs_hook = GCSHook(
            gcp_conn_id=self.gcp_conn_id,
            impersonation_chain=self.impersonation_chain,
        )

        if WILDCARD in self.source_path:
            total_wildcards = self.source_path.count(WILDCARD)
            if total_wildcards > 1:
                raise AirflowException(
                    "Only one wildcard '*' is allowed in source_path parameter. "
                    f"Found {total_wildcards} in {self.source_path}."
                )

            prefix, delimiter = self.source_path.split(WILDCARD, 1)
            base_path = os.path.dirname(prefix)

            files, _, _ = self.sftp_hook.get_tree_map(base_path, prefix=prefix, delimiter=delimiter)

            for file in files:
                destination_path = file.replace(base_path, self.destination_path, 1)
                # See issue: https://github.com/apache/airflow/issues/41763
                # If the destination_path is not specified, it defaults to an empty string. As a result,
                # replacing base_path with an empty string is ineffective, causing the destination_path to
                # retain the "/" prefix, if it has.
                if not self.destination_path:
                    destination_path = destination_path.lstrip("/")
                self._copy_single_object(gcs_hook, self.sftp_hook, file, destination_path)

        else:
            destination_object = (
                self.destination_path if self.destination_path else self.source_path.rsplit("/", 1)[1]
            )
            self._copy_single_object(gcs_hook, self.sftp_hook, self.source_path, destination_object)

    def _copy_single_object(
        self,
        gcs_hook: GCSHook,
        sftp_hook: SFTPHook,
        source_path: str,
        destination_object: str,
    ) -> None:
        """Copy single object."""
        self.log.info(
            "Executing copy of %s to gs://%s/%s",
            source_path,
            self.destination_bucket,
            destination_object,
        )

        if self.use_stream:
            dest_bucket = gcs_hook.get_bucket(self.destination_bucket)
            dest_blob = dest_bucket.blob(destination_object)
            with dest_blob.open("wb") as write_stream:
                sftp_hook.retrieve_file(source_path, write_stream, prefetch=self.sftp_prefetch)
        else:
            with NamedTemporaryFile("w") as tmp:
                sftp_hook.retrieve_file(source_path, tmp.name, prefetch=self.sftp_prefetch)

                gcs_hook.upload(
                    bucket_name=self.destination_bucket,
                    object_name=destination_object,
                    filename=tmp.name,
                    mime_type=self.mime_type,
                    gzip=self.gzip,
                )

        if self.move_object:
            self.log.info("Executing delete of %s", source_path)
            sftp_hook.delete_file(source_path)

    @staticmethod
    def _set_destination_path(path: str | None) -> str:
        if path is not None:
            return path.lstrip("/") if path.startswith("/") else path
        return ""

    @staticmethod
    def _set_bucket_name(name: str) -> str:
        bucket = name if not name.startswith("gs://") else name[5:]
        return bucket.strip("/")

    def get_openlineage_facets_on_start(self):
        from airflow.providers.common.compat.openlineage.facet import Dataset
        from airflow.providers.google.cloud.openlineage.utils import extract_ds_name_from_gcs_path
        from airflow.providers.openlineage.extractors import OperatorLineage

        source_name = extract_ds_name_from_gcs_path(self.source_path.split(WILDCARD, 1)[0])
        if self.source_path.startswith("/") and source_name != "/":
            source_name = "/" + source_name

        if WILDCARD not in self.source_path and not self.destination_path:
            dest_name = self.source_path.rsplit("/", 1)[1]
        else:
            dest_name = extract_ds_name_from_gcs_path(f"{self.destination_path}")

        return OperatorLineage(
            inputs=[
                Dataset(
                    namespace=f"file://{self.sftp_hook.remote_host}:{self.sftp_hook.port}",
                    name=source_name,
                )
            ],
            outputs=[
                Dataset(namespace="gs://" + self._set_bucket_name(self.destination_bucket), name=dest_name)
            ],
        )
