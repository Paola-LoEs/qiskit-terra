# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""A module for visualizing device coupling maps"""

import math
import numpy as np
from qiskit.exceptions import QiskitError
from .matplotlib import HAS_MATPLOTLIB
from .exceptions import VisualizationError

if HAS_MATPLOTLIB:
    import matplotlib
    from matplotlib import get_backend
    import matplotlib.pyplot as plt  # pylint: disable=import-error
    import matplotlib.patches as mpatches
    import matplotlib.cm as cm
    import matplotlib.gridspec as gridspec
    from matplotlib import ticker


class _GraphDist():
    """Transform the circles properly for non-square axes.
    """

    def __init__(self, size, ax, x=True):
        self.size = size
        self.ax = ax  # pylint: disable=invalid-name
        self.x = x

    @property
    def dist_real(self):
        """Compute distance.
        """
        x0, y0 = self.ax.transAxes.transform(  # pylint: disable=invalid-name
            (0, 0))
        x1, y1 = self.ax.transAxes.transform(  # pylint: disable=invalid-name
            (1, 1))
        value = x1 - x0 if self.x else y1 - y0
        return value

    @property
    def dist_abs(self):
        """Distance abs
        """
        bounds = self.ax.get_xlim() if self.x else self.ax.get_ylim()
        return bounds[0] - bounds[1]

    @property
    def value(self):
        """Return value.
        """
        return (self.size / self.dist_real) * self.dist_abs

    def __mul__(self, obj):
        return self.value * obj


def plot_gate_map(backend, figsize=None,
                  plot_directed=False,
                  label_qubits=True,
                  qubit_size=24,
                  line_width=4,
                  font_size=12,
                  qubit_color=None,
                  qubit_labels=None,
                  line_color=None,
                  font_color='w',
                  ax=None):
    """Plots the gate map of a device.

    Args:
        backend (BaseBackend): A backend instance,
        figsize (tuple): Output figure size (wxh) in inches.
        plot_directed (bool): Plot directed coupling map.
        label_qubits (bool): Label the qubits.
        qubit_size (float): Size of qubit marker.
        line_width (float): Width of lines.
        font_size (int): Font size of qubit labels.
        qubit_color (list): A list of colors for the qubits
        qubit_labels (list): A list of qubit labels
        line_color (list): A list of colors for each line from coupling_map.
        font_color (str): The font color for the qubit labels.
        ax (Axes): A Matplotlib axes instance.

    Returns:
        Figure: A Matplotlib figure instance.

    Raises:
        QiskitError: if tried to pass a simulator.
        ImportError: if matplotlib not installed.
    """
    if not HAS_MATPLOTLIB:
        raise ImportError('Must have Matplotlib installed.')

    if backend.configuration().simulator:
        raise QiskitError('Requires a device backend, not simulator.')

    input_axes = False
    if ax:
        input_axes = True

    mpl_data = {}

    mpl_data[20] = [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4],
                    [1, 0], [1, 1], [1, 2], [1, 3], [1, 4],
                    [2, 0], [2, 1], [2, 2], [2, 3], [2, 4],
                    [3, 0], [3, 1], [3, 2], [3, 3], [3, 4]]

    mpl_data[14] = [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4],
                    [0, 5], [0, 6], [1, 7], [1, 6], [1, 5],
                    [1, 4], [1, 3], [1, 2], [1, 1]]

    mpl_data[16] = [[1, 0], [0, 0], [0, 1], [0, 2], [0, 3],
                    [0, 4], [0, 5], [0, 6], [0, 7], [1, 7],
                    [1, 6], [1, 5], [1, 4], [1, 3], [1, 2], [1, 1]]

    mpl_data[5] = [[1, 0], [0, 1], [1, 1], [1, 2], [2, 1]]

    mpl_data[53] = [[0, 2], [0, 3], [0, 4], [0, 5], [0, 6],
                    [1, 2], [1, 6],
                    [2, 0], [2, 1], [2, 2], [2, 3], [2, 4],
                    [2, 5], [2, 6], [2, 7], [2, 8],
                    [3, 0], [3, 4], [3, 8],
                    [4, 0], [4, 1], [4, 2], [4, 3], [4, 4],
                    [4, 5], [4, 6], [4, 7], [4, 8],
                    [5, 2], [5, 6],
                    [6, 0], [6, 1], [6, 2], [6, 3], [6, 4],
                    [6, 5], [6, 6], [6, 7], [6, 8],
                    [7, 0], [7, 4], [7, 8],
                    [8, 0], [8, 1], [8, 2], [8, 3], [8, 4],
                    [8, 5], [8, 6], [8, 7], [8, 8],
                    [9, 2], [9, 6]]

    config = backend.configuration()
    n_qubits = config.n_qubits
    cmap = config.coupling_map

    if qubit_labels is None:
        qubit_labels = list(range(n_qubits))
    else:
        if len(qubit_labels) != n_qubits:
            raise QiskitError('Length of qubit labels '
                              'does not equal number '
                              'of qubits.')

    if n_qubits in mpl_data.keys():
        grid_data = mpl_data[n_qubits]
    else:
        if not input_axes:
            fig, ax = plt.subplots(figsize=(5, 5))  # pylint: disable=invalid-name
            ax.axis('off')
            return fig

    x_max = max([d[1] for d in grid_data])
    y_max = max([d[0] for d in grid_data])
    max_dim = max(x_max, y_max)

    if figsize is None:
        if x_max / max_dim > 0.33 and y_max / max_dim > 0.33:
            figsize = (5, 5)
        else:
            figsize = (9, 3)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)  # pylint: disable=invalid-name
        ax.axis('off')

    # set coloring
    if qubit_color is None:
        qubit_color = ['#648fff'] * config.n_qubits
    if line_color is None:
        line_color = ['#648fff'] * len(cmap)

    # Add lines for couplings
    for ind, edge in enumerate(cmap):
        is_symmetric = False
        if edge[::-1] in cmap:
            is_symmetric = True
        y_start = grid_data[edge[0]][0]
        x_start = grid_data[edge[0]][1]
        y_end = grid_data[edge[1]][0]
        x_end = grid_data[edge[1]][1]

        if is_symmetric:
            if y_start == y_end:
                x_end = (x_end - x_start) / 2 + x_start

            elif x_start == x_end:
                y_end = (y_end - y_start) / 2 + y_start

            else:
                x_end = (x_end - x_start) / 2 + x_start
                y_end = (y_end - y_start) / 2 + y_start
        ax.add_artist(plt.Line2D([x_start, x_end], [-y_start, -y_end],
                                 color=line_color[ind], linewidth=line_width,
                                 zorder=0))
        if plot_directed:
            dx = x_end - x_start  # pylint: disable=invalid-name
            dy = y_end - y_start  # pylint: disable=invalid-name
            if is_symmetric:
                x_arrow = x_start + dx * 0.95
                y_arrow = -y_start - dy * 0.95
                dx_arrow = dx * 0.01
                dy_arrow = -dy * 0.01
                head_width = 0.15
            else:
                x_arrow = x_start + dx * 0.5
                y_arrow = -y_start - dy * 0.5
                dx_arrow = dx * 0.2
                dy_arrow = -dy * 0.2
                head_width = 0.2
            ax.add_patch(mpatches.FancyArrow(x_arrow,
                                             y_arrow,
                                             dx_arrow,
                                             dy_arrow,
                                             head_width=head_width,
                                             length_includes_head=True,
                                             edgecolor=None,
                                             linewidth=0,
                                             facecolor=line_color[ind],
                                             zorder=1))

    # Add circles for qubits
    for var, idx in enumerate(grid_data):
        _idx = [idx[1], -idx[0]]
        width = _GraphDist(qubit_size, ax, True)
        height = _GraphDist(qubit_size, ax, False)
        ax.add_artist(mpatches.Ellipse(
            _idx, width, height, color=qubit_color[var], zorder=1))
        if label_qubits:
            ax.text(*_idx, s=qubit_labels[var],
                    horizontalalignment='center',
                    verticalalignment='center',
                    color=font_color, size=font_size, weight='bold')
    ax.set_xlim([-1, x_max + 1])
    ax.set_ylim([-(y_max + 1), 1])
    if not input_axes:
        if get_backend() in ['module://ipykernel.pylab.backend_inline',
                             'nbAgg']:
            plt.close(fig)
        return fig
    return None


def plot_circuit_layout(circuit, backend, view='virtual'):
    """Plot the layout of a circuit transpiled for a given
    target backend.

    Args:
        circuit (QuantumCircuit): Input quantum circuit.
        backend (BaseBackend): Target backend.
        view (str): Layout view: either 'virtual' or 'physical'.

    Returns:
        Figure: A matplotlib figure showing layout.

    Raises:
        QiskitError: Invalid view type given.
        VisualizationError: Circuit has no layout attribute.
    """
    if circuit._layout is None:
        raise QiskitError('Circuit has no layout. '
                          'Perhaps it has not been transpiled.')

    n_qubits = backend.configuration().n_qubits

    qubits = []
    qubit_labels = [None] * n_qubits

    if view == 'virtual':
        idx = 0
        for key, val in circuit._layout.get_virtual_bits().items():
            if key.register.name != 'ancilla':
                qubits.append(val)
                qubit_labels[val] = idx
            idx += 1

    elif view == 'physical':
        for key, val in circuit._layout.get_physical_bits().items():
            if val.register.name != 'ancilla':
                qubits.append(key)
                qubit_labels[key] = key

    else:
        raise VisualizationError("Layout view must be 'virtual' or 'physical'.")

    qcolors = ['#648fff'] * n_qubits
    for k in qubits:
        qcolors[k] = 'k'

    cmap = backend.configuration().coupling_map

    lcolors = ['#648fff'] * len(cmap)

    for idx, edge in enumerate(cmap):
        if edge[0] in qubits and edge[1] in qubits:
            lcolors[idx] = 'k'

    fig = plot_gate_map(backend,
                        qubit_color=qcolors,
                        qubit_labels=qubit_labels,
                        line_color=lcolors)
    return fig


def plot_error_map(backend, figsize=(12, 9), show_title=True):
    """Plots the error map of a given backend.

    Args:
        backend (IBMQBackend): Given backend.
        figsize (tuple): Figure size in inches.
        show_title (bool): Show the title or not.

    Returns:
        Figure: A matplotlib figure showing error map.

    Raises:
        VisualizationError: Input is not IBMQ backend.
    """
    color_map = cm.viridis

    props = backend.properties().to_dict()
    config = backend.configuration().to_dict()

    n_qubits = config['n_qubits']

    # U2 error rates
    single_gate_errors = [q['parameters'][0]['value']
                          for q in props['gates'][1:3 * n_qubits:3]]

    # Convert to percent
    single_gate_errors = 100 * np.asarray(single_gate_errors)
    avg_1q_err = np.mean(single_gate_errors)

    single_norm = matplotlib.colors.Normalize(
        vmin=min(single_gate_errors), vmax=max(single_gate_errors))
    q_colors = [color_map(single_norm(err)) for err in single_gate_errors]

    cmap = config['coupling_map']

    directed = False
    if n_qubits < 20:
        for edge in cmap:
            if not [edge[1], edge[0]] in cmap:
                directed = True
                break

    cx_errors = []
    for line in cmap:
        for item in props['gates']:
            if item['qubits'] == line:
                cx_errors.append(item['parameters'][0]['value'])
                break
        else:
            continue

    # Convert to percent
    cx_errors = 100 * np.asarray(cx_errors)
    avg_cx_err = np.mean(cx_errors)

    cx_norm = matplotlib.colors.Normalize(
        vmin=min(cx_errors), vmax=max(cx_errors))
    line_colors = [color_map(cx_norm(err)) for err in cx_errors]

    # Measurement errors

    read_err = []

    for qubit in range(n_qubits):
        for item in props['qubits'][qubit]:
            if item['name'] == 'readout_error':
                read_err.append(item['value'])

    read_err = 100 * np.asarray(read_err)
    avg_read_err = np.mean(read_err)
    max_read_err = np.max(read_err)

    fig = plt.figure(figsize=figsize)
    gridspec.GridSpec(nrows=2, ncols=3)

    grid_spec = gridspec.GridSpec(12, 12, height_ratios=[1] * 11 + [0.5],
                                  width_ratios=[2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2])

    left_ax = plt.subplot(grid_spec[2:10, :1])
    main_ax = plt.subplot(grid_spec[:11, 1:11])
    right_ax = plt.subplot(grid_spec[2:10, 11:])
    bleft_ax = plt.subplot(grid_spec[-1, :5])
    bright_ax = plt.subplot(grid_spec[-1, 7:])

    plot_gate_map(backend, qubit_color=q_colors,
                  line_color=line_colors,
                  qubit_size=28,
                  line_width=5,
                  plot_directed=directed,
                  ax=main_ax)
    main_ax.axis('off')
    main_ax.set_aspect(1)

    single_cb = matplotlib.colorbar.ColorbarBase(bleft_ax, cmap=color_map,
                                                 norm=single_norm,
                                                 orientation='horizontal')
    tick_locator = ticker.MaxNLocator(nbins=5)
    single_cb.locator = tick_locator
    single_cb.update_ticks()
    single_cb.update_ticks()
    bleft_ax.set_title('H error rate (%) [Avg. = {}]'.format(round(avg_1q_err, 3)))

    cx_cb = matplotlib.colorbar.ColorbarBase(bright_ax, cmap=color_map,
                                             norm=cx_norm,
                                             orientation='horizontal')
    tick_locator = ticker.MaxNLocator(nbins=5)
    cx_cb.locator = tick_locator
    cx_cb.update_ticks()
    bright_ax.set_title('CNOT error rate (%) [Avg. = {}]'.format(round(avg_cx_err, 3)))

    if n_qubits < 10:
        num_left = n_qubits
        num_right = 0
    else:
        num_left = math.ceil(n_qubits / 2)
        num_right = n_qubits - num_left

    left_ax.barh(range(num_left), read_err[:num_left], align='center', color='#007d79')
    left_ax.axvline(avg_read_err, linestyle='--', color='#212121')
    left_ax.set_yticks(range(num_left))
    left_ax.set_xticks([0, round(avg_read_err, 2), round(max_read_err, 2)])
    left_ax.set_yticklabels([str(kk) for kk in range(num_left)], fontsize=12)
    left_ax.invert_yaxis()
    left_ax.set_title('Readout Error (%)', fontsize=12)

    for spine in left_ax.spines.values():
        spine.set_visible(False)

    if num_right:
        right_ax.barh(range(num_left, n_qubits), read_err[num_left:],
                      align='center', color='#007d79')
        right_ax.axvline(avg_read_err, linestyle='--', color='#212121')
        right_ax.set_yticks(range(num_left, n_qubits))
        right_ax.set_xticks([0, round(avg_read_err, 2), round(max_read_err, 2)])
        right_ax.set_yticklabels([str(kk) for kk in range(num_left, n_qubits)],
                                 fontsize=12)
        right_ax.invert_yaxis()
        right_ax.invert_xaxis()
        right_ax.yaxis.set_label_position("right")
        right_ax.yaxis.tick_right()
        right_ax.set_title('Readout Error (%)', fontsize=12)
    else:
        right_ax.axis('off')

    for spine in right_ax.spines.values():
        spine.set_visible(False)

    if show_title:
        fig.suptitle('{name} Error Map'.format(name=backend.name()),
                     fontsize=24, y=0.9)
    if get_backend() in ['module://ipykernel.pylab.backend_inline',
                         'nbAgg']:
        plt.close(fig)
    return fig
