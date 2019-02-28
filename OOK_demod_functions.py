#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Name:         OOK_demod_functions
# Purpose:      Example code for demodulating an OOK signal using RTL-SDR
#
# Author:       yramgulam
#
# Created:      28/02/2019
# Copyright:    (c) yramgulam2019
# Licence:      <your licence>
#-------------------------------------------------------------------------------

import numpy as np
import scipy.signal

# ----------------------------------------------------------------

def clock_recovery(data, DataRate, SamplingRate):

    sps             = int(SamplingRate/DataRate)
    clock           = []
    synced_data     = []
    error           = 1
    index           = 0
    epsilon         = 0
    Kp              = -sps/2

    while (index*sps + epsilon) < len(data) - sps :

        # This is Gardner formula
        error = (data[index*sps + epsilon] - data[(index-1)*sps + epsilon]) * data[index*sps - sps//2 + epsilon] 
        
        # We apply a gain to the error 
        epsilon += int(np.round(error*Kp))

        # and we store the result
        clock.append(int(index*sps + epsilon))
        synced_data.append(data[int(index*sps + epsilon)])

        index += 1
    
    return synced_data, clock

# ------------------------------------------------------------------------

def search_sync(data, sync_word, preamble_pattern = 'AA', nb_preamble_bytes=2, sync_threshold=12):
    """
        data                : array containing the data
        sync_word           : hex string, MSB first, WITHOUT '0x'. Example : AE55 for 0xAE 0x55
        preamble_pattern    : hex string, MSB first, WITHOUT '0x'. Example : AA for 0xAA
        nb_preamble_bytes   : number of preamble bytes to consider
        sync_threshold      : threshold level to validate correlation
  
        returns : index of sync if success
      
    """
    # Variables
    sync_string = nb_preamble_bytes*preamble_pattern + sync_word
    sync_number = int(sync_string, 16)
    sync_index  = 0

    # Format HEX sync word & preamble into array of bits
    spec            = '{fill}{align}{width}{type}'.format(fill='0', align='>', width=len(sync_string)//2*8, type='b')
    sync_bit_string = format(sync_number,spec)
    
    sync_bit_list   = [0]*len(sync_bit_string)
    for i in range(0,len(sync_bit_string)):
        sync_bit_list[i] = int(sync_bit_string[i])

    # correlation
    synchronisation_sequence = np.repeat(sync_bit_list, 1) # Generation of reference sequence
    correlated_data = scipy.signal.correlate(data, synchronisation_sequence, mode='same')

    # decision
    for i in range(1,len(correlated_data)-1):
        # if we have a peak above the threshold
        if (correlated_data[i] > sync_threshold):
            # We check that the neighbouring peaks are sufficiently lower
            if (correlated_data[i] - correlated_data[i-1] > sync_threshold) and (correlated_data[i] - correlated_data[i+1] > sync_threshold) :
                sync_index = i
                payload_start = i + int(np.ceil(len(synchronisation_sequence)/2))
                print("SYNC found at index ", sync_index,"/ ",len(correlated_data))
                print("PAYLOAD starts at index ", payload_start,"/ ",len(correlated_data))
                print("Correlation level is ", correlated_data[i] - correlated_data[i-1])
            else :
                pass
        else:
            pass
          
    return sync_index, payload_start, correlated_data

# ------------------------------------------------------------

def payload_extraction(data, sync_index, payload_size=0):

    payload_hex     = [0]*payload_size
    payload_data    = 0

    for j in range(0, payload_size):

        payload_data = 0
        k = 7

        for i in range(sync_index + j*8, sync_index + j*8 + 8):
            payload_data += int(data[i]) << k
            k -= 1
            
        payload_hex[j] = hex(payload_data)
          
    print("Payload = ",payload_hex)

    return payload_hex