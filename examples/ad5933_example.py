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
        help="Precomputed calibration gain factor. If given, calibration is"
        " skipped and |Z| is reported in ohms.",
    )
    parser.add_argument(
        "--calibration-impedance",
        type=float,
        default=None,
        help="Known reference impedance in ohms connected during calibration."
        " Used to measure the gain factor before the sweep.",
    )
    args = parser.parse_args()

    ################################################################################
    # Use this with MCUs running tinyiiod and make sure to use the correct com port.
    dev = ad5933(uri=args.uri)

    # Configure the sweep.
    dev.output_range = 0  # 0 = 2000 mVpp, 1 = 200 mVpp, 2 = 400 mVpp, 3 = 1000 mVpp
    dev.pga_gain = 1  # 0 = x5, 1 = x1
    dev.start_frequency = 30000
    dev.frequency_increment = 500
    dev.frequency_points = 10
    dev.settling_cycles = 50
    dev.measure_mode = 1  # 0 = single, 1 = sweep (buffered rx() requires sweep)
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

    def run_sweep():
        """Trigger one full frequency sweep and return (real, imaginary) lists."""
        dev.sweep_initialized = 1  # Load start frequency and settle.
        dev.sweep_started = 1  # Begin the frequency sweep.
        return dev.rx()

    def measure_gain_factors(calibration_impedance):
        """Measure a per-point AD5933 gain factor from a known reference.

        Running a full sweep against a known impedance yields one gain factor
        per frequency point:
            GF[i] = 1 / (|M_cal[i]| * Z_cal)
        so impedance at each point is recovered as Z[i] = 1 / (GF[i] * |M[i]|).
        Per-point calibration corrects the AD5933 gain variation with frequency
        (see datasheet Rev. F, "Gain Factor Variation with Frequency", p. 17).
        """
        cal_real, cal_imaginary = run_sweep()
        gfs = []
        for re, im in zip(cal_real, cal_imaginary):
            magnitude = math.hypot(float(re), float(im))
            gfs.append(1.0 / (magnitude * calibration_impedance) if magnitude else 0.0)
        avg = sum(gfs) / len(gfs) if gfs else 0.0
        print("Measured " + str(len(gfs)) + " per-point gain factors (avg=" + str(avg) + ")")
        return gfs

    # Determine the gain factor(s) before the sweep. A precomputed scalar takes
    # priority; otherwise measure a per-point array from a known impedance.
    gain_factors = None
    calibrated = False
    if args.gain_factor is not None:
        gain_factors = [args.gain_factor]  # Single value applied to every point.
    elif args.calibration_impedance is not None:
        print()
        print("Connect the " + str(args.calibration_impedance) + " ohm reference impedance.")
        input("Press Enter to start calibration...")
        gain_factors = measure_gain_factors(args.calibration_impedance)
        calibrated = True

    # If we just calibrated against a reference, pause so the reference can be
    # swapped for the device under test before the measurement sweep.
    if calibrated:
        print()
        input("Connect the device under test and press Enter to start the sweep...")

    # Run the measurement sweep on the device under test.
    real, imaginary = run_sweep()

    print()
    print("Sweep results")
    start = dev.start_frequency
    increment = dev.frequency_increment
    for i, (re, im) in enumerate(zip(real, imaginary)):
        freq = start + i * increment
        mag = math.hypot(float(re), float(im))
        phase_deg = math.degrees(math.atan2(float(im), float(re)))
        line = (
            "  f="
            + str(freq)
            + " Hz  real="
            + str(re)
            + "  imag="
            + str(im)
            + "  |M|="
            + str(round(mag, 2))
            + "  phase="
            + str(round(phase_deg, 2))
            + " deg"
        )
        if gain_factors:
            # Use the matching per-point gain factor; fall back to the last one
            # (also covers the single-value/scalar case).
            gf = gain_factors[i] if i < len(gain_factors) else gain_factors[-1]
            impedance = 1.0 / (gf * mag) if (gf and mag) else float("inf")
            line += "  |Z|=" + str(round(impedance, 2)) + " ohm"
        print(line)

    del dev
