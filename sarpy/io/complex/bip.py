# -*- coding: utf-8 -*-
"""
This provides implementation of Reading and writing capabilities for files with
data stored in *Band Interleaved By Pixel (BIP)* format.
"""

import logging
import os
import sys

import numpy

from .base import BaseChipper, AbstractWriter

size_func = int
int_func = int
if sys.version_info[0] < 3:
    # noinspection PyUnresolvedReferences
    int_func = long  # to accommodate 32-bit python 2


__classification__ = "UNCLASSIFIED"
__author__ = "Thomas McCullough"


class BIPChipper(BaseChipper):
    """
    Band interleaved format file chipper
    """

    __slots__ = (
        '_file_name', '_data_type', '_data_offset', '_shape', '_bands', '_memory_map', '_fid')

    def __init__(self, file_name, data_type, data_size,
                 symmetry=(False, False, False), complex_type=False,
                 data_offset=0, bands_ip=1):
        """

        Parameters
        ----------
        file_name : str
            The name of the file from which to read
        data_type : numpy.dtype|str
            The data type of the underlying file. **Note: specify endianness where necessary.**
        data_size : tuple
            The full size of the data *after* any required transformation. See
            `data_size` property.
        symmetry : tuple
            Describes any required data transformation. See the `symmetry` property.
        complex_type : callable|bool
            For complex type handling.
            If callable, then this is expected to transform the raw data to the complex data.
            If this evaluates to `True`, then the assumption is that real/imaginary
            components are stored in adjacent bands, which will be combined into a
            single band upon extraction.
        data_offset : int
            byte offset from the start of the file at which the data actually starts
        bands_ip : int
            number of bands - really intended for complex data
        """

        super(BIPChipper, self).__init__(data_size, symmetry=symmetry, complex_type=complex_type)

        bands = int_func(bands_ip)
        if self._complex_type is not False:
            bands *= 2

        self._data_offset = int_func(data_offset)
        self._data_type = data_type
        self._bands = bands
        self._shape = data_size + (self._bands, )

        if not os.path.isfile(file_name):
            raise IOError('Path {} either does not exists, or is not a file.'.format(file_name))
        if not os.access(file_name, os.R_OK):
            raise IOError('User does not appear to have read access for file {}.'.format(file_name))
        self._file_name = file_name

        self._memory_map = None
        self._fid = None
        try:
            self._memory_map = numpy.memmap(self._file_name,
                                            dtype=data_type,
                                            mode='r',
                                            offset=data_offset,
                                            shape=self._shape)  # type: numpy.memmap
        except (OverflowError, OSError):
            # if 32-bit python, then we'll fail for any file larger than 2GB
            # we fall-back to a slower version of reading manually
            self._fid = open(self._file_name, mode='rb')
            logging.warning(
                'Falling back to reading file {} manually (instead of using mem-map). This has almost '
                'certainly occurred because you are 32-bit python to try to read (portions of) a file '
                'which is larger than 2GB.'.format(self._file_name))

    def __del__(self):
        if hasattr(self, '_fid') and self._fid is not None and \
                hasattr(self._fid, 'closed') and not self._fid.closed:
            self._fid.close()

    def _read_raw_fun(self, range1, range2):
        range1, range2 = self._reorder_arguments(range1, range2)
        if self._memory_map is not None:
            return self._read_memory_map(range1, range2)
        elif self._fid is not None:
            return self._read_file(range1, range2)

    def _read_memory_map(self, range1, range2):
        if (range1[1] == -1 and range1[2] < 0) and (range2[1] == -1 and range2[2] < 0):
            out = numpy.array(self._memory_map[range1[0]::range1[2], range2[0]::range2[2]], dtype=self._data_type)
        elif range1[1] == -1 and range1[2] < 0:
            out = numpy.array(self._memory_map[range1[0]::range1[2], range2[0]:range2[1]:range2[2]], dtype=self._data_type)
        elif range2[1] == -1 and range2[2] < 0:
            out = numpy.array(self._memory_map[range1[0]:range1[1]:range1[2], range2[0]::range2[2]],
                              dtype=self._data_type)
        else:
            out = numpy.array(self._memory_map[range1[0]:range1[1]:range1[2], range2[0]:range2[1]:range2[2]],
                              dtype=self._data_type)
        return out

    def _read_file(self, range1, range2):
        def get_row_location(rr, cc):
            return self._data_offset + \
                   rr*stride + \
                   cc*element_size

        # we have to manually map out the stride and all that for the array ourselves
        element_size = int_func(numpy.dtype(self._data_type).itemsize*self._bands)
        stride = element_size*int_func(self._shape[0])  # how much to skip a whole (real) row?
        entries_per_row = abs(range1[1] - range1[0])  # not including the stride, if not +/-1
        # let's determine the specific row/column arrays that we are going to read
        dim1array = numpy.arange(range1)
        dim2array = numpy.arange(range2)
        # allocate our output array
        out = numpy.empty((len(dim1array), len(dim2array), self._bands), dtype=self._data_type)
        # determine the first column reading location (may be reading cols backwards)
        col_begin = dim2array[0] if range2[2] > 0 else dim2array[-1]

        for i, row in enumerate(dim1array):
            # go to the appropriate point in the file for (row/col)
            self._fid.seek(get_row_location(row, col_begin))
            # interpret this of line as numpy.ndarray - inherently flat array
            line = numpy.fromfile(self._fid, self._data_type, entries_per_row*self._bands)
            # note that we purposely read without considering skipping elements, which
            #   is factored in (along with any potential order reversal) below
            out[i, :, :] = line[::range2[2]]
        return out


class BIPWriter(AbstractWriter):
    """
    For writing the SICD data into the NITF container. This is abstracted generally
    because an array of these writers is used for multi-image segment NITF files.
    That is, SICD with enough rows/columns.
    """

    __slots__ = (
        '_data_size', '_data_type', '_complex_type', '_data_offset',
        '_shape', '_memory_map', '_fid')

    def __init__(self, file_name, data_size, data_type, complex_type, data_offset=0):
        """
        For writing the SICD data into the NITF container. This is abstracted generally
        because an array of these writers is used for multi-image segment NITF files.
        That is, SICD with enough rows/columns.

        Parameters
        ----------
        file_name : str
            the file_name
        data_size : tuple
            the shape of the form (rows, cols)
        data_type : numpy.dtype|str
            the underlying data type of the output data. Specify endianess here if necessary.
        complex_type : callable|bool
            For complex type handling.

            * If callable, then this is expected to transform the complex data
              to the raw data. A ValueError will be raised if the data type of
              the output doesn't match `data_type`. By the sicd standard,
              `data_type` should be int16 or uint8.

            * If `True`, then the data is dtype complex64 or complex128, and will
              be written out to raw after appropriate manipulation. This requires
              that `data_type` is float32 - for the sicd standard.

            * If `False`, the then data will be written directly to raw. A ValueError
              will be raised if the data type of the data to be written doesn't
              match `data_type`.
        data_offset : int
            byte offset from the start of the file at which the data actually starts
        """

        super(BIPWriter, self).__init__(file_name)
        if not isinstance(data_size, tuple):
            data_size = tuple(data_size)
        if len(data_size) != 2:
            raise ValueError(
                'The data_size parameter must have length 2, and got {}.'.format(data_size))
        data_size = (int_func(data_size[0]), int_func(data_size[1]))
        if data_size[0] < 0 or data_size[1] < 0:
            raise ValueError('All entries of data_size {} must be non-negative.'.format(data_size))
        self._data_size = data_size

        self._data_type = numpy.dtype(data_type)
        if not (isinstance(complex_type, bool) or callable(complex_type)):
            raise ValueError('complex-type must be a boolean or a callable')
        self._complex_type = complex_type

        if self._complex_type is True and self._data_type.name != 'float32':
            raise ValueError(
                'complex_type = `True`, which requires that data for writing has '
                'dtype complex64/128, and output is written as float32 (data_type). '
                'data_type is given as {}.'.format(data_type))
        if callable(self._complex_type) and self._data_type.name not in ('uint8', 'int16'):
            raise ValueError(
                'complex_type is callable, which requires that dtype complex64/128, '
                'and output is written as uint8 or uint16. '
                'data_type is given as {}.'.format(self._data_type.name))

        self._data_offset = int_func(data_offset)
        if self._complex_type is False:
            self._shape = self._data_size
        else:
            self._shape = (self._data_size[0], self._data_size[1], 2)

        self._memory_map = None
        self._fid = None
        try:
            self._memory_map = numpy.memmap(self._file_name,
                                            dtype=self._data_type,
                                            mode='r+',
                                            offset=self._data_offset,
                                            shape=self._shape)
        except (OverflowError, OSError):
            # if 32-bit python, then we'll fail for any file larger than 2GB
            # we fall-back to a slower version of reading manually
            self._fid = open(self._file_name, mode='r+b')
            logging.warning(
                'Falling back to writing file {} manually (instead of using mem-map). This has almost '
                'certainly occurred because you are 32-bit python to try to read (portions of) a file '
                'which is larger than 2GB.'.format(self._file_name))

    def write_chip(self, data, start_indices=(0, 0)):
        self.__call__(data, start_indices=start_indices)

    def __call__(self, data, start_indices=(0, 0)):
        """
        Write the specified data.

        Parameters
        ----------
        data : numpy.ndarray
        start_indices : tuple

        Returns
        -------
        None
        """

        # NB: it is expected that start-indices has been validate before getting here
        if not isinstance(data, numpy.ndarray):
            raise TypeError('Requires data is a numpy.ndarray, got {}'.format(type(data)))

        start1, stop1 = start_indices[0], start_indices[0] + data.shape[0]
        start2, stop2 = start_indices[1], start_indices[1] + data.shape[1]

        # make sure we are using the proper data ordering
        if not data.flags.c_contiguous:
            data = numpy.ascontiguousarray(data)

        if self._complex_type is False:
            if data.dtype.name != self._data_type.name:
                raise ValueError(
                    'Writer expects data type {}, and got data of type {}.'.format(self._data_type, data.dtype))
            self._call(start1, stop1, start2, stop2, data)
        elif callable(self._complex_type):
            new_data = self._complex_type(data)
            if new_data.dtype.name != self._data_type.name:
                raise ValueError(
                    'Writer expects data type {}, and got data of type {} from the '
                    'callable method complex_type.'.format(self._data_type, new_data.dtype))
            self._call(start1, stop1, start2, stop2, new_data)
        else:  # complex_type is True
            if data.dtype.name not in ('complex64', 'complex128'):
                raise ValueError(
                    'Writer expects data type {}, and got data of type {} from the '
                    'callable method complex_type.'.format(self._data_type, data.dtype))
            if data.dtype.name != 'complex64':
                data = data.astype(numpy.complex64)

            data_view = data.view(numpy.float32).reshape((data.shape[0], data.shape[1], 2))
            self._call(start1, stop1, start2, stop2, data_view)

    def _call(self, start1, stop1, start2, stop2, data):
        if self._memory_map is not None:
            self._memory_map[start1:stop1, start2:stop2, :] = data
            return

        # we have to fall-back to manually write
        element_size = int_func(self._data_type.itemsize)
        if len(self._shape) == 3:
            element_size *= int_func(self._shape[2])
        stride = element_size*int_func(self._data_size[0])
        # go to the appropriate spot in the file for first entry
        self._fid.seek(self._data_offset + stride*start1 + element_size*start2)
        if start1 == 0 and stop1 == self._data_size[0]:
            # we can write the block all at once
            data.astype(self._data_type).tofile(self._fid)
        else:
            # have to write one row at a time
            bytes_to_skip_per_row = element_size*(self._data_size[0]-(stop1-start1))
            for i, row in enumerate(data):
                # we the row, and then skip to where the next row starts
                row.astype(self._data_type).tofile(self._fid)
                if i < len(data) - 1:
                    # don't seek on last entry (avoid segfault, or whatever)
                    self._fid.seek(bytes_to_skip_per_row, os.SEEK_CUR)

    def close(self):
        """
        **Should be called on exit.** Cleanly close the file. This is actually only
        required if memory map failed, and we fell back to manually writing the file.

        Returns
        -------
        None
        """

        if hasattr(self, '_fid') and self._fid is not None and \
                hasattr(self._fid, 'closed') and not self._fid.closed:
            self._fid.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is None:
            self.close()
        else:
            logging.error(
                'The {} file writer generated an exception during processing. The file {} may be '
                'only partially generated and corrupt.'.format(self.__class__.__name__, self._file_name))
            # The exception will be reraised.
            # It's unclear how any exception could be caught.
