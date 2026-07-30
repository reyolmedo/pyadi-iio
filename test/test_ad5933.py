import pytest

import adi

hardware = ["ad5933"]
classname = "adi.ad5933"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_ad5933_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 5)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("real", "raw"),
        ("imaginary", "raw"),
        ("temp", "raw"),
        ("temp", "scale"),
        ("temp", "processed"),
    ],
)
def test_ad5933_attr_readonly_channel(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("attr", [("sweep_done")])
def test_ad5933_attr_readonly(
    test_attribute_single_value_readonly, iio_uri, classname, attr
):
    test_attribute_single_value_readonly(iio_uri, classname, attr, 1)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("pga_gain", 0, 1, 1, 0, 2),
        ("output_range", 0, 3, 1, 0, 4),
        ("start_frequency", 1000, 100000, 1000, 0, 3),
        ("frequency_increment", 1, 1000, 1, 0, 3),
        ("frequency_points", 1, 511, 1, 0, 3),
        ("settling_cycles", 0, 511, 1, 0, 3),
        ("settling_multiplier", 0, 1, 1, 0, 2),
        ("sweep_start", 0, 1, 1, 0, 2),
    ],
)
def test_ad5933_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats
    )
