import copy
import json
import os
from datetime import timedelta
from typing import Any, Dict, List, Literal

import pandas as pd
import prefect
from prefect import Task
from prefect.tasks.secrets import PrefectSecret
from prefect.utilities import logging
from prefect.utilities.tasks import defaults_from_attrs

from viadot.task_utils import *

from ..sources import VidClub

logger = logging.get_logger()


class VidClubToDF(Task):
    def __init__(
        self,
        source: Literal["jobs", "product", "company", "survey"] = None,
        credentials: Dict[str, Any] = None,
        credentials_secret: str = "VIDCLUB",
        vault_name: str = None,
        from_date: str = "2022-03-22",
        to_date: str = "",
        timeout: int = 3600,
        report_name: str = "vid_club_to_df",
        *args: List[Any],
        **kwargs: Dict[str, Any],
    ):
        """
        Task to downloading data from Vid Club APIs to Pandas DataFrame.

        Args:
            source (Literal["jobs", "product", "company", "survey"], optional): The endpoint source to be accessed. Defaults to None.
            credentials (Dict[str, Any], optional): Stores the credentials information. Defaults to None.
            credentials_secret (str, optional): The name of the secret in Azure Key Vault or Prefect or local_config file. Defaults to "VIDCLUB".
            vault_name (str, optional): For credentials stored in Azure Key Vault. The name of the vault from which to obtain the secret. Defaults to None.
            from_date (str): Start date for the query, by default is the oldest date in the data, '2022-03-22'.
            to_date (str): End date for the query, if empty, datetime.today() will be used.
            timeout (int, optional): The amount of time (in seconds) to wait while running this task before
                a timeout occurs. Defaults to 3600.
            report_name (str, optional): Stores the report name. Defaults to "vid_club_to_df".

        Returns: Pandas DataFrame
        """
        self.source = source
        self.from_date = from_date
        self.to_date = to_date
        self.report_name = report_name
        self.credentials_secret = credentials_secret
        self.vault_name = vault_name

        if credentials is None:
            self.credentials = credentials_loader.run(
                credentials_secret=credentials_secret, vault_name=vault_name
            )
        else:
            self.credentials = credentials

        super().__init__(
            name=self.report_name,
            timeout=timeout,
            *args,
            **kwargs,
        )

    def __call__(self, *args, **kwargs):
        """Download Vid Club data to Pandas DataFrame"""
        return super().__call__(*args, **kwargs)

    @defaults_from_attrs(
        "source",
        "credentials",
        "credentials_secret",
        "vault_name",
        "from_date",
        "to_date",
    )
    def run(
        self,
        source: Literal["jobs", "product", "company", "survey"] = None,
        credentials: Dict[str, Any] = None,
        from_date: str = "2022-03-22",
        to_date: str = "",
        items_per_page: int = 100,
        region: str = "null",
        days_interval: int = 30,
    ) -> pd.DataFrame:
        """
        Task run method.

        Args:
            source (Literal["jobs", "product", "company", "survey"], optional): The endpoint source to be accessed. Defaults to None.
            credentials (Dict[str, Any], optional): Stores the credentials information. Defaults to None.
            from_date (str, optional): Start date for the query, by default is the oldest date in the data, '2022-03-22'.
            to_date (str, optional): End date for the query, if empty, datetime.today() will be used.
            items_per_page (int, optional): Number of entries per page. 100 entries by default.
            region (str, optinal): Region filter for the query. By default, it is empty.
            days_interval (int, optional): Days specified in date range per api call (test showed that 30-40 is optimal for performance). Defaults to 30.

        Returns:
            pd.DataFrame: The query result as a pandas DataFrame.
        """

        vc_obj = VidClub(credentials=credentials)

        vc_dataframe = vc_obj.total_load(
            source=source,
            from_date=from_date,
            to_date=to_date,
            items_per_page=items_per_page,
            region=region,
            days_interval=days_interval,
        )

        return vc_dataframe
