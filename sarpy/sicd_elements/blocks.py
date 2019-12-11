"""
Basic building blocks for SICD standard.
"""

from .base import _get_node_value, _create_text_node, _create_new_node, Serializable, DEFAULT_STRICT, \
    _StringDescriptor, _StringEnumDescriptor, _IntegerDescriptor, _FloatDescriptor, _FloatModularDescriptor, \
    _SerializableDescriptor, _parse_serializable_array

from collections import OrderedDict

import numpy
import scipy
if scipy.__version__ >= '1.0':
    from scipy.special import comb
else:
    from scipy.misc import comb


__classification__ = "UNCLASSIFIED"


class ParameterType(Serializable):
    """A parameter - just a name attribute and associated value"""
    _fields = ('name', 'value')
    _required = _fields
    _set_as_attribute = ('name', )
    # descriptor
    name = _StringDescriptor(
        'name', _required, strict=False, docstring='The name.')  # type: str
    value = _StringDescriptor('value', _required, strict=False, docstring='The value')  # type: str

    def __init__(self, value=None, name=None, **kwargs):
        """
        Parameters
        ----------
        value : str
        name : str
        kwargs : dict
        """

        self.name = name
        self.value = value
        super(ParameterType, self).__init__(**kwargs)

    @classmethod
    def from_node(cls, node, kwargs=None):
        return cls(name=node.attrib['name'], value=_get_node_value(node))

    def to_node(self, doc, tag, parent=None, strict=DEFAULT_STRICT, exclude=()):
        # we have to short-circuit the super call here, because this is a really primitive element
        node = _create_text_node(doc, tag, self.value, parent=parent)
        node.attrib['name'] = self.name
        return node


##########
# Geographical coordinates

class XYZType(Serializable):
    """A spatial point in ECF coordinates."""
    _fields = ('X', 'Y', 'Z')
    _required = _fields
    _numeric_format = {}  # TODO: desired precision? 'X': '0.8f', 'Y': '0.8f', 'Z': '0.8f'
    # descriptors
    X = _FloatDescriptor(
        'X', _required, strict=True,
        docstring='The X attribute. Assumed to ECF or other, similar coordinates.')  # type: float
    Y = _FloatDescriptor(
        'Y', _required, strict=True,
        docstring='The Y attribute. Assumed to ECF or other, similar coordinates.')  # type: float
    Z = _FloatDescriptor(
        'Z', _required, strict=True,
        docstring='The Z attribute. Assumed to ECF or other, similar coordinates.')  # type: float

    def __init__(self, coords=None, X=None, Y=None, Z=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [X, Y, Z]
        X : float
        Y : float
        Z : float
        kwargs : dict
        """

        if isinstance(coords, (numpy.ndarray, list, tuple)):
            if len(coords) >= 3:
                self.X, self.Y, self.Z = coords[0], coords[1], coords[2]
            else:
                raise ValueError('Expected coords to be of length 3, and received {}'.format(coords))
        else:
            self.X, self.Y, self.Z = X, Y, Z
        super(XYZType, self).__init__(**kwargs)

    def get_array(self, dtype=numpy.float64):
        """Gets an array representation of the class instance.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return

        Returns
        -------
        numpy.ndarray
            array of the form [X,Y,Z]
        """

        return numpy.array([self.X, self.Y, self.Z], dtype=dtype)


class LatLonType(Serializable):
    """A two-dimensional geographic point in WGS-84 coordinates."""
    _fields = ('Lat', 'Lon')
    _required = _fields
    _numeric_format = {'Lat': '2.8f', 'Lon': '3.8f'}
    # descriptors
    Lat = _FloatDescriptor(
        'Lat', _required, strict=True,
        docstring='The latitude attribute. Assumed to be WGS-84 coordinates.')  # type: float
    Lon = _FloatDescriptor(
        'Lon', _required, strict=True,
        docstring='The longitude attribute. Assumed to be WGS-84 coordinates.')  # type: float

    def __init__(self, coords=None, Lat=None, Lon=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        Lat : float
        Lon : float
        kwargs : dict
        """
        if isinstance(coords, (numpy.ndarray, list, tuple)):
            if len(coords) >= 2:
                self.Lat, self.Lon = coords[0], coords[1]
            else:
                raise ValueError('Expected coords to be of length 2, and received {}'.format(coords))
        else:
            self.Lat, self.Lon = Lat, Lon
        super(LatLonType, self).__init__(**kwargs)

    def get_array(self, order='LON', dtype=numpy.float64):
        """Gets an array representation of the data.

        Parameters
        ----------
        order : str
            Determines array order. 'LAT' yields [Lat, Lon], and anything else yields  [Lon, Lat].
        dtype : numpy.dtype
            data type of the return

        Returns
        -------
        numpy.ndarray
            data array with appropriate entry order
        """

        if order.upper() == 'LAT':
            return numpy.array([self.Lat, self.Lon], dtype=dtype)
        else:
            return numpy.array([self.Lon, self.Lat], dtype=dtype)


class LatLonArrayElementType(LatLonType):
    """An geographic point in an array"""
    _fields = ('Lat', 'Lon', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    _numeric_format = {'Lat': '2.8f', 'Lon': '3.8f'}
    index = _IntegerDescriptor(
        'index', _required, strict=False, docstring="The array index")  # type: int

    def __init__(self, coords=None, Lat=None, Lon=None, index=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        Lat : float
        Lon : float
        index : int
        kwargs : dict
        """

        self.index = index
        super(LatLonArrayElementType, self).__init__(coords=coords, Lat=Lat, Lon=Lon, **kwargs)


class LatLonRestrictionType(LatLonType):
    """A two-dimensional geographic point in WGS-84 coordinates."""
    _fields = ('Lat', 'Lon')
    _required = _fields
    _numeric_format = {'Lat': '2.8f', 'Lon': '3.8f'}
    # descriptors
    Lat = _FloatModularDescriptor(
        'Lat', 90.0, _required, strict=True,
        docstring='The latitude attribute. Assumed to be WGS-84 coordinates.')  # type: float
    Lon = _FloatModularDescriptor(
        'Lon', 180.0, _required, strict=True,
        docstring='The longitude attribute. Assumed to be WGS-84 coordinates.')  # type: float

    def __init__(self, coords=None, Lat=None, Lon=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        Lat : float
        Lon : float
        kwargs : dict
        """

        super(LatLonRestrictionType, self).__init__(coords=coords, Lat=Lat, Lon=Lon, **kwargs)


class LatLonHAEType(LatLonType):
    """A three-dimensional geographic point in WGS-84 coordinates."""
    _fields = ('Lat', 'Lon', 'HAE')
    _required = _fields
    _numeric_format = {'Lat': '2.8f', 'Lon': '3.8f', 'HAE': '0.8f'}
    # descriptors
    HAE = _FloatDescriptor(
        'HAE', _required, strict=True,
        docstring='The Height Above Ellipsoid (in meters) attribute. Assumed to be '
                  'WGS-84 coordinates.')  # type: float

    def __init__(self, coords=None, Lat=None, Lon=None, HAE=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon, HAE]
        Lat : float
        Lon : float
        HAE : float
        kwargs : dict
        """
        if isinstance(coords, (numpy.ndarray, list, tuple)):
            if len(coords) >= 3:
                Lat, Lon, self.HAE = coords[0], coords[1], coords[2]
            else:
                raise ValueError('Expected coords to be of length 3, and received {}'.format(coords))
        else:
            self.HAE = HAE
        super(LatLonHAEType, self).__init__(Lat=Lat, Lon=Lon, **kwargs)

    def get_array(self, order='LON', dtype=numpy.float64):
        """Gets an array representation of the data.

        Parameters
        ----------
        order : str
            Determines array order. 'LAT' yields [Lat, Lon, HAE], and anything else yields  [Lon, Lat, HAE].
        dtype : numpy.dtype
            data type of the return

        Returns
        -------
        numpy.ndarray
            data array with appropriate entry order
        """

        if order.upper() == 'LAT':
            return numpy.array([self.Lat, self.Lon, self.HAE], dtype=dtype)
        else:
            return numpy.array([self.Lon, self.Lat, self.HAE], dtype=dtype)


class LatLonHAERestrictionType(LatLonHAEType):
    _fields = ('Lat', 'Lon', 'HAE')
    _required = _fields
    """A three-dimensional geographic point in WGS-84 coordinates."""
    Lat = _FloatModularDescriptor(
        'Lat', 90.0, _required, strict=True,
        docstring='The latitude attribute. Assumed to be WGS-84 coordinates.')  # type: float
    Lon = _FloatModularDescriptor(
        'Lon', 180.0, _required, strict=True,
        docstring='The longitude attribute. Assumed to be WGS-84 coordinates.')  # type: float

    def __init__(self, coords=None, Lat=None, Lon=None, HAE=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon, HAE]
        Lat : float
        Lon : float
        HAE : float
        kwargs : dict
        """

        super(LatLonHAERestrictionType, self).__init__(coords=coords, Lat=Lat, Lon=Lon, HAE=HAE, **kwargs)


class LatLonCornerType(LatLonType):
    """A two-dimensional geographic point in WGS-84 coordinates representing a collection area box corner point."""
    _fields = ('Lat', 'Lon', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # descriptors
    index = _IntegerDescriptor(
        'index', _required, strict=True, bounds=(0, 4),
        docstring='The integer index. This represents a clockwise enumeration of '
                  'the rectangle vertices wrt the frame of reference of the collector. '
                  'Should be 1-4, but 0-3 may be permissible.')  # type: int

    def __init__(self, coords=None, Lat=None, Lon=None, index=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        Lat : float
        Lon : float
        index : int
        kwargs : dict
        """
        self.index = index
        super(LatLonCornerType, self).__init__(coords=coords, Lat=Lat, Lon=Lon, **kwargs)


class LatLonCornerStringType(LatLonType):
    """A two-dimensional geographic point in WGS-84 coordinates representing a collection area box corner point."""
    _fields = ('Lat', 'Lon', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # other specific class variable
    _CORNER_VALUES = ('1:FRFC', '2:FRLC', '3:LRLC', '4:LRFC')
    # descriptors
    index = _StringEnumDescriptor(
        'index', _CORNER_VALUES, _required, strict=True,
        docstring="The string index.")  # type: str

    def __init__(self, coords=None, Lat=None, Lon=None, index=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        Lat : float
        Lon : float
        index : str
        kwargs : dict
        """
        self.index = index
        super(LatLonCornerStringType, self).__init__(coords=coords, Lat=Lat, Lon=Lon, **kwargs)


class LatLonHAECornerRestrictionType(LatLonHAERestrictionType):
    """A three-dimensional geographic point in WGS-84 coordinates. Represents a collection area box corner point."""
    _fields = ('Lat', 'Lon', 'HAE', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # descriptors
    index = _IntegerDescriptor(
        'index', _required, strict=False, bounds=(0, 4),
        docstring='The integer index. This represents a clockwise enumeration of the '
                  'rectangle vertices wrt the frame of reference of the collector. '
                  'Should be 1-4, but 0-3 may be permissible.')  # type: int

    def __init__(self, coords=None, Lat=None, Lon=None, HAE=None, index=None, **kwargs):
        """

        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon, HAE]
        Lat : float
        Lon : float
        HAE : float
        index : int
        kwargs : dict
        """
        self.index = index
        super(LatLonHAECornerRestrictionType, self).__init__(coords=coords, Lat=Lat, Lon=Lon, HAE=HAE, **kwargs)


class LatLonHAECornerStringType(LatLonHAEType):
    """A three-dimensional geographic point in WGS-84 coordinates. Represents a collection area box corner point."""
    _fields = ('Lat', 'Lon', 'HAE', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    _CORNER_VALUES = ('1:FRFC', '2:FRLC', '3:LRLC', '4:LRFC')
    # descriptors
    index = _StringEnumDescriptor(
        'index', _CORNER_VALUES, _required, strict=True, docstring="The string index.")  # type: str

    def __init__(self, coords=None, Lat=None, Lon=None, HAE=None, index=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Lat, Lon, HAE]
        Lat : float
        Lon : float
        HAE : float
        index : str
        kwargs : dict
        """
        self.index = index
        super(LatLonHAECornerStringType, self).__init__(coords=coords, Lat=Lat, Lon=Lon, HAE=HAE, **kwargs)


#######
# Image space coordinates


class RowColType(Serializable):
    """A row and column attribute container - used as indices into array(s)."""
    _fields = ('Row', 'Col')
    _required = _fields
    Row = _IntegerDescriptor(
        'Row', _required, strict=True, docstring='The Row attribute.')  # type: int
    Col = _IntegerDescriptor(
        'Col', _required, strict=True, docstring='The Column attribute.')  # type: int

    def __init__(self, coords=None, Row=None, Col=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Row, Col]
        Row : int
        Col : int
        kwargs : dict
        """
        if isinstance(coords, (numpy.ndarray, list, tuple)):
            if len(coords) >= 2:
                self.Row, self.Col = coords[0], coords[1]
            else:
                raise ValueError('Expected coords to be of length 2, and received {}'.format(coords))
        else:
            self.Row, self.Col = Row, Col
        super(RowColType, self).__init__(**kwargs)

    def get_array(self, dtype=numpy.int64):
        """Gets an array representation of the class instance.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return

        Returns
        -------
        numpy.ndarray
            array of the form [Row, Col]
        """

        return numpy.array([self.Row, self.Col], dtype=dtype)


class RowColArrayElement(RowColType):
    """A array element row and column attribute container - used as indices into other array(s)."""
    # Note - in the SICD standard this type is listed as RowColvertexType. This is not a descriptive name
    # and has an inconsistency in camel case
    _fields = ('Row', 'Col', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # descriptors
    index = _IntegerDescriptor(
        'index', _required, strict=False, docstring='The array index attribute.')  # type: int

    def __init__(self, coords=None, Row=None, Col=None, index=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
            assumed [Row, Col]
        Row : int
        Col : int
        index : int
        kwargs : dict
        """
        self.index = index
        super(RowColArrayElement, self).__init__(coords=coords, Row=Row, Col=Col, **kwargs)


###############
# Polynomial Types


class Poly1DType(Serializable):
    """Represents a one-variable polynomial, defined by one-dimensional coefficient array."""
    _fields = ('Coefs', 'order1')
    _required = ('Coefs', )
    _numeric_format = {'Coefs': '0.8f'}
    # other class variables
    _Coefs = None

    def __init__(self, Coefs=None, **kwargs):
        """
        Parameters
        ----------
        Coefs : numpy.ndarray|tuple|list
        kwargs : dict
        """
        self.Coefs = Coefs
        super(Poly1DType, self).__init__(**kwargs)

    @property
    def order1(self):
        """
        int: The order1 attribute [READ ONLY]  - that is, largest exponent presented in the monomial terms of coefs.
        """

        return self.Coefs.size - 1

    @property
    def Coefs(self):
        """
        numpy.ndarray: The one-dimensional polynomial coefficient array of dtype=float64. Assignment object must be a
        one-dimensional numpy.ndarray, or naively convertible to one.
        """

        return self._Coefs

    @Coefs.setter
    def Coefs(self, value):
        if value is None:
            raise ValueError('The coefficient array for a Poly1DType instance must be defined.')

        if isinstance(value, (list, tuple)):
            value = numpy.array(value, dtype=numpy.float64)

        if not isinstance(value, numpy.ndarray):
            raise ValueError(
                'Coefs for class Poly1D must be a list or numpy.ndarray. Received type {}.'.format(type(value)))
        elif len(value.shape) != 1:
            raise ValueError(
                'Coefs for class Poly1D must be one-dimensional. Received numpy.ndarray '
                'of shape {}.'.format(value.shape))
        elif not value.dtype == numpy.float64:
            value = numpy.cast[numpy.float64](value)
        self._Coefs = value

    def __call__(self, x):
        """
        Evaluate the polynomial at points `x`. This passes `x` straight through to :func:`polyval` of
        :module:`numpy.polynomial.polynomial`.

        Parameters
        ----------
        x : numpy.ndarray
            The point(s) at which to evaluate.

        Returns
        -------
        numpy.ndarray
        """

        return numpy.polynomial.polynomial.polyval(x, self._Coefs)

    def derivative(self, der_order=1, return_poly=False):
        """
        Calculate the `der_order` derivative of the polynomial.

        Parameters
        ----------
        der_order : int
            the order of the derivative
        return_poly : bool
            return a Poly1DType if True, otherwise return the coefficient array.

        Returns
        -------
        Poly1DType|numpy.ndarray
        """

        coefs = numpy.polynomial.polynomial.polyder(self._Coefs, der_order)
        if return_poly:
            return Poly1DType(Coefs=coefs)
        return coefs

    def derivative_eval(self, x, der_order=1):
        """
        Evaluate the `der_order` derivative of the polynomial at points `x`. This uses the
        functionality presented in :module:`numpy.polynomial.polynomial`.

        Parameters
        ----------
        x : numpy.ndarray
            The point(s) at which to evaluate.
        der_order : int
            The derivative.
        Returns
        -------
        numpy.ndarray
        """

        coefs = self.derivative(der_order=der_order, return_poly=False)
        return numpy.polynomial.polynomial.polyval(x, coefs)

    def shift(self, t_0, alpha=1, return_poly=False):
        r"""
        Transform a polynomial with respect to a affine shift in the coordinate system.
        That is, :math:`P(x) = Q(\alpha\cdot(t-t_0))`.

        Be careful to follow the convention that the transformation parameters express the *current coordinate system*
        as a shifted, **and then** scaled version of the *new coordinate system*. If the new coordinate is
        :math:`t = \beta\cdot x - t_0`, then :math:`x = (t - t_0)/\beta`, and :math:`\alpha = 1/\beta`.

        Parameters
        ----------
        t_0 : float
            the **current center coordinate** in the **new coordinate system.**
            That is, `x=0` when `t=t_0`.

        alpha : float
            the scale. That is, when `t = t0 + 1`, then `x = alpha`. **NOTE:** it is assumed that the
            coordinate system is re-centered, and **then** scaled.

        return_poly : bool
            if `True`, a Poly1DType object be returned, otherwise the coefficients array is returned.

        Returns
        -------
        Poly1DType|numpy.ndarray
        """

        coefs = self._Coefs

        if t_0 == 0:
            out = numpy.copy(coefs)
        else:
            out = numpy.zeros(coefs.shape, dtype=numpy.float64)
            siz = out.size
            for i in range(siz):
                N = numpy.arange(i, siz)
                K = N-i
                out[i] = numpy.sum(comb(N, K)*coefs[i:]*numpy.power(-t_0, K))
                # This is just the binomial expansion and gathering terms

        if alpha != 1:
            out *= numpy.power(alpha, numpy.arange(out.size))

        if return_poly:
            return Poly1DType(Coefs=out)
        else:
            return out

    @classmethod
    def from_node(cls, node, kwargs=None):
        """For XML deserialization.

        Parameters
        ----------
        node : ElementTree.Element
            dom element for serialized class instance
        kwargs : None|dict
            `None` or dictionary of previously serialized attributes. For use in inheritance call, when certain
            attributes require specific deserialization.

        Returns
        -------
        Serializable
            corresponding class instance
        """

        order1 = int(node.attrib['order1'])
        coefs = numpy.zeros((order1+1, ), dtype=numpy.float64)
        for cnode in node.findall('Coef'):
            ind = int(cnode.attrib['exponent1'])
            val = float(_get_node_value(cnode))
            coefs[ind] = val
        return cls(Coefs=coefs)

    def to_node(self, doc, tag, parent=None, strict=DEFAULT_STRICT, exclude=()):
        """For XML serialization, to a dom element.

        Parameters
        ----------
        doc : ElementTree.ElementTree
            The xml Document
        tag : None|str
            The tag name. Defaults to the value of `self._tag` and then the class name if unspecified.
        parent : None|ElementTree.Element
            The parent element. Defaults to the document root element if unspecified.
        strict : bool
            If `True`, then raise an Exception (of appropriate type) if the structure is not valid.
            Otherwise, log a hopefully helpful message.
        exclude : tuple
            Attribute names to exclude from this generic serialization. This allows for child classes
            to provide specific serialization for special properties, after using this super method.

        Returns
        -------
        ElementTree.Element
            The constructed dom element, already assigned to the parent element.
        """

        if parent is None:
            parent = doc.getroot()

        node = _create_new_node(doc, tag, parent=parent)
        node.attrib['order1'] = str(self.order1)
        fmt_func = self._get_formatter('Coef')
        for i, val in enumerate(self.Coefs):
            # if val != 0.0:  # should we serialize it sparsely?
            cnode = _create_text_node(doc, 'Coef', fmt_func(val), parent=node)
            cnode.attrib['exponent1'] = str(i)
        return node

    def to_dict(self, strict=DEFAULT_STRICT, exclude=()):
        """For json serialization.

        Parameters
        ----------
        strict : bool
            If `True`, then raise an Exception (of appropriate type) if the structure is not valid.
            Otherwise, log a hopefully helpful message.
        exclude : tuple
            Attribute names to exclude from this generic serialization. This allows for child classes
            to provide specific serialization for special properties, after using this super method.

        Returns
        -------
        OrderedDict
            dict representation of class instance appropriate for direct json serialization.
        """

        out = OrderedDict()
        out['Coefs'] = self.Coefs.tolist()
        return out


class Poly2DType(Serializable):
    """Represents a one-variable polynomial, defined by two-dimensional coefficient array."""
    _fields = ('Coefs', 'order1', 'order2')
    _required = ('Coefs', )
    _numeric_format = {'Coefs': '0.8f'}
    # other class variables
    _Coefs = None

    def __init__(self, Coefs=None, **kwargs):
        """
        Parameters
        ----------
        Coefs : numpy.ndarray|list|tuple
        kwargs : dict
        """
        self.Coefs = Coefs
        super(Poly2DType, self).__init__(**kwargs)

    def __call__(self, x, y):
        """
        Evaluate a polynomial at points [`x`, `y`]. This passes `x`,`y` straight through to :func:`polyval2d` of
        :module:`numpy.polynomial.polynomial`.

        Parameters
        ----------
        x : numpy.ndarray
            The first dependent variable of point(s) at which to evaluate.
        y : numpy.ndarray
            The second dependent variable of point(s) at which to evaluate.

        Returns
        -------
        numpy.ndarray
        """

        return numpy.polynomial.polynomial.polyval2d(x, y, self.Coefs)

    @property
    def order1(self):
        """
        int: The order1 attribute [READ ONLY]  - that is, largest exponent1 presented in the monomial terms of coefs.
        """

        return self.Coefs.shape[0] - 1

    @property
    def order2(self):
        """
        int: The order1 attribute [READ ONLY]  - that is, largest exponent2 presented in the monomial terms of coefs.
        """

        return self.Coefs.shape[1] - 1

    @property
    def Coefs(self):
        """
        numpy.ndarray: The two-dimensional polynomial coefficient array of dtype=float64. Assignment object must be a
        two-dimensional numpy.ndarray, or naively convertible to one.
        """

        return self._Coefs

    @Coefs.setter
    def Coefs(self, value):
        if value is None:
            raise ValueError('The coefficient array for a Poly2DType instance must be defined.')

        if isinstance(value, (list, tuple)):
            value = numpy.array(value, dtype=numpy.float64)

        if not isinstance(value, numpy.ndarray):
            raise ValueError(
                'Coefs for class Poly2D must be a list or numpy.ndarray. Received type {}.'.format(type(value)))
        elif len(value.shape) != 2:
            raise ValueError(
                'Coefs for class Poly2D must be two-dimensional. Received numpy.ndarray '
                'of shape {}.'.format(value.shape))
        elif not value.dtype == numpy.float64:
            value = numpy.cast[numpy.float64](value)
        self._Coefs = value

    @classmethod
    def from_node(cls, node, kwargs=None):
        """For XML deserialization.

        Parameters
        ----------
        node : ElementTree.Element
            dom element for serialized class instance
        kwargs : None|dict
            `None` or dictionary of previously serialized attributes. For use in inheritance call, when certain
            attributes require specific deserialization.

        Returns
        -------
        Serializable
            corresponding class instance
        """

        order1 = int(node.attrib['order1'])
        order2 = int(node.attrib['order2'])
        coefs = numpy.zeros((order1+1, order2+1), dtype=numpy.float64)
        for cnode in node.findall('Coef'):
            ind1 = int(cnode.attrib['exponent1'])
            ind2 = int(cnode.attrib['exponent2'])
            val = float(_get_node_value(cnode))
            coefs[ind1, ind2] = val
        return cls(Coefs=coefs)

    def to_node(self, doc, tag, parent=None, strict=DEFAULT_STRICT, exclude=()):
        """For XML serialization, to a dom element.

        Parameters
        ----------
        doc : ElementTree.ElementTree
            The xml Document
        tag : None|str
            The tag name. Defaults to the value of `self._tag` and then the class name if unspecified.
        parent : None|ElementTree.Element
            The parent element. Defaults to the document root element if unspecified.
        strict : bool
            If `True`, then raise an Exception (of appropriate type) if the structure is not valid.
            Otherwise, log a hopefully helpful message.
        exclude : tuple
            Attribute names to exclude from this generic serialization. This allows for child classes
            to provide specific serialization for special properties, after using this super method.

        Returns
        -------
        ElementTree.Element
            The constructed dom element, already assigned to the parent element.
        """

        if parent is None:
            parent = doc.getroot()
        node = _create_new_node(doc, tag, parent=parent)
        node.attrib['order1'] = str(self.order1)
        node.attrib['order2'] = str(self.order2)
        fmt_func = self._get_formatter('Coefs')
        for i, val1 in enumerate(self.Coefs):
            for j, val in enumerate(val1):
                # if val != 0.0:  # should we serialize it sparsely?
                cnode = _create_text_node(doc, 'Coef', fmt_func(val), parent=node)
                cnode.attrib['exponent1'] = str(i)
                cnode.attrib['exponent2'] = str(j)
        return node

    def to_dict(self, strict=DEFAULT_STRICT, exclude=()):
        """For json serialization.

        Parameters
        ----------
        strict : bool
            If `True`, then raise an Exception (of appropriate type) if the structure is not valid.
            Otherwise, log a hopefully helpful message.
        exclude : tuple
            Attribute names to exclude from this generic serialization. This allows for child classes
            to provide specific serialization for special properties, after using this super method.

        Returns
        -------
        OrderedDict
            dict representation of class instance appropriate for direct json serialization.
        """

        out = OrderedDict()
        out['Coefs'] = self.Coefs.tolist()
        return out


class XYZPolyType(Serializable):
    """
    Represents a single variable polynomial for each of `X`, `Y`, and `Z`. This gives position in ECF coordinates
    as a function of a single dependent variable.
    """

    _fields = ('X', 'Y', 'Z')
    _required = _fields
    # descriptors
    X = _SerializableDescriptor(
        'X', Poly1DType, _required, strict=True,
        docstring='The polynomial for the X coordinate.')  # type: Poly1DType
    Y = _SerializableDescriptor(
        'Y', Poly1DType, _required, strict=True,
        docstring='The polynomial for the Y coordinate.')  # type: Poly1DType
    Z = _SerializableDescriptor(
        'Z', Poly1DType, _required, strict=True,
        docstring='The polynomial for the Z coordinate.')  # type: Poly1DType

    def __init__(self, coords=None, X=None, Y=None, Z=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
        X : Poly1DType|numpy.ndarray|list|tuple
        Y : Poly1DType|numpy.ndarray|list|tuple
        Z : Poly1DType|numpy.ndarray|list|tuple
        kwargs : dict
        """
        if isinstance(coords, (numpy.ndarray, list, tuple)):
            if len(coords) >= 3:
                self.X, self.Y, self.Z = coords[0], coords[1], coords[2]
            else:
                raise ValueError('Expected coords to be of length 3, and received {}'.format(coords))
        else:
            self.X, self.Y, self.Z = X, Y, Z
        super(XYZPolyType, self).__init__(**kwargs)

    def __call__(self, t):
        """
        Evaluate the polynomial at points `t`. This passes `t` straight through
        to :func:`polyval` of :module:`numpy.polynomial.polynomial` for each of
        X,Y,Z components. If any of X,Y,Z is not populated, then None is returned.

        Parameters
        ----------
        t : float|int|numpy.ndarray
            The point(s) at which to evaluate.

        Returns
        -------
        numpy.ndarray
        """

        return numpy.array([self.X(t), self.Y(t), self.Z(t)])

    def get_array(self, dtype=numpy.object):
        """Gets an array representation of the class instance.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return.
            If `object`, an array of Poly1DType objects is returned.
            Otherwise, an ndarray of shape (3, N) of coefficient vectors is returned.

        Returns
        -------
        numpy.ndarray
            array of the form [X,Y,Z].
        """

        if dtype in ['object', numpy.object]:
            return numpy.array([self.X, self.Y, self.Z], dtype=numpy.object)
        else:
            # return a 3 x N array of coefficients
            xv = self.X.Coefs
            yv = self.Y.Coefs
            zv = self.Z.Coefs
            length = max(xv.size, yv.size, zv.size)
            out = numpy.zeros((3, length), dtype=dtype)
            out[0, :xv.size] = xv
            out[1, :yv.size] = yv
            out[2, :zv.size] = zv
            return out

    def derivative(self, der_order=1, return_poly=False):
        """
        Calculate the `der_order` derivative of each component polynomial.

        Parameters
        ----------
        der_order : int
            the order of the derivative
        return_poly : bool
            if `True`, a XYZPolyType if returned, otherwise a list of the coefficient arrays is returned.

        Returns
        -------
        XYZPolyType|list
        """

        coefs = [
            getattr(self, attrib).derivative(der_order=der_order, return_poly=False) for attrib in ['X', 'Y', 'Z']]

        if return_poly:
            return XYZPolyType(X=coefs[0], Y=coefs[1], Z=coefs[2])
        return coefs

    def derivative_eval(self, t, der_order=1):
        """
        Evaluate the `der_order` derivative of the polynomial collection at points `x`.
        This uses the functionality presented in :module:`numpy.polynomial.polynomial`.

        Parameters
        ----------
        t : numpy.ndarray
            The point(s) at which to evaluate.
        der_order : int
            The derivative.
        Returns
        -------
        numpy.ndarray
        """

        coefs = self.derivative(der_order=der_order, return_poly=False)
        return numpy.array([numpy.polynomial.polynomial.polyval(t, entry) for entry in coefs], dtype=numpy.float64)

    def shift(self, t_0, alpha=1, return_poly=False):
        r"""
        Transform a polynomial with respect to a affine shift in the coordinate system.
        That is, :math:`P(u) = Q(\alpha\cdot(t-t_0))`.

        Be careful to follow the convention that the transformation parameters express the *current coordinate system*
        as a shifted, **and then** scaled version of the *new coordinate system*. If the new coordinate is
        :math:`t = \beta\cdot u - t_0`, then :math:`u = (t - t_0)/\beta`, and :math:`\alpha = 1/\beta`.

        Parameters
        ----------
        t_0 : float
            the **current center coordinate** in the **new coordinate system.**
            That is, `u=0` when `t=t_0`.

        alpha : float
            the scale. That is, when `t = t0 + 1`, then :math:`u = \alpha`.

        return_poly : bool
            if `True`, an XYZPolyType instance is returned, otherwise a list of the coefficient arrays is returned.

        Returns
        -------
        XYZPolyType|list
        """

        coefs = [
            getattr(self, attrib).shift(t_0, alpha=alpha, return_poly=False) for attrib in ['X', 'Y', 'Z']]

        if return_poly:
            return XYZPolyType(X=coefs[0], Y=coefs[1], Z=coefs[2])
        return coefs


class XYZPolyAttributeType(XYZPolyType):
    """
    An array element of X, Y, Z polynomials. The output of these polynomials are expected
    to be spatial variables in the ECF coordinate system.
    """
    _fields = ('X', 'Y', 'Z', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # descriptors
    index = _IntegerDescriptor(
        'index', _required, strict=DEFAULT_STRICT, docstring='The array index value.')  # type: int

    def __init__(self, coords=None, X=None, Y=None, Z=None, index=None, **kwargs):
        """
        Parameters
        ----------
        coords : numpy.ndarray|list|tuple
        X : Poly1DType|numpy.ndarray|list|tuple
        Y : Poly1DType|numpy.ndarray|list|tuple
        Z : Poly1DType|numpy.ndarray|list|tuple
        index : int
        kwargs : dict
        """
        self.index = index
        super(XYZPolyAttributeType, self).__init__(coords=coords, X=X, Y=Y, Z=Z, **kwargs)


class GainPhasePolyType(Serializable):
    """A container for the Gain and Phase Polygon definitions."""

    _fields = ('GainPoly', 'PhasePoly')
    _required = _fields
    # descriptors
    GainPoly = _SerializableDescriptor(
        'GainPoly', Poly2DType, _required, strict=DEFAULT_STRICT,
        docstring='One-way signal gain (in dB) as a function of X-axis direction cosine (DCX) (variable 1) '
                  'and Y-axis direction cosine (DCY) (variable 2). Gain relative to gain at DCX = 0 '
                  'and DCY = 0, so constant coefficient is always 0.0.')  # type: Poly2DType
    PhasePoly = _SerializableDescriptor(
        'PhasePoly', Poly2DType, _required, strict=DEFAULT_STRICT,
        docstring='One-way signal phase (in cycles) as a function of DCX (variable 1) and '
                  'DCY (variable 2). Phase relative to phase at DCX = 0 and DCY = 0, '
                  'so constant coefficient is always 0.0.')  # type: Poly2DType

    def __init__(self, GainPoly=None, PhasePoly=None, **kwargs):
        """
        Parameters
        ----------
        GainPoly : Poly2DType|numpy.ndarray|list|tuple
        PhasePoly : Poly2DType|numpy.ndarray|list|tuple
        kwargs : dict
        """
        self.GainPoly = GainPoly
        self.PhasePoly = PhasePoly
        super(GainPhasePolyType, self).__init__(**kwargs)

    def __call__(self, x, y):
        """
        Evaluate a polynomial at points [`x`, `y`]. This passes `x`,`y` straight
        through to the call method for each component.

        Parameters
        ----------
        x : numpy.ndarray
            The first dependent variable of point(s) at which to evaluate.
        y : numpy.ndarray
            The second dependent variable of point(s) at which to evaluate.

        Returns
        -------
        numpy.ndarray
        """

        # TODO: is it remotely sensible that only one of these is defined?
        if self.GainPoly is None or self.PhasePoly is None:
            return None
        return numpy.array([self.GainPoly(x, y), self.PhasePoly(x, y)], dtype=numpy.float64)


#############
# Error Decorrelation type


class ErrorDecorrFuncType(Serializable):
    """
    This container allows parameterization of linear error decorrelation rate model.
    If `(Delta t) = |t2 - t1|`, then `CC(Delta t) = Min(1.0, Max(0.0, CC0 - DCR*(Delta t)))`.
    """

    _fields = ('CorrCoefZero', 'DecorrRate')
    _required = _fields
    _numeric_format = {'CorrCoefZero': '0.8f', 'DecorrRate': '0.8f'}
    # descriptors
    CorrCoefZero = _FloatDescriptor(
        'CorrCoefZero', _required, strict=True,
        docstring='Error correlation coefficient for zero time difference (CC0).')  # type: float
    DecorrRate = _FloatDescriptor(
        'DecorrRate', _required, strict=True,
        docstring='Error decorrelation rate. Simple linear decorrelation rate (DCR).')  # type: float

    def __init__(self, CorrCoefZero=None, DecorrRate=None, **kwargs):
        """
        Parameters
        ----------
        CorrCoefZero : float
        DecorrRate : float
        kwargs : dict
        """
        self.CorrCoefZero = CorrCoefZero
        self.DecorrRate = DecorrRate
        super(ErrorDecorrFuncType, self).__init__(**kwargs)


#############
# Coordinate Array type

class SerializableArray(object):
    _child_tag = None
    _child_type = None
    _minimum_length = 0
    _maximum_length = 2**32
    _array = None
    _name = None

    def __init__(self, coords=None, name=None, child_tag=None, child_type=None, minimum_length=None,
                 maximum_length=None, **kwargs):
        if name is None:
            raise ValueError('The name parameter is required.')
        if not isinstance(name, str):
            raise TypeError(
                'The name parameter is required to be an instance of str, got {}'.format(type(name)))
        self._name = name

        if child_tag is None:
            raise ValueError('The child_tag parameter is required.')
        if not isinstance(child_tag, str):
            raise TypeError(
                'The child_tag parameter is required to be an instance of str, got {}'.format(type(child_tag)))
        self._child_tag = child_tag

        if child_type is None:
            raise ValueError('The child_type parameter is required.')
        if not issubclass(child_type, Serializable):
            raise TypeError('The child_type is required to be a subclass of Serializable.')
        self._child_type = child_type

        if minimum_length is not None:
            self._minimum_length = max(int(minimum_length), 0)
        if maximum_length is not None:
            self._maximum_length = max(int(maximum_length), self._minimum_length)

        self.set_array(coords)

    @property
    def size(self):  # type: () -> int
        """
        int: the size of the array.
        """

        if self._array is None:
            return 0
        else:
            return self._array.size

    def get_array(self, dtype=numpy.object, **kwargs):
        """Gets an array representation of the class instance.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return.
        kwargs : keyword arguments for calls of the form child.get_array(**kwargs)

        Returns
        -------
        numpy.ndarray
            * If `dtype` in `(numpy.object`, 'object')`, then the literal array of
              child objects is returned. *Note: Beware of mutating the elements.*
            * If `dtype` has any other value, then the return value will be tried
              as `numpy.array([child.get_array(dtype=dtype, **kwargs) for child in array]`.
            * If there is any error, then `None` is returned.
        """

        if dtype in [numpy.object, 'object']:
            return self._array
        else:
            try:
                return numpy.array(
                    [child.get_array(dtype=dtype, **kwargs) for child in self._array], dtype=dtype)
            except Exception:
                return None

    def set_array(self, coords):
        """
        Sets the underlying array.

        Parameters
        ----------
        coords : numpy.ndarray|list|tuple

        Returns
        -------
        None
        """
        # TODO: flesh this docstring out more effectively.

        if coords is None:
            self._array = None
        else:
            self._array = _parse_serializable_array(
                coords, 'coords', self, self._child_type, self._child_tag)

    def to_node(self, doc, tag, parent=None, strict=DEFAULT_STRICT, exclude=()):
        if self.size == 0:
            return None  # nothing to be done

        anode = _create_new_node(doc, tag, parent=parent)
        anode.attrib['size'] = str(self.size)
        for i, entry in enumerate(self._array):
            entry.to_node(doc, self._child_tag, parent=anode, strict=strict)

    @classmethod
    def from_node(cls, node, name, child_tag, child_type, **kwargs):
        return cls(coords=node, name=name, child_tag=child_tag, child_type=child_type, **kwargs)

    def to_dict(self, strict=DEFAULT_STRICT):
        if self.size == 0:
            return []
        return [entry.to_dict(strict=strict) for entry in self._array]

# TODO:
#  1.)  Move this into base.py
#  2.) Make a special cornerstring version with the four attributes.
#  3.)  Incorporate into the _SerializableArrayDescriptor
#  4.)  Incorporate into the Serializable serialization process.
#  5.)  Make a Serializable list & use that for all the lists
#  6.)  This is mostly Parameters, so that should be a particular case.
#       Like a dictionary descriptor or something?
