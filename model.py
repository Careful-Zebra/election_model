import pandas as pd
from sklearn.metrics import root_mean_squared_error
import numpy as np

TRAINING_YEARS = [i for i in range(1978, 2012)]
VALIDATION_YEARS = [i for i in range(2012, 2018)]
TESTING_YEARS = [i for i in range(2018, 2026)]
ERROR_WEIGHT = 0.8

#metric: share of races with the wrong sign plus rmse times error weight of 0.8 (slightly favour getting winner of light right)
def score(actual, predicted) -> dict[str, float]:

    #input validation
    predicted = np.asarray(predicted)
    actual = np.asarray(actual)
    assert len(predicted) == len(actual), "Length mismatch between predicted and actual, predicted: " + str(len(predicted)) + ", actual: " + str(len(actual))
    assert not np.isnan(predicted).any(), "Predicted contains NaN(s)"
    assert not np.isnan(actual).any(), "Actual contains NaN(s)"

    results = {}
    n = len(predicted)
    assert n > 0, "N is zero"
    results['n'] = float(n)

    #get races with wrong sign
    mults = actual * predicted
    wrong_sign = np.sum(mults <= 0)
    results['wrong_sign'] = float(wrong_sign)

    rmse = root_mean_squared_error(actual, predicted)
    results['rmse'] = rmse

    score = (wrong_sign / n) + (rmse * ERROR_WEIGHT)
    results['score'] = float(score)

    return results

