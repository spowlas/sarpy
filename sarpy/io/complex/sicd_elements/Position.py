# -*- coding: utf-8 -*-
"""
The PositionType definition.
"""

from typing import List, Union
import logging

import numpy

from .base import Serializable, DEFAULT_STRICT, \
    _SerializableDescriptor, _SerializableArrayDescriptor, SerializableArray
from .blocks import XYZType, XYZPolyType, XYZPolyAttributeType


__classification__ = "UNCLASSIFIED"
__author__ = "Thomas McCullough"


class PositionType(Serializable):
    """The details for platform and ground reference positions as a function of time since collection start."""
    _fields = ('ARPPoly', 'GRPPoly', 'TxAPCPoly', 'RcvAPC')
    _required = ('ARPPoly',)
    _collections_tags = {'RcvAPC': {'array': True, 'child_tag': 'RcvAPCPoly'}}

    # descriptors
    ARPPoly = _SerializableDescriptor(
        'ARPPoly', XYZPolyType, _required, strict=DEFAULT_STRICT,
        docstring='Aperture Reference Point (ARP) position polynomial in ECF as a function of elapsed '
                  'seconds since start of collection.')  # type: XYZPolyType
    GRPPoly = _SerializableDescriptor(
        'GRPPoly', XYZPolyType, _required, strict=DEFAULT_STRICT,
        docstring='Ground Reference Point (GRP) position polynomial in ECF as a function of elapsed '
                  'seconds since start of collection.')  # type: XYZPolyType
    TxAPCPoly = _SerializableDescriptor(
        'TxAPCPoly', XYZPolyType, _required, strict=DEFAULT_STRICT,
        docstring='Transmit Aperture Phase Center (APC) position polynomial in ECF as a function of '
                  'elapsed seconds since start of collection.')  # type: XYZPolyType
    RcvAPC = _SerializableArrayDescriptor(
        'RcvAPC', XYZPolyAttributeType, _collections_tags, _required, strict=DEFAULT_STRICT,
        docstring='Receive Aperture Phase Center polynomials array. '
                  'Each polynomial has output in ECF, and represents a function of elapsed seconds since start of '
                  'collection.')  # type: Union[SerializableArray, List[XYZPolyAttributeType]]

    def __init__(self, ARPPoly=None, GRPPoly=None, TxAPCPoly=None, RcvAPC=None, **kwargs):
        """

        Parameters
        ----------
        ARPPoly : XYZPolyType
        GRPPoly : XYZPolyType
        TxAPCPoly : XYZPolyType
        RcvAPC : SerializableArray|List[XYZPolyAttributeType]|list|tuple
        kwargs : dict
        """
        self.ARPPoly = ARPPoly
        self.GRPPoly = GRPPoly
        self.TxAPCPoly = TxAPCPoly
        self.RcvAPC = RcvAPC
        super(PositionType, self).__init__(**kwargs)

    def _derive_arp_poly(self, SCPCOA):
        """
        Expected to be called from SICD parent. Set the aperture position polynomial from position, time,
        acceleration at scptime, if necessary.

        .. Note::

            This assumes constant velocity and acceleration.

        Parameters
        ----------
        SCPCOA : sarpy.io.complex.sicd_elements.SCPCOA.SCPCOAType

        Returns
        -------
        None
        """

        if self.ARPPoly is not None:
            return  # nothing to be done

        if SCPCOA is None or SCPCOA.ARPPos is None or SCPCOA.ARPVel is None or SCPCOA.SCPTime is None:
            return  # not enough information to derive

        if SCPCOA.ARPAcc is None:
            SCPCOA.ARPAcc = XYZType.from_array((0, 0, 0))
        # define the polynomial
        coefs = numpy.zeros((3, 3), dtype=numpy.float64)
        scptime = SCPCOA.SCPTime
        pos = SCPCOA.ARPPos.get_array()
        vel = SCPCOA.ARPVel.get_array()
        acc = SCPCOA.ARPAcc.get_array()
        coefs[0, :] = pos - vel * scptime + 0.5 * acc * scptime * scptime
        coefs[1, :] = vel - acc * scptime
        coefs[2, :] = acc
        self.ARPPoly = XYZPolyType.from_array(coefs)

    def _basic_validity_check(self):
        condition = super(PositionType, self)._basic_validity_check()
        if self.ARPPoly is not None and \
                (self.ARPPoly.X.order1 < 2 or self.ARPPoly.Y.order1 < 2 or self.ARPPoly.Z.order1 < 2):
            logging.error(
                'ARPPoly should be order at least 2 in each component. '
                'Got X.order1 = {}, Y.order1 = {}, and Z.order1 = {}'.format(self.ARPPoly.X.order1,
                                                                             self.ARPPoly.Y.order1,
                                                                             self.ARPPoly.Z.order1))
            condition = False
        return condition
