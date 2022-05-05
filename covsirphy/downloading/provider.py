#!/usr/bin/env python
# -*- coding: utf-8 -*-

import contextlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib
import pandas as pd
from covsirphy.util.term import Term


class _DataProvider(Term):
    """Extract datasets and save it locally.

    Args:
        filename (str or pathlib.Path): filename to save/read the download
        update_interval (int): update interval of downloading dataset
        stdout (str or None): stdout when downloading (shown at most one time) or None (no outputs)
    """

    def __init__(self, filename, update_interval, stdout):
        self._filename = filename
        self._update_interval = update_interval
        self._stdout = stdout

    def latest(self, url, columns, date, date_format):
        """Provide the last dataset as a dataframe, downloading remote files or reading local files.

        Args:
            url (str): URL of the dataset
            columns (list[str]): column names the dataset must have
            date (str or None): column name of date
            date_format (str): format of date column, like %Y-%m-%d

        Note:
            If @verbose is 0, no descriptions will be shown.
            If @verbose is 1 or larger, URL and database name will be shown.
        """
        if not self._download_necessity(self._filename):
            with contextlib.suppress(ValueError):
                return self._read_csv(self._filename, columns, date=date, date_format=date_format)
        if self._stdout is not None:
            print(self._stdout)
            self._stdout = None
        df = self._read_csv(url, columns, date=date, date_format=date_format)
        df.to_csv(self._filename, index=False)
        return df

    @staticmethod
    def _last_updated_local(path):
        """
        Return the date last updated of local file/directory.

        Args:
            path (str or pathlib.Path): name of the file/directory

        Returns:
            datetime.datetime: time last updated (UTC)
        """
        m_time = Path(path).stat().st_mtime
        date = datetime.fromtimestamp(m_time)
        return date.astimezone(timezone.utc).replace(tzinfo=None)

    def _download_necessity(self, filename):
        """
        Return whether we need to get the data from remote servers or not,
        comparing the last update of the files.

        Args:
            filename (str): filename of the local file

        Returns:
            (bool): whether we need to get the data from remote servers or not

        Note:
            If the last updated date is unknown, returns True.
            If @update_interval (of _DataProvider) hours have passed and the remote file was updated, return True.
        """
        if not Path(filename).exists():
            return True
        date_local = self._last_updated_local(filename)
        time_limit = date_local + timedelta(hours=self._update_interval)
        return datetime.now() >= time_limit

    @staticmethod
    def _read_csv(path, columns, date, date_format):
        """Read the CSV file and return as a dataframe.

        Args:
            columns (list[str]): column names the dataset must have
            date (str or None): column name of date
            date_format (str): format of date column, like %Y-%m-%d

        Returns:
            pandas.DataFrame: downloaded data
        """
        kwargs = {
            "low_memory": False, "header": 0, "usecols": columns,
            "parse_dates": None if date is None else [date], "date_parser": lambda x: pd.datetime.strptime(x, date_format)
        }
        try:
            return pd.read_csv(path, **kwargs)
        except urllib.error.HTTPError:
            return pd.read_csv(path, storage_options={"User-Agent": "Mozilla/5.0"}, **kwargs)
