#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Name:         OOK_demod_article
# Purpose:      Example code for demodulating an OOK signal using RTL-SDR
#
# Author:       yramgulam
#
# Created:      28/02/2019
# Copyright:    (c) yramgulam2019
# Licence:      <your licence>
#-------------------------------------------------------------------------------

import OOK_demod_functions as functions

import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
from scipy.io import wavfile
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import time

# --- Constants
bitrate         = 5000
DecimationRatio = 10

# --- read wav_file
Fs, data = wavfile.read('./_WAV/keyfob_iq_ook.wav')
data = data/np.amax(data)

I_data = data[:,0]
Q_data = data[:,1]

I_data = I_data[130000:185022] # I'm only interested in this part 
Q_data = Q_data[130000:185022] # I'm only interested in this part

# --- This is the original complex IQ stream
complex_data = I_data + 1j*Q_data

# --- Decimate data to improve SNR and reduce computing load
# We decimate by 10 i.e. 2e6/10 = 200kHz output bandwidth
decimated_data = scipy.signal.decimate(complex_data, DecimationRatio, ftype='iir')

# This is just for the sake of plotting, to show the difference
# between original signal and decimated signal on the same scale
interpolated_data = scipy.signal.resample_poly(decimated_data, DecimationRatio,1) 

# --- demodulate (extract magnitude)
data_magnitude = np.abs(decimated_data)

# --- Matched filtering
samples_per_bit = int(Fs/DecimationRatio/bitrate) # Calculate number of samples per bit
reference_pulse = np.repeat([1], samples_per_bit) # Create reference pulse of length "samples_per_bit"
matched_data = scipy.signal.correlate(data_magnitude, reference_pulse, mode='same') / samples_per_bit # Correlate

# --- Eliminate DC component and slice data resulting in samples between +/-0.5
matched_data /= np.amax(matched_data)
ac_data = matched_data - np.average(matched_data)

# --- synchronize bit stream
synced_data, clock = functions.clock_recovery(data=ac_data, DataRate=bitrate, SamplingRate=Fs/DecimationRatio)

# --- Recover bits
recovered_bits = []
for bit in synced_data:
    if bit > 0:
        recovered_bits.append(1)
    else:
        recovered_bits.append(0)

print("recovered bits = ", recovered_bits)

# --- frame synchronisation : Look for synchronisation word
SynchroFrameIndex, PayloadStart, SynchroFrameResult = functions.search_sync(recovered_bits,'DB6A', sync_threshold=12)

# --- payload decoding
payload = functions.payload_extraction(recovered_bits, PayloadStart, payload_size=9)

# --- Plot results
fig, (ax_iq, ax_mag) = plt.subplots(2, 1, sharex=False)
fig2, (ax_match, ax_clocksync, ax_framesync) = plt.subplots(3, 1, sharex=False)

ax_iq.plot(I_data+2.5, label='I (Fs=2Msps)')
ax_iq.plot(Q_data, label='Q (Fs=2Msps)')
ax_iq.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=1, mode=None, borderaxespad=0.)

ax_mag.plot(np.abs(complex_data), label='demodulated signal - before decimation')
ax_mag.plot(np.abs(interpolated_data), label='demodulated signal - after x10 decimation')
ax_mag.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=1, mode=None, borderaxespad=0.)

ax_match.plot(data_magnitude, label='Demodulated data')
ax_match.plot(matched_data, label='match-filtered data')
ax_match.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=1, mode=None, borderaxespad=0.)

ax_clocksync.plot(ac_data, label='dc-blocked data')
ax_clocksync.plot(clock,synced_data, 'ro', label='clock-synchronized data')
ax_clocksync.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=1, mode=None, borderaxespad=0.)

ax_framesync.plot(SynchroFrameResult, label='SynchroFrame correlation')
ax_framesync.plot(SynchroFrameIndex,SynchroFrameResult[SynchroFrameIndex], 'ro', label='clock-synchronized data')
ax_framesync.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=1, mode=None, borderaxespad=0.)

fig2.tight_layout()
fig.tight_layout()
plt.show()


