import math


def round_to_significant_digits(x, num_dig_digits):
    """Round given number to given number of significant digits

    Parameters
    ----------
    x: flost
        Number to be rounded
    num_dig_digits: int
        Number of significant digits


    Returns
    -------
    Rounded number.

    For NaN, NaN is returned.
    """
    if math.isnan(x):
        return x
    try:
        return round(x, num_dig_digits - int(math.floor(math.log10(abs(x)))) - 1)
    except ValueError:
        return x
