import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

# plt.style.use('seaborn-bright')

import random

import logging


logger = logging.getLogger(__name__)


def get_random_color():
    return '#' + ''.join(random.choices('123456789abcdef', k=6))


class ProfilePlot4:

    qf_colors = {'B': 'red',
                 'S': 'orange',
                 'E': 'green'}

    def __init__(self, pack, **kwargs):

        self._pack = pack
        self._df = pack.get_data(suffix='.txt')
        self._depth_data = None

        self._top_adjust = 0.8
        self._ax2_pos = 1.08
        self._ax3_pos = 1.16

        self._ax = {}  # To save axis
        self._colors = {}

        kw = dict(
            figsize=(8.27, 11.69),
            dpi=100
        )
        kw.update(kwargs)

        self._fig = plt.figure(**kw)

        plt.gcf().text(0.5, 0.98,
                       f'{pack("station", pref_suffix=".hdr")}: {pack.key}',
                       fontsize=14,
                       horizontalalignment='center')

        self._add_ax_func_mapping = dict()
        self._add_ax_func_mapping[0] = self._add_ax0
        self._add_ax_func_mapping[1] = self._add_ax1
        self._add_ax_func_mapping[2] = self._add_ax2
        self._add_ax_func_mapping[3] = self._add_ax3

    def _set_depth_par(self, par):
        self._depth_data = np.array([-d for d in self._df[par]])

    def plot_from_config(self, config):
        self._set_depth_par(config['depth_par']['data_par'])
        for nr, c in enumerate(config['pars']):
            try:
                self._plot_par_from_config(nr, c)
                self._plot_vertikal_lines_from_config(nr, c)
                self._plot_qf_from_config(nr, c)
            except KeyError as e:
                logger.warning(f'Parameter {e} not found in file: {self._pack.key}')

    def _plot_vertikal_lines_from_config(self, nr, config):
        data = dict(
            color=config['color'],
            xmin=config['xmin'],
            xmax=config['xmax'],
            default_xmin=config.get('default_xmin'),
            default_xmax=config.get('default_xmax')
        )
        self._plot_vertikal_lines(nr, **data)

    def _plot_par_from_config(self, nr, config):
        data = dict(
            xdata=self._get_xdata(config),
            ydata=list(self._depth_data),
            label=config['title'],
            color=config['color'],
            xmin=config['xmin'],
            xmax=config['xmax']
        )
        self._plot_par(nr, **data)
        plt.close()
        # plt.show()

    def _plot_qf_from_config(self, nr, config):

        for qf, info in self._get_qf_data(config).items():
            data = dict(
                xdata=info['xdata'],
                ydata=info['ydata'],
                color=self.qf_colors.get(qf)
            )
            self._plot_qf(nr, **data)

    def _get_xdata(self, config):
        par = config['data_par']
        if '--' in par:
            par1, par2 = par.split('--')
            data1 = self._df[par1]
            data2 = self._df[par2]
            data = data1-data2
        else:
            data = self._df[par]
        return data

    def _get_qf_data(self, config):
        par = config['data_par']
        qf_par = config['qf_par']
        if '--' in par:
            qf_par1, qf_par2 = qf_par.split('--')
            unique_qf = list(set([x for x in list(self._df[qf_par1])+list(self._df[qf_par2]) if not str(x) == 'nan']))
        else:
            unique_qf = list(set([x for x in self._df[qf_par] if not str(x) == 'nan']))

        all_index = []
        qf_data = {}
        for qf in self.qf_colors:
            if qf not in unique_qf:
                continue
            qf_data[qf] = dict(index=[])
            if '--' in par:
                match1 = self._df[qf_par1] == qf
                match2 = self._df[qf_par2] == qf
                index = list(set(list(np.where(match1)[0]) + list(np.where(match2)[0])))

            else:
                match = self._df[qf_par] == qf
                index = list(np.where(match)[0])
            for i in index:
                if i not in all_index:
                    all_index.append(i)
                    qf_data[qf]['index'].append(i)
            qf_data[qf]['xdata'] = np.array(self._get_xdata(config))[index]
            qf_data[qf]['ydata'] = self._depth_data[index]
        return qf_data

    def _add_ax0(self, **kwargs):
        self._ax[0] = self._fig.add_subplot(111)
        self._fig.subplots_adjust(top=self._top_adjust)
        self._colors[0] = kwargs.get('color', get_random_color())
        self._ax[0].spines.bottom.set_color(self._colors[0])
        self._ax[0].grid(True)
        return self._ax[0]

    def _add_ax1(self, **kwargs):
        self._ax[1] = self._ax[0].twiny()
        self._colors[1] = kwargs.get('color', get_random_color())
        self._ax[1].spines.top.set_color(self._colors[1])
        self._ax[1].spines.bottom.set_visible(False)
        return self._ax[1]

    def _add_ax2(self, **kwargs):
        self._ax[2] = self._ax[0].twiny()
        self._ax[2].spines["top"].set_position(("axes", self._ax2_pos))
        self._colors[2] = kwargs.get('color', get_random_color())
        self._ax[2].spines.top.set_color(self._colors[2])
        return self._ax[2]

    def _add_ax3(self, **kwargs):
        self._ax[3] = self._ax[0].twiny()
        self._ax[3].spines["top"].set_position(("axes", self._ax3_pos))
        self._colors[3] = kwargs.get('color', get_random_color())
        self._ax[3].spines.top.set_color(self._colors[3])
        return self._ax[3]

    def _set_color(self, nr, **kwargs):
        color = kwargs.get('color', get_random_color())
        self._colors[nr] = color
        ax = self._ax[nr]
        ax.xaxis.label.set_color(color)
        ax.tick_params(axis='x', labelcolor=color)

    def _set_x_label(self, nr, **kwargs):
        ax = self._ax[nr]
        ax.set_xlabel(kwargs.get('label', str(nr)), color=self._colors[nr])
        ax.set_xlabel(kwargs.get('label', str(nr)))

    def _set_limit(self, nr, **kwargs):
        ax = self._ax[nr]
        limits = self._get_axes_limit(nr)
        ax.set_xlim(kwargs.get('xmin', limits[0]), kwargs.get('xmax', limits[1]))

    def _get_axes_limit(self, nr):
        data = self._ax[nr].lines[0].get_xdata()
        return [min(data), max(data)]

    def _set_xticks(self, nr):
        xmin, xmax = self._ax[nr].get_xlim()
        ticks = np.linspace(xmin, xmax, 11)
        self._ax[nr].set_xticks(ticks)

    def _set_yticks(self, nr):
        self._fig.canvas.draw()
        labels = [item.get_text() for item in self._ax[nr].get_yticklabels()]
        if not labels[0]:
            return
        new_labels = [c[1:] if ord(c[0]) in [45, 8722] else c for c in labels]
        self._ax[nr].set_yticklabels(new_labels)

    def _plot_par(self, nr, xdata, ydata, **kwargs):
        self._add_ax_func_mapping[nr](**kwargs)
        self._ax[nr].set_ylim(self._get_y_min_from_data(ydata), 0)
        self._ax[nr].plot(xdata, ydata, color=self._colors[nr], label=kwargs.get('label', str(nr)))
        self._set_x_label(nr, **kwargs)
        self._set_color(nr, **kwargs)
        self._set_limit(nr, **kwargs)
        self._set_xticks(nr)
        self._set_yticks(nr)

    def _plot_vertikal_lines(self, nr, **kwargs):
        xmin = kwargs.get('xmin')
        xmax = kwargs.get('xmax')
        default_xmin = kwargs.get('default_xmin')
        default_xmax = kwargs.get('default_xmax')
        logger.debug(f'{xmin=}')
        logger.debug(f'{xmax=}')
        logger.debug(f'{default_xmin=}')
        logger.debug(f'{default_xmax=}')
        # if default_xmin is not None and default_xmax is not None and xmin < default_xmin and xmax > default_xmax:
        #     print('a')
        #     self._ax[nr].axvspan(default_xmin, default_xmax, edgecolor=kwargs.get('color'), linestyle='--', alpha=1.0)
        if default_xmin is not None and xmin < default_xmin:
            print('b')
            self._ax[nr].axvline(x=default_xmin, color=kwargs.get('color'), linestyle='--', label='default_xmin')
        if default_xmax is not None and xmax > default_xmax:
            print('c')
            self._ax[nr].axvline(x=default_xmax, color=kwargs.get('color'), linestyle='--', label='default_xmin')

    def _plot_qf(self, nr, xdata, ydata, **kwargs):
        self._ax[nr].plot(xdata, ydata, 'o', color=kwargs.get('color'))

    @staticmethod
    def _get_y_min_from_data(ydata):
        value = min(ydata)
        if value > 50:
            ymin = int(np.round(value/10))*10 - 10
        else:
            ymin = int(np.round(value/5))*5 - 5
        return ymin

    def save_pdf(self, file_path, **kwargs):
        pdf_pages = PdfPages(file_path)
        pdf_pages.savefig(self._fig, **kwargs)
        pdf_pages.close()

    def save(self, file_path, **kwargs):
        kw = dict(
            bbox_inches='tight'
        )
        kw.update(kwargs)
        self._fig.savefig(file_path, **kw)
        return file_path
