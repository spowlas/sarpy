"""Implements coordinate transformations on the WGS 84 ellipsoid"""

import numpy as np

__classification__ = "UNCLASSIFIED"
__author__ = "Wade Schwartzkopf"
__email__ = "Wade.C.Schwartzkopf@nga.mil"

# WGS 84 defining parameters
a = 6378137.0           # Semi-major radius (m)
f = 1/298.257223563     # Flattening
GM = 3986004.418E8      # Earth's gravitational constant (including atmosphere)
w = 7292115.1467E-11    # Angular velocity (radians/second), not including precession
# WGS 84 derived geometric constants
b = a - f*a               # 6356752.3142, Semi-minor radius (m)
e2 = ((a*a)-(b*b))/(a*a)  # 6.69437999014E-3, First eccentricity squared
# TODO: LOW - these constants should probably be hidden - is there any reason why not?


def ecf_to_geodetic(x, y=None, z=None):
    """
    Converts ECF (Earth Centered Fixed) coordinates to geodetic latitude, longitude, and altitude.

    :param x: numpy.ndarray of the form [[x, y, z]] or [x,]
    :param y: None or numpy.ndarray of the form [y,]
    :param z: None or numpy.ndarray of the form [z,]
    :return: if `x` is `Nx3`, then returns `Nx3` numpy.ndarray of the form [latitude, longitude, altitude]
        otherwise return tuple of numpy.ndarrays (latitude, longitude, altitude)

    Implements transform described in *Zhu, J. Conversion of Earth-centered, Earth-fixed coordinates to
    geodetic coordinates. IEEE Transactions on Aerospace and Electronic Systems, 30, 3 (July 1994), 957-962.*
    """

    # TODO: HIGH - unit test this
    x, y, z, componentwise = _normalize_3dinputs(x, y, z)

    # calculate derived constants
    e4 = e2 * e2
    ome2 = 1.0 - e2
    a2 = a * a
    b2 = b * b
    e_b2 = (a2 - b2) / b2

    # calculate intermediates
    z2 = z * z
    r2 = (x * x) + (y * y)
    r = np.sqrt(r2)

    # Check for invalid solution
    valid = ((a * r) * (a * r) + (b * z) * (b * z) > (a2 - b2) * (a2 - b2))
    # Default values for invalid solutions
    lon = np.full(x.shape, np.nan, dtype=np.float64)
    lat = np.full(x.shape, np.nan, dtype=np.float64)
    alt = np.full(x.shape, np.nan, dtype=np.float64)

    # calculate longitude
    lon[valid] = np.rad2deg(np.arctan2(y[valid], x[valid]))

    # calculate intermediates
    f_ = 54.0 * b2 * z2  # not the WGS 84 flattening parameter
    g = r2 + ome2 * z2 - e2 * (a2 - b2)
    c = e4 * f_ * r2 / (g * g * g)
    s = (1.0 + c + np.sqrt(c * c + 2 * c)) ** (1. / 3.)
    templ = s + 1.0 / s + 1.0
    p = f_ / (3.0 * templ * templ * g * g)
    q = np.sqrt(1.0 + 2.0 * e4 * p)
    r0 = -p * e2 * r / (1.0 + q) + np.sqrt(np.abs(0.5 * a2 * (1.0 + 1.0 / q) - p * ome2 * z2 / (q * (1.0 + q)) - 0.5 * p * r2))
    temp2 = r - e2 * r0
    temp22 = temp2 * temp2
    u = np.sqrt(temp22 + z2)
    v = np.sqrt(temp22 + ome2 * z2)
    z0 = b2 * z / (a * v)

    # calculate latitude
    lat[valid] = np.rad2deg(np.arctan2(z[valid] + e_b2 * z0[valid], r[valid]))

    # calculate altitude
    alt[valid] = u[valid] * (1.0 - b2 / (a * v[valid]))
    if componentwise:
        return lat, lon, alt
    else:
        return np.column_stack((lat, lon, alt))


def geodetic_to_ecf(lat, lon=None, alt=None):
    """
    Converts geodetic latitude, longitude, and altitude to ECF (Earth Centered Fixed) coordinates.

    :param lat: numpy.ndarray of the form [[latitude, longitude, altitude]] or [latitude,]
    :param lon: None or numpy.ndarray of the form [longitude,]
    :param alt: None or numpy.ndarray of the form [altitude,]
    :return: if `lat` is `Nx3`, then returns `Nx3` numpy.ndarray of the form [x, y, z]
        otherwise return tuple of numpy.ndarrays (x, y, z)

    Implements transform described in *Zhu, J. Conversion of Earth-centered, Earth-fixed coordinates to
    geodetic coordinates. IEEE Transactions on Aerospace and Electronic Systems, 30, 3 (July 1994), 957-962.*
    """

    # TODO: HIGH - unit test this
    lat, lon, alt, componentwise = _normalize_3dinputs(lat, lon, alt)

    # calculate distance to surface of ellipsoid
    r = a / np.sqrt(1.0 - e2 * np.sin(np.deg2rad(lat)) * np.sin(np.deg2rad(lat)))

    # calculate coordinates
    x = (r + alt) * np.cos(np.deg2rad(lat)) * np.cos(np.deg2rad(lon))
    y = (r + alt) * np.cos(np.deg2rad(lat)) * np.sin(np.deg2rad(lon))
    z = (r + alt - e2 * r) * np.sin(np.deg2rad(lat))

    if componentwise:
        return x, y, z
    else:
        return np.column_stack((x, y, z))


def wgs_84_norm(x, y=None, z=None):
    """
    Computes the normal vector to the WGS_84 ellipsoid at a given point in ECF space.

    :param x: numpy.ndarray of the form [[x, y, z]] or [x,]
    :param y: None or numpy.ndarray of the form [y,]
    :param z: None or numpy.ndarray of the form [z,]
    :return: if `x` is `Nx3`, then returns `Nx3` numpy.ndarray of the form [[x, y, z]]
        otherwise return tuple of numpy.ndarrays (x, y, z)
    """
    # TODO: LOW - the language in this doc string is confusing - WGS 84 ellipsoid in ECF space is nonsense?

    x, y, z, componentwise = _normalize_3dinputs(x, y, z)

    # Calculate normal vector
    x = x/(a**2)
    y = y/(a**2)
    z = z/(b**2)
    mag = np.sqrt(x**2 + y**2 + z**2)
    x = x/mag
    y = y/mag
    z = z/mag

    if componentwise:
        return x, y, z
    else:
        return np.column_stack((x, y, z))


def ric_ecf_mat(rarp, varp, frame_type):
    """
    Computes the ECF transformation matrix for RIC frame.

    :param rarp:
    :param varp:
    :param frame_type: one of 'eci' or 'ecf'?
    :return:
    """
    # TODO: LOW - fix this docstring. These argument names are poor.

    if frame_type.upper() == 'ECI':
        vi = varp + np.cross([0, 0, w], rarp)
    elif frame_type.upper() == 'ECF':
        vi = varp
    else:
        ValueError('frame_type must be one of "ECI", "ECF"')

    r = rarp/np.sqrt(np.sum(rarp*rarp))  # what if it's zero?
    c = np.cross(rarp, vi)
    c = c/np.sqrt(np.sum(c*c))
    i = np.cross(c, r)

    # TODO: HIGH - this should not be a matrix, should be an ndarray
    return np.matrix([r, i, c])


def _normalize_3dinputs(x, y, z):
    """
    Helper function for ensuring compatibility of arguments for module methods.
    :param x: numpy.ndarray `Nx3` or `N`
    :param y: None or one dimensional numpy.ndarray
    :param z: None or one dimensional numpy.ndarray
    :return: (x, y, z, componentwise) where `x,y,z` are one dimensional numpy.ndarrays and `componentwise` is a
        boolean reflecting whether input argument signature of the form `y,z` not `None`
    """

    # TODO: MEDIUM - atleast_1d? Bah.
    x = np.atleast_2d(x)  # Assure a numpy array for componentwise or array versions
    if len(x.shape) > 2:
        raise ValueError("Input argument x is greater than two dimensional - shape = {}".format(x.shape))
    if (x.shape[1] > 1) and (y is None or z is None):
        raise ValueError("If x is two-dimensional, then arguments y,z should be None")
    if (x.shape[1] > 1) and (x.shape[1] != 3):
        raise ValueError("If x is two-dimensional, then it should be N x 3 - shape = {}".format(x.shape))
    if (y is None and z is not None) or (z is None and y is not None):
        raise ValueError("Argument y,z must either both be None, or neither be None")
    if (y is None) and (x.shape[1] != 3):
        raise ValueError("Arguments y, z unspecified, so argument x is assumed (N,3) - shape = {}".format(x.shape))

    if x.shape[1] > 1:
        return x[:, 0], x[:, 1], x[:, 2], False
    else:
        # TODO: MEDIUM - why 2-d? That seems wrong? Should be 1-d?
        return x, np.atleast_2d(y), np.atleast_2d(z), True
