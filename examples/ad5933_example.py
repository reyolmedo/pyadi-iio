# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import argparse
import math

from adi.ad5933 import ad5933

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AD5933 basic frequency-sweep example")
    parser.add_argument(
        "--uri",
        type=str,
        default="serial:/dev/ttyACM0,57600,8n1",
        help="IIO context URI. Use 'ip:<address>' for Ethernet"
        " or 'serial:<port>,<baud>,8n1' for USB serial.",
    )
    parser.add_argument(
        "--gain-factor",
        type=float,
        default=None,
        help="Calibration gain factor from a known reference impedance."
        " If given, |Z| is reported in ohms.",
    )
    args = parser.parse_args()

    ################################################################################
    # Use this with MCUs running tinyiiod and make sure to use the correct com port.
    dev = ad5933(uri=args.uri)

    # Configure the sweep.
    dev.output_range = 0  # 0 = 2000 mVpp, 1 = 200 mVpp, 2 = 400 mVpp, 3 = 1000 mVpp
    dev.pga_gain = 1  # 0 = x5, 1 = x1
    dev.start_frequency = 30000
    dev.frequency_increment = 100
    dev.frequency_points = 50
    dev.settling_cycles = 50
    dev.measure_mode = 1  # 0 = single, 1 = sweep
    dev.settling_cycles_multiplier = 0  # 0 = x1, 1 = x2, 3 = x4

    print("AD5933 configuration")
    print("  Start frequency:     " + str(dev.start_frequency) + " Hz")
    print("  Frequency increment: " + str(dev.frequency_increment) + " Hz")
    print("  Frequency points:    " + str(dev.frequency_points))
    print("  Output range code:   " + str(dev.output_range))
    print("  PGA gain code:       " + str(dev.pga_gain))
    print("  Measure mode:        " + str(dev.measure_mode))

    # Temperature reading.
    temp_c = dev.temp.raw * dev.temp.scale
    print("  Die temperature:     " + str(round(temp_c, 2)) + " C")

    # Capture one full sweep. Channel 0 = real, channel 1 = imaginary.
    dev.rx_enabled_channels = [0, 1]
    dev.rx_buffer_size = dev.frequency_points + 1

    dev.sweep_initialized = 1  # Load start frequency and settle.
    dev.sweep_started = 1  # Begin the frequency sweep.

    if int(dev.measure_mode) == 0:
        # Single mode: read one impedance point straight from the data registers.
        single_raw = dev.real.raw
        single_imaginary = dev.imaginary.raw
        print()
        print("Single measurement")
        print("  Single read (Real):      " + str(round(single_raw, 2)))
        print("  Single read (Imaginary): " + str(round(single_imaginary, 2)))
    else:
        # Sweep mode: capture the full buffered sweep once it completes.
        while dev.sweep_started:
            pass

        real, imaginary = dev.rx()

        print()
        print("Sweep results")
        start = dev.start_frequency
        increment = dev.frequency_increment
        for i, (re, im) in enumerate(zip(real, imaginary)):
            freq = start + i * increment
            magnitude = math.hypot(float(re), float(im))
            phase_deg = math.degrees(math.atan2(float(im), float(re)))
            line = (
                "  f="
                + str(freq)
                + " Hz  real="
                + str(re)
                + "  imag="
                + str(im)
                + "  |M|="
                + str(round(magnitude, 2))
                + "  phase="
                + str(round(phase_deg, 2))
                + " deg"
            )
            if args.gain_factor:
                impedance = (
                    1.0 / (args.gain_factor * magnitude) if magnitude else float("inf")
                )
                line += "  |Z|=" + str(round(impedance, 2)) + " ohm"
            print(line)

    del dev
