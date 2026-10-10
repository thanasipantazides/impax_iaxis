import os
import sys
from datetime import datetime, timezone

import astropy.time
import numpy as np
from spacepy import pycdf

# CDF global fields:
#
#   - APID
#   - SRC_FILE
#   - INST
#   - MISS
#   - PI
#   - LEVEL
#   - QUALITY
#   - FILE_VERSION
#   - GENERATED_BY
#   - LINK
#
#  zVariables:
#   - EPOCH
#       - TIME
#       - UNITS
#       - DEPEND_1


def cdf_defaults_hk(save_path: str):
    logical_source = "impax_iaxis_l0-hk"
    data_version = "0"
    datestr = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    fname = f"{logical_source}_{datestr}_{data_version}"
    fpath = os.path.join(save_path, fname + ".cdf")

    cdf = pycdf.CDF(fpath, "", readonly=False)

    cdf.attrs["Data_type"] = "L0-raw>level 0 hk"
    cdf.attrs["Data_version"] = data_version
    cdf.attrs["Descriptor"] = "IAXIS>IMPAX Atmospheric X-ray Imaging Spectrometer"
    cdf.attrs["Instrument_type"] = ["Imaging and Remote Sensing (Magnetosphere/Earth)"]
    cdf.attrs["Logical_source"] = logical_source
    cdf.attrs["Logical_file_id"] = fname
    cdf.attrs["Logical_source_description"] = "IMPAX IAXIS level 0 hk"
    cdf.attrs["Mission_group"] = (
        "Imaging Microburst Precipitation with Atmospheric X-ray emissions cubesat (IMPAX)"
    )
    cdf.attrs["PI_affiliation"] = "University of Minnesota"
    cdf.attrs["PI_name"] = "Chris Colpitts"
    cdf.attrs["Source_name"] = (
        "IMPAX>Imaging Microburst Precipitation with Atmospheric X-ray emissions cubesat"
    )
    cdf.attrs["TEXT"] = ["Raw IAXIS HK telemetry fields decoded."]
    cdf.attrs["Date_Start"] = "1970-01-01T00:00:00"
    cdf.attrs["Date_End"] = "2050-01-01T00:00:00"

    cdf.attrs["IMPAX_Quality"] = "Tenuous and preliminary"

    # for some reason type=pycdf.const.CDF_TIME_TT2000 does not work here.
    # cdf.attrs["Epoch"] = 0
    # cdf.attrs["Epoch"].type = pycdf.const.CDF_EPOCH

    return cdf


def cdf_defaults_sci(save_path: str):
    logical_source = "impax_iaxis_l0-sci"
    data_version = "0"
    datestr = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    fname = f"{logical_source}_{datestr}_{data_version}"
    fpath = os.path.join(save_path, fname + ".cdf")

    cdf = pycdf.CDF(fpath, "", readonly=False)

    cdf.attrs["Data_type"] = "L0-sci>level 0 sci"
    cdf.attrs["Data_version"] = data_version
    cdf.attrs["Descriptor"] = "IAXIS>IMPAX Atmospheric X-ray Imaging Spectrometer"
    cdf.attrs["Instrument_type"] = ["Imaging and Remote Sensing (Magnetosphere/Earth)"]
    cdf.attrs["Logical_source"] = logical_source
    cdf.attrs["Logical_file_id"] = fname
    cdf.attrs["Logical_source_description"] = "IMPAX IAXIS level 0 sci"
    cdf.attrs["Mission_group"] = (
        "Imaging Microburst Precipitation with Atmospheric X-ray emissions cubesat (IMPAX)"
    )
    cdf.attrs["PI_affiliation"] = "University of Minnesota"
    cdf.attrs["PI_name"] = "Chris Colpitts"
    cdf.attrs["Source_name"] = (
        "IMPAX>Imaging Microburst Precipitation with Atmospheric X-ray emissions cubesat"
    )
    cdf.attrs["TEXT"] = ["Raw IAXIS science telemetry fields decoded."]
    cdf.attrs["Date_Start"] = "1970-01-01T00:00:00"
    cdf.attrs["Date_End"] = "2050-01-01T00:00:00"

    cdf.attrs["IMPAX_Quality"] = "Tenuous and preliminary"

    # for some reason type=pycdf.const.CDF_TIME_TT2000 does not work here.
    # cdf.attrs["Epoch"] = 0
    # cdf.attrs["Epoch"].type = pycdf.const.CDF_EPOCH

    return cdf


def cdf_make_epoch(fields, cdf):
    # todo: check here for rollover of CCSDS_SEQUENCE_COUNT in here, correct for it.
    # in a way that is tolerant packet loss. But still correct. Good luck.
    # determine ordering of all packets, based on the CCSDS sequence counter.

    # order = fields["CCSDS_SEQUENCE_COUNT"].argsort()
    ct = fields["Coarse Time"]  # [order]
    ft = fields["Coarse Time"]  # [order]

    # time = cdf.new("time", type=pycdf.const.CDF_DOUBLE, recVary=True)
    t = 1e9 * (ct + ft / 1000)  # in ns

    epoch = cdf.new("Epoch", type=pycdf.const.CDF_TIME_TT2000, recVary=True)
    epoch[...] = t
    epoch.attrs["MONOTON"] = "INCREASE"
    epoch.attrs["VAR_TYPE"] = "support_data"
    epoch.attrs["LABLAXIS"] = "Epoch"
    epoch.attrs["UNITS"] = "ns"
    epoch.attrs["SCALETYP"] = "linear"
    epoch.attrs["TIME_BASE"] = "J2000"
    epoch.attrs["TIME_SCALE"] = "Terrestrial Time"
    epoch.attrs["DICT_KEY"] = "SPASE>Support>SupportQuantity:Temporal"
    return cdf


def cdf_from_220(fields, src_file: str, save_path: str):
    cdf = cdf_defaults_hk(save_path)
    cdf = cdf_make_epoch(fields, cdf)

    return cdf


def cdf_from_221(fields, src_file: str, save_path: str):
    pass


def cdf_from_222(fields, src_file: str, save_path: str):
    pass


def cdf_from_252(fields, src_file: str, save_path: str):
    cdf = cdf_defaults_sci(save_path)
    cdf = cdf_make_epoch(fields, cdf)

    # add the pixel list
    pix = cdf.new("Pixels", type=pycdf.const.CDF_UINT1, recVary=True)
    pix[...] = range(0, 256, 1)
    pix.attrs["VAR_TYPE"] = "support_data"
    pix.attrs["FIELDNAM"] = "Pixel Index"
    pix.attrs["DEPEND_0"] = "Epoch"
    pix.attrs["LABLAXIS"] = "Pixel Index"
    pix.attrs["UNITS"] = ""

    # add the energy bins
    pix = cdf.new("ADC", type=pycdf.const.CDF_UINT1, recVary=True)
    pix[...] = range(0, 2**6 - 1, 1)
    pix.attrs["VAR_TYPE"] = "support_data"
    pix.attrs["FIELDNAM"] = "Raw ADC Value"
    pix.attrs["DEPEND_0"] = "Epoch"
    pix.attrs["LABLAXIS"] = "Raw ADC"
    pix.attrs["UNITS"] = ""

    # add the image data, which references the pixel and energy variables
    # bins = cdf.new("Bins", type=pycdf.const.CDF_BYTE, recVary=True)
    cdf["Bins"] = fields["Pixel Data"]
    cdf["Bins"].attrs["VAR_TYPE"] = "data"
    cdf["Bins"].attrs["FIELDNAM"] = "Per-pixel ADC value"
    cdf["Bins"].attrs["CATDESC"] = (
        "Per-pixel ADC value for 256 pixels, each 6 bits deep."
    )
    # note: this is a 1D list of pixels at each timestep, not yet a 2D image.
    cdf["Bins"].attrs["UNITS"] = ""
    cdf["Bins"].attrs["DEPEND_0"] = "Epoch"
    cdf["Bins"].attrs["DEPEND_1"] = "Pixels"
    # bins.attrs["DEPEND_2"] = "ADC"

    cdf["Bins"].attrs["LABLAXIS"] = "ADC Count"

    cdf["Bins"].attrs["DICT_KEY"] = "SPASE>Huh"
    cdf["Bins"].attrs["DISPLAY_TYPE"] = (
        "spectrogram>y=energy,z=Bins(*,1),z=Bins(*,7),z=Bins(*,12)"
    )

    cdf["Bins"].attrs["AVG_TYPE"] = "standard"
    cdf["Bins"].attrs["SCALETYP"] = "linear"

    return cdf


cdf_writer_lookup = {
    0x220: cdf_from_220,
    0x221: cdf_from_221,
    0x222: cdf_from_222,
    0x252: cdf_from_252,
}


# todo: make this depot path for CDF L0 globally configurable.
def cdf_from_apid(
    apid: int,
    packet: dict,
    src_file: str,
    save_path: str = os.path.join(os.path.dirname(__file__), "..", "data", "log"),
):
    # if apid != packet["CCSDS_APID"]:
    #     raise ValueError

    cdf = cdf_writer_lookup[apid](packet, src_file, save_path)
    cdf.close()
    print(f"wrote {cdf.pathname}")
