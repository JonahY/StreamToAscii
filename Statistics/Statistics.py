"""
@version: 1.0
@author: Jonah
@file: Statistics.py
@Created time: 2022/05/23 21:19
@Last Modified: 2022/05/23 22:30
"""
import sys
from os import makedirs
from os.path import join, dirname, exists
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from math import floor, ceil
from matplotlib.pylab import mpl
from json import load
from time import sleep
from warnings import filterwarnings
from os import system
import colorama


def app_path():
    """Returns the base application path."""
    if hasattr(sys, 'frozen'):
        # Handles PyInstaller
        return dirname(sys.executable)  # 打包后的exe目录
    return dirname(__file__)  # 没打包前的py目录


PROJECT_PATH = app_path()
system("")
colorama.init(autoreset=True)
mpl.rcParams['axes.unicode_minus'] = False  # 显示负号
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
filterwarnings("ignore")


def plot_norm(ax, xlabel=None, ylabel=None, zlabel=None, title=None, x_lim=[], y_lim=[], z_lim=[], legend=True,
              grid=False, frameon=True, legend_loc='upper left', font_color='black', legendsize=11, labelsize=14,
              titlesize=15, ticksize=13, linewidth=2, fontname='Arial'):
    ax.spines['bottom'].set_linewidth(linewidth)
    ax.spines['left'].set_linewidth(linewidth)
    ax.spines['right'].set_linewidth(linewidth)
    ax.spines['top'].set_linewidth(linewidth)

    # 设置坐标刻度值的大小以及刻度值的字体 Arial, Times New Roman
    ax.tick_params(which='both', width=linewidth, labelsize=ticksize, colors=font_color)
    labels = ax.get_xticklabels() + ax.get_yticklabels()
    [label.set_fontname(fontname) for label in labels]

    font_legend = {'family': fontname, 'weight': 'normal', 'size': legendsize}
    font_label = {'family': fontname, 'weight': 'bold', 'size': labelsize, 'color': font_color}
    font_title = {'family': fontname, 'weight': 'bold', 'size': titlesize, 'color': font_color}

    if x_lim:
        ax.set_xlim(x_lim[0], x_lim[1])
    if y_lim:
        ax.set_ylim(y_lim[0], y_lim[1])
    if z_lim:
        ax.set_zlim(z_lim[0], z_lim[1])
    if legend:
        ax.legend(loc=legend_loc, prop=font_legend, frameon=frameon)
        # plt.legend(loc=legend_loc, prop=font_legend)
    if grid:
        ax.grid(ls='-.')
    if xlabel:
        ax.set_xlabel(xlabel, font_label)
    if ylabel:
        ax.set_ylabel(ylabel, font_label)
    if zlabel:
        ax.set_zlabel(zlabel, font_label)
    if title:
        ax.set_title(title, font_title)
    plt.tight_layout()


class Features:
    def __init__(self):
        if not exists(join(PROJECT_PATH, 'Statistics.json')):
            print('\033[1;34mConfig File Not Found!\nPlease Add Configuration File [Statistics.json] In This Directory.'
                  '\nThis terminal will closed in 5s...\033[0m')
            sleep(5)
            sys.exit(0)

        with open(join(PROJECT_PATH, 'Statistics.json'), 'r', encoding='utf-8') as f:
            js = load(f)
        try:
            self.mode = js['features']
            if self.mode not in ['Energy', 'Amplitude', 'Duration']:
                print(f"\033[1;34mError: 'features'\nPlease check the parameters in the configuration file!\n"
                      f"This terminal will closed in 5s...\033[0m")
                sleep(5)
                sys.exit(0)
            self.file = js['absolute of file']
            if not exists(join(PROJECT_PATH, self.file)):
                print("\033[1;34mError: 'absolute of file'\nTarget File Not Found! "
                      "Please Check Absolute Path In [Statistics.json].\nThis terminal will closed in 5s...\033[0m")
                sleep(5)
                sys.exit(0)
            self.save_path = js['save path']
            if not exists(join(PROJECT_PATH, self.save_path)):
                makedirs(self.save_path)
            self.INTERVAL_NUM = int(js['interval number'])
        except (KeyError, Exception, BaseException) as e:
            print(f"\033[1;34mError: {e}\nPlease check the parameters in the configuration file!\n"
                  f"This terminal will closed in 5s...\033[0m")
            sleep(5)
            sys.exit(0)

        for idx, f in enumerate(['Energy', 'Amplitude', 'Duration']):
            if self.mode == f:
                self.xlabel = ['Energy (aJ)', 'Amplitude (μV)', 'Duration (μs)'][idx]

        with open(self.file, 'r') as f:
            self.tmp = sorted(np.array([float(i.strip()) for i in f.readlines()]))

    def __cal_log_interval(self, tmp):
        """
        Take the logarithmic interval to get the first number in each order
        :param tmp: Energy/Amplitude/Duration in order of magnitude
        :return:
        """
        tmp_min = floor(np.log10(min(tmp)))
        tmp_max = ceil(np.log10(max(tmp)))
        inter = [i for i in range(tmp_min, tmp_max + 1)]
        return inter

    def __cal_log(self, tmp, inter, interval_num, idx=0):
        """
        Calculate the probability density value at logarithmic interval
        :param tmp: Energy/Amplitude/Duration in order of magnitude
        :param inter: The first number of each order of magnitude
        :param interval_num: Number of bins divided in each order of magnitude
        :param idx:
        :return:
        """
        x, xx, interval = np.array([]), np.array([]), np.array([])
        for i in inter:
            logspace = np.logspace(i, i + 1, interval_num, endpoint=False)
            tmp_inter = [logspace[i + 1] - logspace[i] for i in range(len(logspace) - 1)]
            tmp_xx = [(logspace[i + 1] + logspace[i]) / 2 for i in range(len(logspace) - 1)]
            tmp_inter.append(10 * logspace[0] - logspace[-1])
            tmp_xx.append((10 * logspace[0] + logspace[-1]) / 2)
            x = np.append(x, logspace)
            interval = np.append(interval, np.array(tmp_inter))
            xx = np.append(xx, np.array(tmp_xx))

        y = np.zeros(x.shape[0])
        for i, n in Counter(tmp).items():
            while True:
                try:
                    if x[idx] <= i < x[idx + 1]:
                        y[idx] += n
                        break
                except IndexError:
                    if x[idx] <= i:
                        y[idx] += n
                        break
                idx += 1

        xx, y, interval = xx[y != 0], y[y != 0], interval[y != 0]
        yy = y / (sum(y) * interval)
        return xx, yy

    def cal_PDF(self):
        """
        Calculate Probability Density Distribution Function
        :return:
        """
        fig = plt.figure(figsize=[6, 3.9])
        ax = plt.subplot()
        inter = self.__cal_log_interval(self.tmp)
        xx, yy = self.__cal_log(self.tmp, inter, self.INTERVAL_NUM)
        ax.loglog(xx, yy, '.', marker='.', markersize=8, color='black')
        with open(join(self.save_path, f'PDF({self.xlabel[0].upper()}).txt'), 'w') as f:
            f.write(f'{self.xlabel}, PDF({self.xlabel[0].upper()})\n')
            for j in range(len(xx)):
                f.write(f'{xx[j]}, {yy[j]}\n')
        plot_norm(ax, self.xlabel, f'PDF({self.xlabel[0].upper()})', legend=False)
        plt.show()

    def cal_CCDF(self):
        """
        Calculate Complementary Cumulative Distribution Function
        :return:
        """
        fig = plt.figure(figsize=[6, 3.9])
        ax = plt.subplot()
        N = len(self.tmp)
        xx, yy = [], []
        for i in range(N - 1):
            xx.append(np.mean([self.tmp[i], self.tmp[i + 1]]))
            yy.append((N - i + 1) / N)
        ax.loglog(xx, yy, color='black')
        with open(join(self.save_path, f'CCDF({self.xlabel[0].upper()}).txt'), 'w') as f:
            f.write(f'{self.xlabel}, CCDF({self.xlabel[0].upper()})\n')
            for j in range(len(xx)):
                f.write(f'{xx[j]}, {yy[j]}\n')
        plot_norm(ax, self.xlabel, f'CCDF({self.xlabel[0].upper()})', legend=False)
        plt.show()

    def cal_ML(self):
        """
        Calculate the maximum likelihood function distribution
        :return:
        """
        fig = plt.figure(figsize=[6, 3.9])
        ax = plt.subplot()
        N = len(self.tmp)
        ax.set_xscale("log", nonposx='clip')
        ML_y, Error_bar = [], []
        for j in range(N):
            valid_x = self.tmp[j:]
            E0 = valid_x[0]
            Sum = np.sum(np.log(valid_x / E0)) + 1e-5
            N_prime = N - j
            alpha = 1 + N_prime / Sum
            error_bar = (alpha - 1) / pow(N_prime, 0.5)
            ML_y.append(alpha)
            Error_bar.append(error_bar)
        ax.errorbar(self.tmp, ML_y, yerr=Error_bar, fmt='o', ecolor='black', color='black', elinewidth=1, capsize=2, ms=3)
        with open(join(self.save_path, f'ML({self.xlabel[0].upper()}).txt'), 'w') as f:
            f.write(f'{self.xlabel}, ML({self.xlabel[0].upper()}), Error bar\n')
            for j in range(len(ML_y)):
                f.write(f'{self.tmp[j]}, {ML_y[j]}, {Error_bar[j]}\n')
        plot_norm(ax, self.xlabel, f'ML({self.xlabel[0].upper()})', y_lim=[1.3, 3.0], legend=False)
        plt.show()


if __name__ == '__main__':
    while True:
        ans = input("Please select an calculation mode, enter \033[1;31;40m[PDF]\033[0m to Calculate PDF, "
                    "enter \033[1;31;40m[CCDF]\033[0m to Calculate CCDF, "
                    "enter \033[1;31;40m[ML]\033[0m to Calculate ML, "
                    "enter \033[1;31;40m[quit]\033[0m to close: ")
        if ans.strip().upper() == 'PDF':
            Features().cal_PDF()
        elif ans.strip().upper() == 'CCDF':
            Features().cal_CCDF()
        elif ans.strip().upper() == 'ML':
            Features().cal_ML()
        elif ans.strip().lower() == 'quit':
            sys.exit(0)
