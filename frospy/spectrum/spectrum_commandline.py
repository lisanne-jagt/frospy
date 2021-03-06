#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from .controllers import (
                    load_cmt, read_data, load_segments, report_input,
                    quit_spectrum, timewindow, freqwindow, remove_station,
                    set_plot_args, process_input, search_stream
                    )

try:
    from frospy.core.spectrum.plot import plot_spectrum
    import matplotlib.pyplot as plt
    NOWINDOW = False

except ImportError:
    NOWINDOW = True

from frospy.core import Spectrum
from frospy.util.base import inv4stream
from frospy.core.modes import read as read_modes

from obspy.core import AttribDict
from obspy import Stream


try:
    import readline
    readline.parse_and_bind("tab: complete")
except ImportError:
    pass


def run(data, **iargs):
    """
    Spectrum() provides an interactive tool to visualize and compare the
    frequency-spectrum (phase and amplitude) of real data and syntetics.
    Additional to the spectrum, the used singlets, time-window of the
    seismogram, the beachball of the source and the great cirlce path of the
    source-receiver combination are displayed.

    param data: name of or path to the data file, containing the real data
    type  data: string

    param syn: name of or path to the data file, containing the synthetic data.
               If more than one synthetic data set should be loaded for each
               station, a list of strings has to be provided.
    type  syn: list of strings

    param syn: corresponding list of labels for synthetic data. If None,
               synthetics will be given   names "Synthetics 1",
               "Synthetics 2".
    type  syn: list of strings or None

    param cmt_file: Path to csv file containing event id and moment tensor
    type  cmt_file: string

    param show_modes: Set True if reference frequencies (using PREM)
                      of modes should be plotted. Default False
    type  show_modes: Bool

    param segment_file: Path to pick file, as specified in
                        "Splitting functions: A  manual for measurement and
                        calculation" by Arwen Deuss
    type  segment_file: String

    param runall_in: Tuple containing keywords for the procedure, e.g.:

                  runall = (modes, min_snr, exec_part)

                  with: modes     = List of modenames
                        min_snr   = minimum signal to noise ratio
                        exec_part = part of code to run
                                    ('printw' or 'autopick')

    """
    # Read input files, preparing workfiles ###################################
    # Assignin id

    # Temporary solution
    # create all local variables
    main = AttribDict(iargs)
    main = set_defaults_init_main(main)

    print('Reading files ...')
    # Loading cmt file
    if main.cmt_file:
        main.cmt = load_cmt(file=main.cmt_file, verbose=main.verbose)
    else:
        main.cmt = load_cmt(id=main.cmt_id, verbose=main.verbose)

    # Loading pick file
    if main.segment_file is not None:
        main.segments = load_segments([main.segment_file])

    pick = None

    # Don't check for identical data files but check later for correct channel
    # selection
    main = read_data(data, main)
    main.inv = inv4stream(main.st)

    print(report_input(main))

    if main.search:
        main = search_stream(main, main.search)

    while True:
        if len(main.st_work) == 0:
            msg = 'No data'
            print(msg)

            quit_spectrum(main, False)
            plt.ioff()
            plt.close('all')
            break

        elif main.i >= len(main.st_work) and main.i_old is not None:
            msg = '\n\x1b[6;30;42m\n\nReached end of search-scope,'
            msg += ' going back to last station\n\x1b[0m'
            print(msg)
            main.st_work = main.st.copy()
            if main.syn:
                main.st_syn_work = main.st_syn[:]
            main.i = main.i_old
            main.i_old = None

        elif main.i >= len(main.st_work):
            msg = '\n\x1b[6;30;42m\n\nReached end of file,'
            msg += ' going back to start\n\x1b[0m'
            print(msg)
            main.i = 0

        # Pick current data set and corresponding synthetic set
        main.tr = main.st_work[main.i]
        main.syn_trs = Stream()
        if main.segments is not None:
            main.segments.sort(['fw2'])
            maxj = len(main.segments.select(station=main.tr.stats.station))
            if main.j >= maxj and maxj != 0:
                msg = '\n\x1b[6;30;42m\n\nReached end of segments,'
                msg += ' for this station. Going back to start\n\x1b[0m'
                print(msg)
                main.j = 0

        # select synthetics
        if main.syn:
            if main.stream_order == 'same':
                for s in main.st_syn_work:
                    main.syn_trs += s[main.i]
            else:
                for s in main.st_syn_work:
                    main.syn_trs += s.select(station=main.tr.stats.station)

        if main.recalc:
            print("\n---------------------------")
            msg = '\033[94mCurrent station: %s %s\n\033[0m'
            status_msg = msg % (main.tr.stats.station, main.tr.stats.channel)

            if main.tw_org is not None:
                main.tw = main.tw_org[:]

            pick = None
            if main.segments is not None:
                try:
                    stat = main.tr.stats.station
                    pick = main.segments.select(station=stat)[main.j]
                    if main.set_seg_tw:
                        main.tw = [pick.tw1, pick.tw2]
                    if main.set_seg_fw:
                        main.fw = [pick.fw1 - 0.05, pick.fw2 + 0.05]
                    msg = 'Segment data: \n'
                    msg += 'Frequencies:\t%.3f-%.3f mHz\n' % (pick.fw1,
                                                              pick.fw2)
                    msg += 'Timewindow:\t%.1f-%.1f h\n' % (pick.tw1, pick.tw2)
                    status_msg += msg

                except IndexError:
                    msg = 'No picked segments in file for %s\n'
                    status_msg += msg % main.tr.stats.station

            # Cosine taper constructed and applied
            if main.verbose:
                status_msg += "Data info:\n%s\n" % main.tr
                status_msg += "Synthetics info:\n%s\n" % main.syn_trs

            if main.tw is None:
                main.tw, main.tw_org = timewindow(main.tr, [None])

            if main.fw is None:
                main.fw = freqwindow([None])

            if main.qwindow is not None:
                main.tw = main.qwindow
                s = main.tw[0]
                e = main.tw[1]
                msg = '\033[93mTimewindow set by Q-cycle to %i-%i h\033[0m\n'
                print(msg % (s, e))
                main.qwindow = None

            if main.tr.stats.station != main.current_station:
                main.current_station = main.tr.stats.station
                print(status_msg)

            # Perform Fouriertransform
            main.spec = Spectrum(main.tr, main.tw[0], main.tw[1], main.syn_trs,
                                 taper=main.taper_shape,
                                 syn_label=main.syn_label,
                                 label=main.data_label)
            main.startlabel = main.spec.flabel(main.fw[0])
            main.endlabel = main.spec.flabel(main.fw[1])

            # Calculate misfit
            if pick is not None and main.syn is not None:
                snr_t, nwins, ol_err = main.spec.signal2noise(pick)
                mf_msg = "SNR:\t\t%f\n" % snr_t

                try:
                    fwhm = main.spec.signal2fwhm(pick)
                    mf_msg += "SFWHMR:\t\t%e\n" % fwhm
                    mf_msg += "SNR * SFWHMR:\t%e\n" % (snr_t*fwhm)
                except Exception as e:
                    mf_msg += "SFWHMR: %s\n" % e
                mf = main.spec.misfit(pick)
                if ol_err:
                    mf_msg += "\033[91mFreq window overlaps with"
                    mf_msg += " noise window\033[0m\n"

                mf_msg += "\nMisfits:\n"
                for name, c in zip(main.spec.syn, mf):
                    mf_msg += "%s\t%f\n" % (list(name.timeseries.keys())[0],
                                            c[1])

                if mf != main.mf:
                    main.mf = mf
                    print(mf_msg)

                if main.min_snr:
                    if snr_t < main.min_snr:
                        remove_station(main, save_tmp=False)
                        continue

                if main.max_mf:
                    if mf[0][1] > main.max_mf:
                        remove_station(main, save_tmp=False)
                        continue

            if not main.nowindow:
                main = plot_spectrum(main)

        # Wait for keyboard input
        main.recalc = True
        main.savefig = False

        # If quit, it is None
        # out = process_input(spec, pick, main)
        out = process_input(pick, main)
        if out is None:
            plt.ioff()
            plt.close('all')
            break
        else:
            pick, main = out[:]

    plt.ioff()
    return main.segments


def set_defaults_init_main(main):
    main.recalc = True
    main.weighting = 'integrate'
    main.update_maps = True
    main.zoom_sl = 5.
    if 'save_stream' not in main:
        main.save_stream = False

    main.fs = 10.
    main.noisewin = False
    main.overlap = False
    main.current_station = None
    main.segments = None

    main.rmf = None
    main.cmf = None
    main.mf = None

    # Magnification of synthetics
    main.mfac = 1

    # Set reference figure and ax to None
    main.rfig = None
    main.rax = None
    main.seg_ax = None
    main.savefig = False
    main.fs = 10

    # Reading modes
    main.modes_all = read_modes()

    # Set Referece times
    if main.tw:
        main.tw_org = main.tw[:]
    else:
        main.tw_org = None
    main.qwindow = None
    main.min_snr = None
    main.max_mf = None

    if main.seg_reference:
        main.set_seg_fw = True
        main.set_seg_tw = True
        if main.fw:
            main.set_seg_fw = False
    else:
        main.set_seg_fw = False
        main.set_seg_tw = True

    main.i = 0
    main.i_old = None

    main.j = 0  # segment iterator

    return main
