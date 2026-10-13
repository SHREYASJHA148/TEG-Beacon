"""SI units. Positive current means power delivered by the loaded TEG."""
from datetime import datetime

MET = {'Walking': 3.5, 'Cycling': 6.0, 'Strength training': 3.5, 'Running': 8.0}

def power(voltage, current, quality='valid', point='teg_loaded'):
    if voltage is None or current is None or quality != 'valid' or point != 'teg_loaded':
        return None
    return voltage * current

def integrate(samples, max_gap=15):
    total, gaps = 0.0, 0
    for a, b in zip(samples, samples[1:]):
        dt = (datetime.fromisoformat(b['timestamp']) - datetime.fromisoformat(a['timestamp'])).total_seconds()
        pa = power(a['voltage_v'], a['current_a'], a['quality'], a['measurement_point'])
        pb = power(b['voltage_v'], b['current_a'], b['quality'], b['measurement_point'])
        if 0 < dt <= max_gap and pa is not None and pb is not None:
            total += (pa + pb) * .5 * dt
        elif dt != 0:
            gaps += 1
    return total, gaps

def capacitor(capacitance, voltage, low, high):
    if not .22 <= capacitance <= 1 or not 0 <= low < high <= 5:
        raise ValueError('Require 0.22–1 F and 0 ≤ low < high ≤ 5 V')
    if voltage is None or not 0 <= voltage <= high:
        return None, None
    return .5 * capacitance * voltage**2, .5 * capacitance * max(0, voltage**2 - low**2)

def calories(activity, mass, seconds):
    return MET[activity] * 3.5 * mass / 200 * seconds / 60
