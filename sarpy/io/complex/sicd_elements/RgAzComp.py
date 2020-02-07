# -*- coding: utf-8 -*-
"""
The RgAzCompType definition.
"""

import logging

import numpy
from numpy.linalg import norm

from .base import Serializable, DEFAULT_STRICT, _FloatDescriptor, _SerializableDescriptor
from .blocks import Poly1DType


__classification__ = "UNCLASSIFIED"
__author__ = "Thomas McCullough"


class RgAzCompType(Serializable):
    """Parameters included for a Range, Doppler image."""
    _fields = ('AzSF', 'KazPoly')
    _required = _fields
    _numeric_format = {'AzSF': '0.16G'}
    # descriptors
    AzSF = _FloatDescriptor(
        'AzSF', _required, strict=DEFAULT_STRICT,
        docstring='Scale factor that scales image coordinate az = ycol (meters) to a delta cosine of the '
                  'Doppler Cone Angle at COA, *(in 1/m)*')  # type: float
    KazPoly = _SerializableDescriptor(
        'KazPoly', Poly1DType, _required, strict=DEFAULT_STRICT,
        docstring='Polynomial function that yields azimuth spatial frequency *(Kaz = Kcol)* as a function of '
                  'slow time *(variable 1)*. That is '
                  ':math:`Slow Time (sec) -> Azimuth spatial frequency (cycles/meter)`. '
                  'Time relative to collection start.')  # type: Poly1DType

    def __init__(self, AzSF=None, KazPoly=None, **kwargs):
        """

        Parameters
        ----------
        AzSF : float
        KazPoly : Poly1DType|numpy.ndarray|list|tuple
        kwargs : dict
        """
        self.AzSF = AzSF
        self.KazPoly = KazPoly
        super(RgAzCompType, self).__init__(**kwargs)

    def _derive_parameters(self, Grid, Timeline, SCPCOA):
        """
        Expected to be called by the SICD object.

        Parameters
        ----------
        Grid : sarpy.io.complex.sicd_elements.GridType
        Timeline : sarpy.io.complex.sicd_elements.TimelineType
        SCPCOA : sarpy.io.complex.sicd_elements.SCPCOA.SCPCOAType

        Returns
        -------
        None
        """

        look = SCPCOA.look
        az_sf = -look*numpy.sin(numpy.deg2rad(SCPCOA.DopplerConeAng))/SCPCOA.SlantRange
        if self.AzSF is None:
            self.AzSF = az_sf
        elif abs(self.AzSF - az_sf) > 1e-3:  # TODO: what is a sensible tolerance here?
            logging.warning(
                'The derived value for RgAzComp.AzSF is {}, while the current '
                'setting is {}.'.format(az_sf, self.AzSF))

        if self.KazPoly is None:
            if Grid.Row.KCtr is not None and Timeline is not None and Timeline.IPP is not None and \
                    Timeline.IPP.size == 1 and Timeline.IPP[0].IPPPoly is not None and SCPCOA.SCPTime is not None:

                st_rate_coa = Timeline.IPP[0].IPPPoly.derivative_eval(SCPCOA.SCPTime, 1)

                krg_coa = Grid.Row.KCtr
                if Grid.Row is not None and Grid.Row.DeltaKCOAPoly is not None:
                    krg_coa += Grid.Row.DeltaKCOAPoly.Coefs[0, 0]

                # Scale factor described in SICD spec
                delta_kaz_per_delta_v = \
                    look*krg_coa*norm(SCPCOA.ARPVel.get_array()) * \
                    numpy.sin(numpy.deg2rad(SCPCOA.DopplerConeAng))/(SCPCOA.SlantRange*st_rate_coa)
                self.KazPoly = Poly1DType(Coefs=delta_kaz_per_delta_v*Timeline.IPP[0].IPPPoly.Coefs)
