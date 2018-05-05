import math

import numpy as np
from matplotlib import pyplot as plt
from numpy import ma as ma


def get_family_harmonics(freqs, freq_step, chosen_f, h):
    lower_f = chosen_f - freq_step / 2
    upper_f = chosen_f + freq_step / 2
    fund_lower = int(lower_f / h)
    fund_upper = int(upper_f / h) + 1
    delta_fund = (fund_upper - fund_lower) / 2 / (fund_lower + fund_upper) / 2

    approx_match = []
    if delta_fund < 0.05:
        for f in freqs:
            if f <= int(f / fund_lower) * fund_upper:
                approx_match.append(f)

    return [fund_lower, fund_upper], approx_match


def eval_fund(freqs, fund_lower_bound, fund_upper_bound, freq_step):
    fund_lower_bound -= fund_lower_bound % freq_step
    fund_upper_bound += freq_step - fund_upper_bound % freq_step

    fund_diaps = {}
    for f in freqs:
        magnitude = math.log10(f[1])
        prob_harmonic_min = max(int(f[0] / fund_upper_bound), 1)
        prob_harmonic_max = int(f[0] / fund_lower_bound)
        if prob_harmonic_max < 3:
            continue  # хотим иметь хотя бы две кратных вниз, иначе низкая точность

        for h in range(prob_harmonic_max, prob_harmonic_min, -1):
            fund_low, fund_high = (f[0] - freq_step / 2) / h, (f[0] + freq_step / 2) / h
            fund_diaps[fund_low], fund_diaps[fund_high] = magnitude, -magnitude

    summary = 0
    x = []
    y = []
    sor = sorted(fund_diaps.items(), key=lambda i: i[0])
    for d in sor:
        summary += d[1]
        x.append(d[0])
        y.append(summary)
    fig = plt.figure(figsize=[4, 4], frameon=False)
    ax = fig.add_subplot(111)
    ax.plot(x, y)
    # fig.show()

    fund = 0

    return fund


def analyse_spectrum(intensity):
    freq_step = 16
    fund_lower_bound = 80
    fund_upper_bound = 300
    n_main_comp = 30

    indices = np.arange(intensity.size)
    ind_round = int(fund_lower_bound / freq_step / 2)

    important = []
    intensity = ma.masked_where(indices < fund_lower_bound / freq_step, intensity)
    for n in range(0, n_main_comp):
        max_intensity = np.argmax(intensity)
        important.append((max_intensity * freq_step, intensity.max()))
        intensity = ma.masked_where(abs(indices - max_intensity) <= ind_round, intensity)

    freq = np.array(important)[:, 0]

    print('seq_search: ' + str(sequential_search(freq, freq_step, fund_lower_bound, fund_upper_bound)))

    return freq, eval_fund(important, fund_lower_bound, fund_upper_bound, freq_step)


def calc_intersect(fund_min, fund_max, band_left, band_right):
    right_corner = fund_max * int(band_left / fund_min)
    next_left_corner = fund_min * (int(band_left / fund_min) + 1)
    intersect = 0
    if band_left < right_corner:
        intersect += min(band_right, right_corner) - band_left
        if band_right > next_left_corner:
            intersect += band_right - next_left_corner
    else:
        if band_right > next_left_corner:
            next_right_corner = fund_max * (int(band_left / fund_min) + 1)
            intersect += min(next_right_corner, band_right) - next_left_corner
    intersect /= band_right - band_left
    return intersect


def analyse_bands(intensity, freq_step, lower_bound, upper_bound, n_parts):
    total_energy = math.fsum(intensity)
    width = (upper_bound - lower_bound) / n_parts
    statistics = {}
    for p in range(0, n_parts):
        chosen_energy, ch = 0, 0
        freq_min = lower_bound + p * width
        freq_max = freq_min + width
        for f in range(0, intensity.size):
            freq = f * freq_step
            inter = calc_intersect(freq_min, freq_max, freq - freq_step / 2, freq + freq_step / 2)
            chosen_energy += intensity[f] * inter
            ch += inter
        statistics[(freq_min, freq_max)] = chosen_energy / total_energy / ch / intensity.size
    print(sorted(statistics.items(), key=lambda i: i[1]))


def sequential_search(freqs, freq_step, lower_bound, upper_bound):
    fund = lower_bound
    count = 0
    for w in range(upper_bound, lower_bound, -1):
        new_count = 0
        for f in freqs:
            if f % w < freq_step / 2 or w - f % w < freq_step / 2:
                new_count += 1
        if new_count > count:
            fund = w
            count = new_count
    return fund