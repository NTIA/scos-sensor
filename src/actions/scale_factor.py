import logging

import csv

logger = logging.getLogger(__name__)


class ScaleFactors(object):

    # Initialize the class and load the file if given
    def __init__(self, fname=None, default=1):
        self.scale_factor_file = fname
        self.default_scale_factor = default

        # Load defaults
        self.scale_factors_loaded = False
        self.scale_factor_divisions = None
        self.scale_factor_gains = None
        self.scale_factor_frequencies = None
        self.scale_factor_matrix = None

        # If a filename canme, try and load
        if fname is not None:
            self._load_scale_factor_csv(fname)

    def _load_scale_factor_csv(self, fname):
        # In case loading is unsuccessful, assume failure
        self.scale_factors_loaded = False

        # Instantiate scale factor arrays/matrix
        self.scale_factor_divisions = []
        self.scale_factor_gains = []
        self.scale_factor_frequencies = []
        self.scale_factor_matrix = []

        # Load data from file
        logger.debug("Loading scale factor data from '{}'".format(fname))
        with open(fname, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                # Skip an empty row
                if len(row) < 1:
                    continue

                # Check for a division row
                if row[0] == 'div':
                    try:
                        lb = float(row[1])
                        ub = float(row[2])
                        div = [lb, ub]
                        self.scale_factor_divisions.append(div)
                    except IndexError:
                        err = "Scale factor file improperly formatted.\r\n"
                        err += "Divisions need 2 bounds."
                        raise IndexError(err)
                    continue

                # Check for the list of gains
                if row[0] == '' or row[0] == 'freqs\gains':
                    for i in range(len(row)-1):
                        self.scale_factor_gains.append(float(row[i+1]))
                    continue

                # Must be a frequency row
                self.scale_factor_frequencies.append(float(row[0]))
                self.scale_factor_matrix.append([])
                for i in range(len(row)-1):
                    try:
                        self.scale_factor_matrix[-1].append(float(row[i+1]))
                    except ValueError:
                        err = "Scale factor file improperly formatted.\r\n"
                        err += "Invalid scale factor data '{}' at\r\n"
                        err = err.format(str(row[i+1]))
                        err += "freq {}Hz in column {}."
                        err = err.format(self.scale_factor_frequencies[-1], i)
                        raise ValueError(err)
            f.close()

        # Check that all divisions consist of two values
        for i in range(len(self.scale_factor_divisions)):
            div_len = len(self.scale_factor_divisions[i])
            if not div_len == 2:
                err = "Scale factor file improperly formatted.\r\n"
                err += "Division only has {} of 2 required bounds."
                err = err.format(div_len)
                raise RuntimeError(err)

        # Check that frequency and gain arrays were populated
        if len(self.scale_factor_gains) < 1:
            err = "Scale factor file improperly formatted.\r\n"
            err += "No gain values given."
            raise RuntimeError(err)
        if len(self.scale_factor_frequencies) < 1:
            err = "Scale factor file improperly formatted.\r\n"
            err += "No frequency values given."
            raise RuntimeError(err)

        # Check that the number of frequencies matches the SF matrix
        l1 = len(self.scale_factor_frequencies)
        l2 = len(self.scale_factor_matrix)
        if not l1 == l2:
            err = "Scale factor file improperly formatted.\r\n"
            err += "Number of frequencies ({}) does not match "
            err += "row in SF matrix ({})."
            err = err.format(l1, l2)
            raise RuntimeError(err)

        # Check that the number of gains matches the SF matrix
        for i in range(len(self.scale_factor_frequencies)):
            l1 = len(self.scale_factor_matrix[i])
            l2 = len(self.scale_factor_gains)
            if not l1 == l2:
                err = "Scale factor file improperly formatted.\r\n"
                err += "Number of gains ({}) does not match row in "
                err += "SF matrix ({})\r\nin frequency row {} ({}Hz)."
                err = err.format(l2, l1, i, self.scale_factor_frequencies[i])
                raise RuntimeError(err)

        # Sort the data
        sfm = self.scale_factor_matrix
        sfg = self.scale_factor_gains
        sff = self.scale_factor_frequencies
        (sfm, sfg, sff) = self.sort_matrix_by_lists(sfm, sfg, sff)
        self.scale_factor_matrix = sfm
        self.scale_factor_gains = sfg
        self.scale_factor_frequencies = sff

        # Successfully loaded the scale factor file
        self.scale_factors_loaded = True
        return

    # Interpolate to get the power scale factor
    def get_power_scale_factor(self, lo_frequency, gain):
        """
            Find the scale factor closest to the current frequency/gain.
        """

        # Get the LO and gain for the usrp
        f = lo_frequency
        g = gain

        # Get the gain index for the SF interpolation
        g_i = 0
        bypass_gain_interpolation = True
        if g <= self.scale_factor_gains[0]:
            g_i = 0
        elif g >= self.scale_factor_gains[-1]:
            g_i = len(self.scale_factor_gains)-1
        else:
            bypass_gain_interpolation = False
            for i in range(len(self.scale_factor_gains)-1):
                if self.scale_factor_gains[i+1] > g:
                    g_i = i
                    break

        # Get the frequency index range for the SF interpolation
        f_i = 0
        bypass_freq_interpolation = True
        if f <= self.scale_factor_frequencies[0]:
            f_i = 0
        elif f >= self.scale_factor_frequencies[-1]:
            f_i = len(self.scale_factor_frequencies)-1
        else:
            # Narrow the frequency range to a division
            bypass_freq_interpolation = False
            f_div_min = self.scale_factor_frequencies[0]
            f_div_max = self.scale_factor_frequencies[-1]
            for i in range(len(self.scale_factor_divisions)):
                if f >= self.scale_factor_divisions[i][1]:
                    f_div_min = self.scale_factor_divisions[i][1]
                else:
                    # Check if we are in the division
                    if f > self.scale_factor_divisions[i][0]:
                        logger.warning("SDR tuned to within a division:")
                        logger.warning("    LO frequency: {}".format(f))
                        msg = "    Division: [{},{}]"
                        lb = self.scale_factor_divisions[i][0]
                        ub = self.scale_factor_divisions[i][1]
                        msg = msg.format(lb, ub)
                        logger.warning(msg)
                        msg = "Assumed scale factor of lower boundary."
                        logger.warning(msg)
                        f_div_min = self.scale_factor_divisions[i][0]
                        f_div_max = self.scale_factor_divisions[i][0]
                        bypass_freq_interpolation = True
                    else:
                        f_div_max = self.scale_factor_divisions[i][0]
                    break
            # Determine the index associated with the frequency/ies
            for i in range(len(self.scale_factor_frequencies)-1):
                if self.scale_factor_frequencies[i] < f_div_min:
                    continue
                if self.scale_factor_frequencies[i+1] > f_div_max:
                    f_i = i
                    break
                if self.scale_factor_frequencies[i+1] > f:
                    f_i = i
                    break

        # Interpolate as needed
        if bypass_gain_interpolation and bypass_freq_interpolation:
            scale_factor = self.scale_factor_matrix[f_i][g_i]
        elif bypass_freq_interpolation:
            scale_factor = self.interpolate_1d(
                g,
                self.scale_factor_gains[g_i],
                self.scale_factor_gains[g_i+1],
                self.scale_factor_matrix[f_i][g_i],
                self.scale_factor_matrix[f_i][g_i+1]
            )
        elif bypass_gain_interpolation:
            scale_factor = self.interpolate_1d(
                f,
                self.scale_factor_frequencies[f_i],
                self.scale_factor_frequencies[f_i+1],
                self.scale_factor_matrix[f_i][g_i],
                self.scale_factor_matrix[f_i+1][g_i]
            )
        else:
            scale_factor = self.interpolate_2d(
                f,
                g,
                self.scale_factor_frequencies[f_i],
                self.scale_factor_frequencies[f_i+1],
                self.scale_factor_gains[g_i],
                self.scale_factor_gains[g_i+1],
                self.scale_factor_matrix[f_i][g_i],
                self.scale_factor_matrix[f_i+1][g_i],
                self.scale_factor_matrix[f_i][g_i+1],
                self.scale_factor_matrix[f_i+1][g_i+1]
            )

        logger.debug("Using power scale factor: {}".format(scale_factor))
        return scale_factor

    # Get the linear scale factor for the current setup
    def get_scale_factor(self, lo_frequency, gain):
        # Ensure scale factors were loaded
        if not self.scale_factors_loaded:
            msg = "Defaulting scale factor to: {}"
            msg = msg.format(self.default_scale_factor)
            logger.debug(msg)
            return self.default_scale_factor

        # Get the power scaling factor and convert to linear
        psf = self.get_power_scale_factor(lo_frequency, gain)
        sf = (10**(psf/20.0))
        logger.debug("Using linear scale factor: {}".format(sf))
        return sf

    """
        These are functions which can be moved to a utils file
        since they will or could have more universal applications.
    """
    # Sort a matrix by the list defining its row indeces
    def sort_matrix_by_list(self, m, x):
        for i in range(1, len(x)):
            j = i-1
            m_key = m[i]
            x_key = x[i]
            while (x[j] > x_key) and (j >= 0):
                m[j+1] = m[j]
                x[j+1] = x[j]
                j = j - 1
            m[j+1] = m_key
            x[j+1] = x_key
        return m, x

    # Transpose a matrix
    def transpose_matrix(self, m):
        m_p = []
        for i in range(len(m[0])):
            m_p.append([])
            for j in range(len(m)):
                m_p[i].append(m[j][i])
        return m_p

    # Sort a matrix by two dependent lists defining the indices
    def sort_matrix_by_lists(self, m, x=None, y=None):
        if x is not None:
            m = self.transpose_matrix(m)
            m, x = self.sort_matrix_by_list(m, x)
            m = self.transpose_matrix(m)
        if y is not None:
            m, y = self.sort_matrix_by_list(m, y)
        if x is None and y is not None:
            return m, y
        if x is not None and y is None:
            return m, x
        if x is None and y is None:
            return m
        if x is not None and y is not None:
            return m, x, y

    # Interpolate between points in one dimension
    def interpolate_1d(self, x, x1, x2, y1, y2):
        return y1*(x2-x)/(x2-x1) + y2*(x-x1)/(x2-x1)

    # Interpolate between points in two dimensions
    def interpolate_2d(self, x, y, x1, x2, y1, y2, z11, z21, z12, z22):
        z_y1 = self.interpolate_1d(x, x1, x2, z11, z21)
        z_y2 = self.interpolate_1d(x, x1, x2, z12, z22)
        return self.interpolate_1d(y, y1, y2, z_y1, z_y2)
