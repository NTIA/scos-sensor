# YML-Defined Action Initialization

Actions can be manually initialized in [actions/__init__.py](../../src/actions/__init__.py), but an easier method for non-developers and configuration-management software is to place a YAML file in this directory which contains the action class name and parameter definitions.

The file name can be anything. Files must end in `.yml`.

The action initialization logic parses all YAML files in this directory and registers the requested actions in the API.

Let's look at an example.

## Example

Let's say we want to make an instance of the [SingleFrequencyfftAcquisition](../../src/actions/acquire_single_freq_fft.py).

First, create a new YAML file in this directory. In this example we're going to create an acquisition for the LTE 700c band downlink, so we'll call it `acquire_700c_dl.yml`.

Next, we want to find the appropriate string key for the `SingleFrequencyfftAcquisition` class. Look in [actions/__init__.py](../../src/actions/__init__.py) at the `action_classes` dictionary. There, we see:

```python
action_classes = {
    ...
    "single_frequency_fft": acquire_single_freq_fft.SingleFrequencyFftAcquisition,
    ...
}
```

That key tells the action loader which class to create an instance of. Put it as the first non-comment line, followed by a colon:

```yaml
# File: acquire_700c_dl.yml

single_frequency_fft:
```

The next step is to see what parameters that class takes and specify the values. Open up [actions/acquire_single_freq_fft.py](../../src/actions/acquire_single_freq_fft.py) and look at the documentation for the class to see what parameters are available and what units to use, etc.

```python
class SingleFrequencyFftAcquisition(Action):
    """Perform m4s detection over requested number of single-frequency FFTs.

    :param name: the name of the action
    :param frequency: center frequency in Hz
    :param gain: requested gain in dB
    :param sample_rate: requested sample_rate in Hz
    :param fft_size: number of points in FFT (some 2^n)
    :param nffts: number of consecutive FFTs to pass to detector

    """
    ...
```

Lastly, simply modify the YAML file to define any required parameters.

```yaml
# File: acquire_700c_dl.yml

single_frequency_fft:
    name: acquire_700c_dl
    frequency: 751e6
    gain: 40
    sample_rate: 15.36e6
    fft_size: 1024
    nffts: 300
```

You're done. You can define multiple actions in a single file.
