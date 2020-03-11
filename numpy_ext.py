"""
Installation
------------

::

    pip install -U numpy_ext

**Installation for development**::

    git clone https://github.com/3jane/numpy_ext.git
    cd numpy_ext
    pip install -e .[dev]


.. warning::
    Use newest version of pip (>=20)

Operations with nans
--------------------

- :func:`numpy_ext.nans`
- :func:`numpy_ext.drop_na`
- :func:`numpy_ext.fill_na`
- :func:`numpy_ext.fill_not_finite`
- :func:`numpy_ext.prepend_na`

Window operations
-----------------

- :func:`numpy_ext.expanding`
- :func:`numpy_ext.expanding_apply`
- :func:`numpy_ext.rolling`
- :func:`numpy_ext.rolling_apply`

Others
------
- :func:`numpy_ext.apply_map`
- :func:`numpy_ext.expstep_range`

Functions
---------

"""
from typing import Callable, Any, Union, Generator, Tuple, List

import numpy as np
from joblib import Parallel, delayed

Number = Union[int, float]


def expstep_range(
    start: Number,
    end: Number,
    min_step: Number = 1,
    step_mult: Number = 1,
    round_func: Callable = None
) -> np.ndarray:
    """
    Return spaced values within a given interval. Step is increased by a multiplier with each iteration.
    Parameters
    ----------
    start : int or float
        Start of interval. The interval includes this value.
    end : int or float
        End of interval. The interval _does_ include this value.
    min_step : int or float, optional
        Minimal spacing between values. Should be bigger than 0. Default is 1
    step_mult : int or float, optional
        Multiplier by which to increase step with each iteration. Should be bigger than 0. Default is 1
    round_func: Callable, optional
        Vectorized rounding function, e.g. np.ceil, np.floor, etc.
    Returns
    -------
    np.ndarray
        Array of exponentially spaced values.
    Examples
    --------
    >>> expstep_range(1, 100, min_step=1, step_mult=1.5)
    array([ 1.        ,  2.        ,  3.5       ,  5.75      ,  9.125     ,
           14.1875    , 21.78125   , 33.171875  , 50.2578125 , 75.88671875])
    >>> expstep_range(1, 100, min_step=1, step_mult=1.5, round_func=np.ceil)
    array([ 1.,  2.,  4.,  6., 10., 15., 22., 34., 51., 76.])
    >>> expstep_range(start=-1, end=-100, min_step=1, step_mult=1.5)
    array([ -1.        ,  -2.        ,  -3.5       ,  -5.75      ,
            -9.125     , -14.1875    , -21.78125   , -33.171875  ,
           -50.2578125 , -75.88671875])

    Generate array of int`s
    >>> expstep_range(start=100, end=1, min_step=1, step_mult=1.5, round_func=lambda arr: arr.astype(np.int))
    array([100,  99,  97,  95,  91,  86,  79,  67,  50,  25])
    """
    if step_mult <= 0:
        raise ValueError("mult_step should be bigger than 0")

    if min_step <= 0:
        raise ValueError("min_step should be bigger than 0")

    last = start
    values = []
    step = min_step

    sign = 1 if start < end else -1

    while start < end and last < end or start > end and last > end:
        values.append(last)
        last += max(step, min_step) * sign
        step = abs(step * step_mult)

    values = np.array(values)
    if not round_func:
        return values

    values = np.array(round_func(values))
    _, idx = np.unique(values, return_index=True)
    return values[np.sort(idx)]


def apply_map(func: Callable, array: Union[List, np.ndarray]) -> np.ndarray:
    """
    Apply function for each array elements.
    Parameters
    ----------
    func : Callable
        This function should accept one argument
    array : Union[List, np.ndarray]
        Input array. Lists would converts to np.ndarray
    Returns
    -------
    np.ndarray
        Output ndarray
    Examples
    --------
    >>> apply_map(lambda x: 0 if x < 3 else 1, [[2, 2], [3, 3]])
    array([[0, 0],
           [1, 1]])
    """
    array = np.array(array)
    array_view = array.flat
    array_view[:] = [func(x) for x in array_view]
    return array


#############################
# Operations with nans
#############################


def nans(shape: Union[int, Tuple[int]]) -> np.ndarray:
    """
    Return a new array of given shape and type, filled with np.nans.
    Parameters
    ----------
    shape : int or tuple of ints
        Shape of the new array, e.g., (2, 3) or 2.
    Returns
    -------
    np.ndarray
        Array of np.nans with the given shape.
    Examples
    --------
    >>> nans(3)
    array([nan, nan, nan])
    >>> nans((2, 2))
    array([[nan, nan],
           [nan, nan]])
    """
    arr = np.empty(shape)
    arr.fill(np.nan)
    return arr


def drop_na(array: np.ndarray) -> np.ndarray:
    """
    Return a new array without nans
    Parameters
    ----------
    array : np.ndarray
        Input array
    Returns
    -------
    np.ndarray
        New array without nans
    Examples
    --------
    >>> drop_na(np.array([np.nan, 1, 2]))
    array([1., 2.])
    """
    return array[~np.isnan(array)]


def fill_na(array: np.ndarray, value: Any) -> np.ndarray:
    """
    Return a new array with nans replaced with given values
    Parameters
    ----------
    array : np.ndarray
        Input array
    value : Any
        Value to replace nans with
    Returns
    -------
    np.ndarray
        New array with nans replaced with given values
    Examples
    --------
    >>> fill_na(np.array([np.nan, 1, 2]), -1)
    array([-1.,  1.,  2.])
    """
    ar = array.copy()
    ar[np.isnan(ar)] = value
    return ar


def fill_not_finite(array: np.ndarray, value: Any = 0) -> np.ndarray:
    """
    Return a new array with nans and infs replaced with given values
    Parameters
    ----------
    array : np.ndarray
        Input array
    value : Any, optional
        Value to replace nans and infs with. Default is 0
    Returns
    -------
    np.ndarray
        New array with nans and infs replaced with given values
    Examples
    --------
    >>> fill_not_finite(np.array([np.nan, np.inf, 1, 2]), 99)
    array([99., 99.,  1.,  2.])
    """
    ar = array.copy()
    ar[~np.isfinite(array)] = value
    return ar


def prepend_na(array: np.ndarray, size: int) -> np.ndarray:
    """
    Return a new array with nans added at the beginning.
    Parameters
    ----------
    array : np.ndarray
        Input array
    size : int
        How many elements to add
    Returns
    -------
    np.ndarray
        New array with nans added at the beginning
    Examples
    --------
    >>> prepend_na(np.array([1, 2]), 2)
    array([nan, nan,  1.,  2.])
    """
    return np.hstack((nans(size), array))


#############################
# window operations
#############################


def rolling(
    array: np.ndarray,
    window: int,
    skip_nans: bool = False,
    as_array: bool = False
) -> Union[Generator[np.ndarray, None, None], np.ndarray]:
    """
    Return rolling window array or generator
    Parameters
    ----------
    array : np.ndarray
        Input array
    window : int
        Window size
    skip_nans : bool, optional
        If True skip's first `window - 1` nans. Default is False
    as_array : bool, optional
        If True than returns ndarray otherwise generator. Default is False
    Returns
    -------
    np.ndarray or Generator[np.ndarray, None, None]
        Rolling window matrix or generator
    Examples
    --------
    >>> rolling(np.array([1, 2, 3, 4, 5]), 2, as_array=True)
    array([[nan,  1.],
           [ 1.,  2.],
           [ 2.,  3.],
           [ 3.,  4.],
           [ 4.,  5.]])

    Usage with numpy functions
    >>> arr = rolling(np.array([1, 2, 3, 4, 5]), 2, as_array=True)
    >>> np.sum(arr, axis=1)
    array([nan,  3.,  5.,  7.,  9.])
    """
    if not isinstance(window, int):
        raise TypeError(f'Wrong window type ({type(window)}) int expected')

    if array.size < window:
        raise ValueError('array.size should be bigger than window')

    def rows_gen():
        if not skip_nans:
            yield from (prepend_na(array[:i + 1], (window - 1) - i) for i in np.arange(window - 1))

        yield from (array[i:i + window] for i in np.arange(array.size - (window - 1)))

    return np.array([row for row in rows_gen()]) if as_array else rows_gen()


def rolling_apply(func: Callable, window: int, *arrays: np.ndarray, n_jobs: int = 1, **kwargs) -> np.ndarray:
    """
    The rolling function's apply function
    Parameters
    ----------
    func : Callable
        Apply function
    window : int
        Window size
    *arrays : list
        List of input arrays
    n_jobs : int, optional
        Parallel tasks count for joblib. Default is 1
    **kwargs : dict
        Input parameters (passed to func)
    Returns
    -------
    np.ndarray
    Examples
    --------
    >>> arr = np.array([1, 2, 3, 4, 5])
    >>> rolling_apply(sum, 2, arr)
    array([nan,  3.,  5.,  7.,  9.])
    >>> arr2 = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
    >>> func = lambda a1, a2, k: (sum(a1) + max(a2)) * k
    >>> rolling_apply(func, 2, arr, arr2, k=-1)
    array([  nan,  -5.5,  -8.5, -11.5, -14.5])
    """
    if not isinstance(window, int):
        raise TypeError(f'Wrong window type ({type(window)}) int expected')

    if max(len(x.shape) for x in arrays) != 1:
        raise ValueError("Wrong array shape. Supported only 1D arrays")

    if len({array.size for array in arrays}) != 1:
        raise ValueError("Arrays must be the same length")

    def _apply_func_to_arrays(idxs):
        return func(*[array[idxs.astype(np.int)] for array in arrays], **kwargs)

    rolls = rolling(np.arange(len(arrays[0])), window, skip_nans=True)

    if n_jobs == 1:
        arr = [_apply_func_to_arrays(idxs) for idxs in rolls]
    else:
        arr = Parallel(n_jobs=n_jobs)(delayed(_apply_func_to_arrays)(idxs) for idxs in rolls)

    return prepend_na(arr, size=window - 1)


def expanding(
    array: np.ndarray,
    min_periods: int = 1,
    skip_nans: bool = True,
    as_array: bool = False
) -> Union[Generator[np.ndarray, None, None], np.ndarray]:
    """
    Provide expanding transformations
    Parameters
    ----------
    array : np.ndarray
        Input array
    min_periods : int, optional
        Minimal size of expanding window. Default is 1
    skip_nans : bool, optional
        If True skip's first nans (rows with size lower than min_periods). Default is True
    as_array : bool, optional
        If True than returns ndarray otherwise generator. Default is False
    Returns
    -------
    np.ndarray or Generator[np.ndarray, None, None]
    Examples
    --------
    >>> expanding(np.array([1, 2, 3, 4, 5]), 3, as_array=True)
    array([array([1, 2, 3]), array([1, 2, 3, 4]), array([1, 2, 3, 4, 5])],
          dtype=object)
    """
    if not isinstance(min_periods, int):
        raise TypeError(f'Wrong min_periods type ({type(min_periods)}) int expected')

    if array.size < min_periods:
        raise ValueError('array.size should be bigger than min_periods')

    def rows_gen():
        if not skip_nans:
            yield from (nans(i) for i in np.arange(1, min_periods))

        yield from (array[:i] for i in np.arange(min_periods, array.size + 1))

    return np.array([row for row in rows_gen()]) if as_array else rows_gen()


def expanding_apply(func: Callable, min_periods: int, *arrays: np.ndarray, n_jobs: int = 1, **kwargs) -> np.ndarray:
    """
    The expanding function's apply function
    Parameters
    ----------
    func : Callable
        Apply function
    min_periods : int
        Minimal size of expanding window
    *arrays : list
        List of input arrays
    n_jobs : int, optional
        Parallel tasks count for joblib. Default is 1
    **kwargs : dict
        Input parameters (passed to func)
    Returns
    -------
    np.ndarray
    Examples
    --------
    >>> arr = np.array([1, 2, 3, 4, 5])
    >>> expanding_apply(sum, 2, arr)
    array([nan,  3.,  6., 10., 15.])
    >>> arr2 = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
    >>> func = lambda a1, a2, k: (sum(a1) + max(a2)) * k
    >>> expanding_apply(func, 2, arr, arr2, k=-1)
    array([  nan,  -5.5,  -9.5, -14.5, -20.5])
    """
    if not isinstance(min_periods, int):
        raise TypeError(f'Wrong min_periods type ({type(min_periods)}) int expected')

    if max(len(x.shape) for x in arrays) != 1:
        raise ValueError("Supported only 1-D arrays")

    if len({array.size for array in arrays}) != 1:
        raise ValueError("Arrays must be the same length")

    def _apply_func_to_arrays(idxs):
        return func(*[array[idxs.astype(np.int)] for array in arrays], **kwargs)

    rolls = expanding(np.arange(len(arrays[0])), min_periods, skip_nans=True)
    if n_jobs == 1:
        arr = [_apply_func_to_arrays(idxs) for idxs in rolls]
    else:
        arr = Parallel(n_jobs=n_jobs)(delayed(_apply_func_to_arrays)(idxs) for idxs in rolls)

    return prepend_na(arr, size=min_periods - 1)
