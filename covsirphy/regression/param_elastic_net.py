#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from sklearn.linear_model import MultiTaskElasticNetCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from covsirphy.regression.regbase import _RegressorBase
from covsirphy.regression.reg_rate_converter import _RateConverter


class _ParamElasticNetRegressor(_RegressorBase):
    """
    Predict parameter values of ODE models with Elastic Net regression.

    Args:
        X (pandas.DataFrame):
            Index
                Date (pandas.Timestamp): observation date
            Columns
                (int/float): indicators
        y (pandas.DataFrame):
            Index
                Date (pandas.Timestamp): observation date
            Columns
                (int/float) target values
        delay_values (list[int]): list of delay period [days]
        kwargs: keyword arguments of sklearn.model_selection.train_test_split()

    Note:
        If @seed is included in kwargs, this will be converted to @random_state.

    Note:
        default values regarding sklearn.model_selection.train_test_split() are
        test_size=0.2, random_state=0, shuffle=False.
    """
    # Description of regressor
    DESC = "Indicators -> Parameters with Elastic Net"

    def __init__(self, X, y, delay_values, **kwargs):
        super().__init__(X, y, delay_values, **kwargs)

    def _fit(self):
        """
        Fit regression model with training dataset, update self._pipeline and self._param.
        """
        # Model for Elastic Net regression
        tscv = TimeSeriesSplit(n_splits=5).split(self._X_train)
        cv = MultiTaskElasticNetCV(
            alphas=[0, 0.001, 0.01, 0.1, 1, 10, 100, 1000],
            l1_ratio=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            cv=tscv, n_jobs=-1
        )
        # Fit with pipeline
        steps = [
            ("converter", _RateConverter(to_convert=False)),
            ("scaler", MinMaxScaler()),
            ("regressor", cv),
        ]
        pipeline = Pipeline(steps=steps)
        pipeline.fit(self._X_train, self._y_train)
        reg_output = pipeline.named_steps.regressor
        # Update regressor
        self._pipeline = pipeline
        # Intercept/coef
        intercept_df = pd.DataFrame(
            reg_output.coef_, index=self._y_train.columns, columns=self._X_train.columns)
        intercept_df.insert(0, "Intercept", None)
        intercept_df["Intercept"] = reg_output.intercept_
        # Update param
        param_dict = {
            **{k: type(v) for (k, v) in steps},
            "alpha": reg_output.alpha_,
            "l1_ratio": reg_output.l1_ratio_,
            "intercept": intercept_df,
            "coef": intercept_df,
        }
        self._param.update(param_dict)
