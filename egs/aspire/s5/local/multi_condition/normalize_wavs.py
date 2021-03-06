#!/usr/bin/env python
# Copyright 2014  Johns Hopkins University (Authors: Vijayaditya Peddinti).  Apache 2.0.

# normalizes the wave files provided in input file list with a common scaling factor
# the common scaling factor is computed to 1/\sqrt(1/(total_samples) * \sum_i{\sum_j x_i(j)^2}) where total_samples is sum of all samples of all wavefiles. If the data is multi-channel then each channel is treated as a seperate wave files
import argparse, scipy.io.wavfile, warnings, numpy as np, math

def normalize(file_list, is_rir, additional_scaling):
  assert(len(file_list) > 0)
  sampling_rate = None
  total_energy = 0.0
  total_samples = 0.0
  for file in file_list:
    try:
      [rate, data] = scipy.io.wavfile.read(file)
      if len(data.shape) == 1:
        data = data.reshape([data.shape[0], 1])
      if sampling_rate is not None:
        assert(rate == sampling_rate)
      else:
        sampling_rate = rate
      if is_rir:
        # just count the energy of the direct impulse response
        # this is treated as energy of signal from 0.001 seconds before impulse
        # to 0.05 seconds after impulse. This is done as we do not want the 
        # recording length to influence the scaling factor
        channel_one = data[:, 0]
        max_d = max(channel_one)
        delay_impulse = [i for i, j in enumerate(channel_one) if j == max_d][0]
        before_impulse = np.floor(rate * 0.001)
        after_impulse = np.floor(rate * 0.05)
        start_index = max(0, delay_impulse - before_impulse)
        end_index = min(len(channel_one), delay_impulse + after_impulse)
      else:
        start_index = 0
        end_index = data.shape[0]
      total_energy += float(np.sum(data[start_index:end_index, :] ** 2))
      data_shape = list(data.shape)
      data_shape[0] = end_index-start_index
      total_samples += float(np.prod(data_shape))
    except IOError:
      warnings.warn("Did not find the file {0}.".format(file))
  assert(total_samples > 0)
  scaling_coefficient = np.sqrt(total_samples / total_energy)
  print "Scaling coefficient is {0}.".format(scaling_coefficient)
  if math.isnan(scaling_coefficient):
    raise Exception(" Nan encountered while computing scaling coefficient. This is mostly due to numerical overflow")
  for file in file_list:
    [rate, data] = scipy.io.wavfile.read(file)
    scipy.io.wavfile.write(file, rate, data * scaling_coefficient * additional_scaling)

if __name__ == "__main__":
  usage = """ Python script to normalize input wave file list"""

  parser = argparse.ArgumentParser(usage)
  parser.add_argument('--is-room-impulse-response', type=str, default = "false",  help='is the input a list of room impulse responses', choices = ['True', 'False', 'true', 'false'])
  parser.add_argument('--extra-scaling-factor', type=float, default = 1.0,  help='additional scaling factor to be multiplied with the wav files')
  parser.add_argument('input_file_list', type=str, help='list of wav files to be normalized collectively')
  params = parser.parse_args() 
  if params.is_room_impulse_response.lower() == 'true':
    params.is_room_impulse_response = True
  else:
    params.is_room_impulse_response = False

  file_list = []
  for line in  open(params.input_file_list).readlines():
    if len(line.strip()) > 0 :
      file_list.append(line.strip())
  normalize(file_list, params.is_room_impulse_response, params.extra_scaling_factor)
