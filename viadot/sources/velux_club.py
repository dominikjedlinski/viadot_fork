import json
import urllib
import os

from copy import deepcopy
from typing import Any, Dict, List, Literal
from datetime import datetime, timedelta
import requests

import numpy as np
import pandas as pd


from ..config import local_config
from ..exceptions import CredentialError
from ..utils import handle_api_response
from .base import Source


# Custom Errors!
class Source_NOK(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Dates_NOK(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Historical_Too_Old(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class VeluxClub(Source):
    """
    A class implementing the Velux Club API.

    Documentation for this API is located at: https://api.club.velux.com/api/v1/datalake/
    There are 4 endpoints where to get the data

    Args:
        Source (_type_): _description_

    Raises:
        CredentialError: _description_
        ValueError: _description_

    Returns:
        _type_: _description_
    """

    API_URL = "https://api.club.velux.com/api/v1/datalake/"

    def __init__(self, *args, credentials: Dict[str, Any] = None, **kwargs):
        DEFAULT_CREDENTIALS = local_config.get("VELUX_CLUB")
        credentials = kwargs.pop("credentials", DEFAULT_CREDENTIALS)
        if credentials is None:
            raise CredentialError("Missing credentials.")

        self.headers = {
            "Authorization": "Bearer " + credentials["TOKEN"],
            "Content-Type": "application/json",
        }

        super().__init__(*args, credentials=credentials, **kwargs)

    def build_query(
        self, source: str, from_date: str, to_date: str, api_url: str, region: str
    ) -> str:
        if source in ["jobs", "product", "company"]:
            # check if date filter was passed!
            if from_date == "" or to_date == "":
                return "Introduce a 'FROM Date' and 'To Date'"
            url = f"{api_url}{source}?from={from_date}&to={to_date}&region&limit=100"
        elif source in "survey":
            url = f"{api_url}{source}?language=en&type=question"
        else:
            return "pick one these sources: jobs, product, company, survey"
        return url

    def get_response(
        self,
        source: str = "",
        from_date: str = "2022-03-22",
        to_date: str = "",
        region="null",
    ) -> pd.DataFrame:  ## Returns the response
        # DocString

        # Dealing with bad arguments
        if source not in ["jobs", "product", "company", "survey"]:
            raise Source_NOK("The source has to be: jobs, product, company or survey")

        from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
        oldest_date_obj = datetime.strptime("2022-03-22", "%Y-%m-%d")
        delta = from_date_obj - oldest_date_obj

        if delta.days < 0:
            raise Historical_Too_Old("from_date cannot be earlier than 2023-03-22!!")

        to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
        delta = to_date_obj - from_date_obj

        if delta.days < 0:
            raise Dates_NOK("to_date cannot be earlier than from_date!")

        # Preparing the Query
        url = self.build_query(source, from_date, to_date, self.API_URL, region)
        headers = self.headers

        # Getting first page
        response = requests.request("GET", url, headers=headers)

        # Next Pages
        response = response.json()

        if isinstance(response, dict):
            keys_list = list(response.keys())
        elif isinstance(response, list):
            keys_list = list(response[0].keys())
        else:
            keys_list = []

        if "data" in keys_list:
            # first page content
            df = pd.DataFrame(response["data"])
            # next pages
            while response["next_page_url"] != None:
                url = f"{response['next_page_url']}&from={from_date}&to={to_date}&region&limit=100"
                r = requests.request("GET", url, headers=self.headers)
                response = r.json()
                df_page = pd.DataFrame(response["data"])
                if source == "product":
                    df_page = df_page.T

                df = pd.concat((df, df_page), axis=0)
        else:
            df = pd.DataFrame(response)

        return df

    def print_df(df: pd.DataFrame, service_name: str):
        print(f"{service_name} Dataframe Columns")
        print(list(df.columns))
        print(f"{service_name} Number of Columns")
        print(len(list(df.columns)))
        print(f"{service_name} Dataframe Number Of Samples")
        print(str(len(df.index)))
