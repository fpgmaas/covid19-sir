#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import ruptures as rpt
from covsirphy.util.error import deprecate, UnExpectedValueError
from covsirphy.util.term import Term
from covsirphy.trend.sr_change import _SRChange


class TrendDetector(Term):
    """
    Interface for trend analysis (change point analysis).

    Args:
        data (pandas.DataFrame): data to analyse
            Index:
                reset index
            Column:
                - Date(pd.Timestamp): Observation date
                - Confirmed(int): the number of confirmed cases
                - Infected(int): the number of currently infected cases
                - Fatal(int): the number of fatal cases
                - Recovered (int): the number of recovered cases
                - Susceptible(int): the number of susceptible cases
        area (str): area name (used in the figure title)
        min_size (int): minimum value of phase length [days], over 2

    Note:
        "Phase" means a sequential dates in which the parameters of SIR-derived models are fixed.
        "Change points" means the dates when trend was changed.
        "Change points" is the same as the start dates of phases except for the 0th phase.
    """

    def __init__(self, data, area="Selected area", min_size=5):
        self._ensure_dataframe(data, name="data", columns=self.SUB_COLUMNS)
        # Index: Date, Columns: the number cases
        self._record_df = data.groupby(self.DATE).last()
        # Minimum size of phases
        self._min_size = self._ensure_int_range(min_size, name="min_size", value_range=(3, None))
        if len(self._record_df) < self._min_size * 2:
            raise ValueError(f"More than {min_size * 2} records must be included because @min_size is {min_size}.")
        # The first/last date
        self._first_point = self._record_df.index.min()
        self._last_point = self._record_df.index.max()
        # Area name
        self._area = area
        # Change points: list[pandas.Timestamp]
        self._points = []

    def reset(self):
        """
        Reset the phase setting with the end dates of the records.

        Returns:
            covsirphy.TrendDetector: self
        """
        self._points = []
        return self

    def dates(self):
        """
        Return the list of start dates and end dates.

        Returns:
            tuple(list[str], list[str]): list of start dates and end dates
        """
        points = self._points[:]
        # Start dates
        start_dates = [date.strftime(self.DATE_FORMAT) for date in [self._first_point, *points]]
        # End dates
        end_dates = [self.yesterday(date.strftime(self.DATE_FORMAT)) for date in points]
        end_dates.append(self._last_point.strftime(self.DATE_FORMAT))
        return (start_dates, end_dates)

    def summary(self):
        """
        Summarize the phases with a dataframe.

        Returns:
            pandas.Dataframe:
                Index
                    (str): phase names
                Columns
                    - Start (pandas.Timestamp): star dates
                    - End (pandas.Timestamp): end dates
                    - RMSLE_S-R: RMSLE score on S-R plane
        """
        start_dates, end_dates = self.dates()
        return pd.DataFrame(
            {
                self.START: start_dates,
                self.END: end_dates,
                "RMSLE_S-R": _SRChange(sr_df=self._record_df).score(change_points=self._points),
            },
            index=[self.num2str(num) for num in range(len(self._points) + 1)]
        )

    def sr(self, algo="Pelt-rbf", **kwargs):
        """
        Perform S-R trend analysis.

        Args:
            algo (str): detection algorithms and models
            kwargs: the other arguments of algorithm classes (ruptures.Pelt, .Binseg, BottomUp)

        Raises:
            UnExpectedValueError: un-expected value was applied as algorithm name

        Returns:
            covsirphy.TrendDetector: self

        Note:
            Candidates of @algo are "Pelt-rbf", "Binseg-rbf", "Binseg-normal", "BottomUp-rbf", "BottomUp-normal".
            Please refer to documentation of ruptures package.
            https://centre-borelli.github.io/ruptures-docs/
        """
        # Set algorithm class
        algo_kwargs = {"jump": 1, "min_size": self._min_size}
        algo_kwargs.update(kwargs)
        algo_dict = {
            "Pelt-rbf": (rpt.Pelt, {"model": "rbf"}),
            "Binseg-rbf": (rpt.Binseg, {"model": "rbf"}),
            "Binseg-normal": (rpt.Binseg, {"model": "normal"}),
            "BottomUp-rbf": (rpt.BottomUp, {"model": "rbf"}),
            "BottomUp-normal": (rpt.BottomUp, {"model": "normal"}),
        }
        if algo not in algo_dict:
            raise UnExpectedValueError(name="algo", value=algo, candidates=list(algo_dict.keys()))
        algo_kwargs.update(algo_dict[algo][1])
        algorithm = algo_dict[algo][0](**algo_kwargs)
        # Run trend analysis
        finder = _SRChange(sr_df=self._record_df)
        points = finder.run(algorithm=algorithm, **algo_kwargs)
        self._points = sorted(set(self._points) | set(points))
        return self

    def show(self, **kwargs):
        """
        Show the trend on S-R plane.

        Args:
            kwargs: keyword arguments of covsirphy.trend_plot()
        """
        finder = _SRChange(sr_df=self._record_df)
        finder.show(self._points, self._area, **kwargs)


class Trend(TrendDetector):
    """
    Deprecated. Please use TrendDetector class.
    """
    @deprecate("covsirphy.Trend", new="covsirphy.TrendDetector", version="2.17.0-zeta")
    def __init__(self, data, area="Selected area", min_size=5):
        super().__init__(data, area=area, min_size=min_size)


class ChangeFinder(TrendDetector):
    """
    Deprecated. Please use TrendDetector class.
    """
    @deprecate("covsirphy.ChangeFinder", new="covsirphy.TrendDetector", version="2.17.0-zeta")
    def __init__(self, data, area="Selected area", min_size=5):
        super().__init__(data, area=area, min_size=min_size)
