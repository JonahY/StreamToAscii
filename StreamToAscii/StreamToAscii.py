"""
@version: 1.0
@author: Jonah
@file: StreamToAscii.py
@Created time: 2022/05/14 20:00
@Last Modified: 2022/05/25 10:30
"""
import sys
from pyautogui import doubleClick, click, screenshot, typewrite, press, position
from time import sleep, asctime, localtime, time
from os.path import join, exists, dirname
from os import makedirs, listdir
from pytesseract import image_to_string
from PIL import Image
from tqdm import tqdm
from json import load
from scipy.io import savemat, loadmat
from traceback import format_exc
import numpy as np
from multiprocessing import Pool, freeze_support
from math import ceil
from os import system
import colorama

system("")
colorama.init(autoreset=True)


def app_path():
    """Returns the base application path."""
    if hasattr(sys, 'frozen'):
        # Handles PyInstaller
        return dirname(sys.executable)  # 打包后的exe目录
    return dirname(__file__)  # 没打包前的py目录


PROJECT_PATH = app_path()


def convert_ascii2mat(files, asciiFold, matFold, magnification_dB):
    try:
        pbar = tqdm(files, ncols=100)

        for file in pbar:
            pbar.set_description(f'\033[1;34mFile name: {file[43:-4]}\033[0m')

            if not exists(join(matFold, f'{file[:-4]}.mat')):
                with open(join(asciiFold, file), 'r') as f:
                    for _ in range(4):
                        f.readline()
                    fs = int(f.readline().strip().split()[-1]) * 1e-3
                    for _ in range(2):
                        f.readline()
                    trigger_time = float(f.readline().strip()[15:])
                    sig = np.array(list(map(lambda x: float(x.strip()) * 1e6 / pow(10, magnification_dB / 20),
                                            f.readlines()[1:-1])))

                savemat(join(matFold, f'{file[:-4]}.mat'), {'Sampling rate': fs, 'Trigger time': trigger_time,
                                                            'Voltage': sig})

            with open(join(matFold, 'log'), 'a') as f:
                f.write(f'{file}\n')

    except Exception as e:
        print(f'\033[1;34mError: {e}\033[0m')
        print(format_exc())


def shortTermEny_zerosCrossingRate(signal, framelen, stride, fs, window='hamming'):
    """
    :param signal: raw signal of waveform, unit: μV
    :param framelen: length of per frame, type: int
    :param stride: length of translation per frame
    :param fs: sampling rate per microsecond
    :param window: window's function
    :return: time_zcR, zcR
    """
    if signal.shape[0] <= framelen:
        nf = 1
    else:
        nf = int(np.ceil((1.0 * signal.shape[0] - framelen + stride) / stride))
    pad_length = int((nf - 1) * stride + framelen)
    zeros = np.zeros((pad_length - signal.shape[0],))
    pad_signal = np.concatenate((signal, zeros))
    indices = np.tile(np.arange(0, framelen), (nf, 1)) + np.tile(np.arange(0, nf * stride, stride),
                                                                 (framelen, 1)).T.astype(np.int32)
    frames = pad_signal[indices]
    allWindows = {'hamming': np.hamming(framelen), 'hanning': np.hanning(framelen), 'blackman': np.blackman(framelen),
                  'bartlett': np.bartlett(framelen)}
    t = np.arange(0, nf) * (stride * 1.0 / fs)
    eny, res = np.zeros(nf), np.zeros(nf)

    try:
        windows = allWindows[window]
    except:
        print("\033[1;34mPlease select window's function from: hamming, hanning, blackman and bartlett.\033[0m")
        return t, eny, res

    for i in range(nf):
        frame = frames[i:i + 1][0]
        # calculate zeros crossing rate
        tmp = windows * frame
        for j in range(framelen - 1):
            if tmp[j] * tmp[j + 1] <= 0:
                res[i] += 1

        # calculate short term energy
        b = np.square(frame) * windows / fs
        eny[i] = np.sum(b)

    return t, eny, res / framelen


def cal_deriv(x, y):
    diff_x = []
    for i, j in zip(x[0::], x[1::]):
        diff_x.append(j - i)

    diff_y = []
    for i, j in zip(y[0::], y[1::]):
        diff_y.append(j - i)

    slopes = []
    for i in range(len(diff_y)):
        slopes.append(diff_y[i] / diff_x[i])

    deriv = []
    for i, j in zip(slopes[0::], slopes[1::]):
        deriv.append((0.5 * (i + j)))
    deriv.insert(0, slopes[0])
    deriv.append(slopes[-1])

    return deriv


def find_wave(stE, stE_dev, zcR, t_stE, IZCRT=0.3, ITU=75, alpha=0.5, t_backNoise=0):
    start, end = [], []
    last_end = 0

    # Background noise level
    end_backNoise = np.where(t_stE <= t_backNoise)[0][-1]
    ITU_tmp = ITU + np.mean(stE[last_end:end_backNoise]) + alpha * np.std(stE[last_end:end_backNoise]) \
        if last_end != end_backNoise else ITU
    IZCRT_tmp = np.mean(zcR[last_end:end_backNoise]) + alpha * np.std(zcR[last_end:end_backNoise]) \
        if last_end != end_backNoise else IZCRT
    last_end = end_backNoise

    while last_end < stE.shape[0] - 2:
        try:
            start_temp = last_end + np.where(stE[last_end + 1:] >= ITU_tmp)[0][0]
        except IndexError:
            return start, end
        start_true = last_end + np.where(np.array(stE_dev[last_end:start_temp + 1]) <= 0)[0][-1] \
            if np.where(np.array(stE_dev[last_end:start_temp]) <= 0)[0].shape[0] else last_end

        # Auto-adjust threshold
        ITU_tmp = ITU + np.mean(stE[last_end:start_true]) + alpha * np.std(stE[last_end:start_true]) \
            if start_true - last_end > 10 else ITU_tmp
        IZCRT_tmp = np.mean(zcR[last_end:start_true]) + alpha * np.std(zcR[last_end:start_true]) \
            if start_true - last_end > 10 else IZCRT_tmp

        for j in range(start_temp + 1, stE.shape[0]):
            if stE[j] < ITU_tmp:
                end_temp = j
                break
        ITL = 0.368 * max(stE[start_true:end_temp + 1]) if ITU_tmp > 0.368 * max(
            stE[start_true:end_temp + 1]) else ITU_tmp

        for k in range(end_temp, stE.shape[0]):
            if ((stE[k] < ITL) & (zcR[k] > IZCRT_tmp)) | (k == stE.shape[0] - 1):
                end_true = k
                break

        if start_true >= end_true:
            return start, end

        last_end = end_true
        start.append(start_true)
        end.append(end_true)

    return start, end


def cut_stream(files, matFold, eventFold, featuresMatFold, staWin, staLen, overlap, IZCRT, ITU, alpha, t_backNoise):
    try:
        pbar = tqdm(files, ncols=100)
        for file in pbar:
            pbar.set_description(f'\033[1;34mFile name: {file[43:-4]}\033[0m')

            dataMat = loadmat(join(matFold, file))
            fs = dataMat['Sampling rate'][0][0]
            trigger_time = dataMat['Trigger time'][0][0]

            if file not in listdir(featuresMatFold):
                width = int(fs * staLen)
                stride = int(width) - overlap
                t_stE, stE, zcR = shortTermEny_zerosCrossingRate(dataMat['Voltage'][0], width, stride, fs, staWin)
                stE_dev = cal_deriv(t_stE, stE)

                # save calculated values
                savemat(join(featuresMatFold, file), {'Trigger time': trigger_time, 'StaWin': staWin,
                                                      'StaLen': staLen, 'Overlap': overlap, 'Width': width,
                                                      'Stride': stride, 't_stE': t_stE, 'stE': stE,
                                                      'stE_dev': stE_dev, 'zcR': zcR})

            else:
                featuresMat = loadmat(join(featuresMatFold, file))
                t_stE, stE, stE_dev, zcR = featuresMat['t_stE'][0], featuresMat['stE'][0], featuresMat['stE_dev'][0], \
                                           featuresMat['zcR'][0]

            start, end = find_wave(stE, stE_dev, zcR, t_stE, IZCRT=IZCRT, ITU=ITU, alpha=alpha, t_backNoise=t_backNoise)

            for out, [s, e] in enumerate(zip(start, end), 1):
                with open(join(eventFold, '{}-{}.txt'.format(file[:-4], out)), 'w') as f:
                    f.write(f'Trigger time of stream file (s)\n{trigger_time:.8f}\n')
                    f.write(f'Trigger time of AE event (μs)\n{(int(t_stE[s] // (1 / fs)) + 1) / fs:.1f}\n\n')
                    f.write('Amplitude (μV)\n')
                    for i in range(int(t_stE[s] // (1 / fs)) + 1, int(t_stE[e] // (1 / fs)) + 2):
                        f.write(f"{dataMat['Voltage'][0][i]}\n")

            with open(join(eventFold, 'log'), 'a') as f:
                f.write('%s\n' % file)

    except Exception as e:
        print(f'\033[1;34mError: {e}\033[0m')
        print(format_exc())


def stream2ascii():
    if not exists(join(PROJECT_PATH, 'position.json')):
        print('\033[1;34mConfig File Not Found!\nPlease Add Configuration File [position.json] In This Directory.\n'
              'This terminal will closed in 5s...\033[0m')
        sleep(5)
        sys.exit(0)

    with open(join(PROJECT_PATH, 'position.json'), 'r', encoding='utf-8') as f:
        js = load(f)

    INPUT = js['INPUT']
    OUTPUT = js['OUTPUT']

    if not exists(INPUT):
        print('\033[1;34mPlease Enter Correct Input Path!\nThis terminal will closed in 5s...\033[0m')
        sleep(5)
        sys.exit(0)

    while True:
        ans = input("\033[1;34mPlease move this terminal to a suitable location, enter [yes] to continue, "
                    "enter [quit] to close: \033[0m")
        if ans.strip() == 'yes':
            break
        elif ans.strip() == 'quit':
            sys.exit(0)

    screenshotsPath_InputFileName = join(OUTPUT, 'screenshots_InputFileName')
    screenshotsPath_InputLocation = join(OUTPUT, 'screenshots_InputLocation')
    screenshotsPath_Search = join(OUTPUT, 'screenshots_Search')
    screenshotsPath_OutputFileName = join(OUTPUT, 'screenshots_OutputFileName')
    screenshotsPath_OutputLocation = join(OUTPUT, 'screenshots_OutputLocation')
    screenshotsPath_Convert = join(OUTPUT, 'screenshots_Convert')
    OutputDir = join(OUTPUT, 'ascii')

    try:
        locations_fixed = js['locations_dialog']
        LOCATIONS = []
        for k in js['locations_software'].keys():
            LOCATIONS.append(js['locations_software'][k])

        for Path in [screenshotsPath_InputFileName, screenshotsPath_InputLocation, screenshotsPath_Search,
                     screenshotsPath_OutputFileName, screenshotsPath_OutputLocation, screenshotsPath_Convert,
                     OutputDir]:
            if not exists(Path):
                makedirs(Path)

        files = listdir(INPUT)

        first = True
        pbar = tqdm(range(0, len(files), len(LOCATIONS)))
        for i in pbar:
            try:
                F = [files[i + j] for j in range(len(LOCATIONS))]
            except IndexError:
                F = [files[i + j] for j in range(len(files) % len(LOCATIONS))]
            pbar.set_description(f'\033[1;34mProcessing [{F}]\033[0m')

            if first:
                for locations in LOCATIONS:
                    click(x=locations['Produce ASCII Output File'][0], y=locations['Produce ASCII Output File'][1],
                          duration=0)
                    click(x=locations['Show Message Precessing Window'][0],
                          y=locations['Show Message Precessing Window'][1],
                          duration=0)
                first = False

            for locations, f in zip(LOCATIONS[:len(F)], F):
                if f'{f[:-4]}.txt' in listdir(OutputDir):
                    continue

                click(x=locations['Input Browse'][0], y=locations['Input Browse'][1], duration=0)
                screenshotTmp_InputFileName = join(screenshotsPath_InputFileName, f'{f[:-4]}.png')
                while True:
                    screenshot(screenshotTmp_InputFileName, region=(locations_fixed['Screenshot Input File Name'][0],
                                                                    locations_fixed['Screenshot Input File Name'][1],
                                                                    232,
                                                                    14))
                    if 'Please Select Waveform File to Convert' in image_to_string(
                            Image.open(screenshotTmp_InputFileName), lang='eng'):
                        break
                    else:
                        sleep(0.1)

                click(x=locations_fixed['Dir'][0], y=locations_fixed['Dir'][1], duration=0)
                typewrite(message=INPUT, interval=0)
                press('enter')
                screenshotTmp_InputLocation = join(screenshotsPath_InputLocation, f'{f[:-4]}.png')
                while True:
                    screenshot(screenshotTmp_InputLocation, region=(locations_fixed['Screenshot Input Location'][0],
                                                                    locations_fixed['Screenshot Input Location'][1],
                                                                    134,
                                                                    9))
                    if INPUT.split('\\')[-1][:20] in image_to_string(Image.open(screenshotTmp_InputLocation),
                                                                     lang='eng'):
                        break
                    else:
                        sleep(0.1)

                click(x=locations_fixed['Search'][0], y=locations_fixed['Search'][1], duration=0)
                sleep(1)
                typewrite(message=f[:-4] if js['Data Location'] == 'PC' else f, interval=0)
                sleep(0.5)
                click(x=locations_fixed['Search Enter'][0], y=locations_fixed['Search Enter'][1], duration=0)
                screenshotTmp_Search = join(screenshotsPath_Search, f'{f[:-4]}.png')
                while True:
                    screenshot(screenshotTmp_Search, region=(locations_fixed['Screenshot Search'][0],
                                                             locations_fixed['Screenshot Search'][1], 431, 23))
                    if f.split('-')[5] in image_to_string(Image.open(screenshotTmp_Search), lang='eng'):
                        break
                    else:
                        sleep(0.1)

                doubleClick(x=locations_fixed['Search Result'][0], y=locations_fixed['Search Result'][1], duration=0)
                sleep(0.75)

                # Output File Name Prefix
                click(x=locations['Output Browse'][0], y=locations['Output Browse'][1], duration=0)
                screenshotTmp_OutputFileName = join(screenshotsPath_OutputFileName, f'{f[:-4]}.png')
                while True:
                    screenshot(screenshotTmp_OutputFileName, region=(locations_fixed['Screenshot Output File Name'][0],
                                                                     locations_fixed['Screenshot Output File Name'][1],
                                                                     181,
                                                                     12))
                    if 'Please Select Output ASCII' in image_to_string(Image.open(screenshotTmp_OutputFileName),
                                                                       lang='eng'):
                        break
                    else:
                        sleep(0.1)

                click(x=locations_fixed['Dir'][0], y=locations_fixed['Dir'][1], duration=0)
                typewrite(message=OutputDir, interval=0)
                press('enter')
                screenshotTmp_OutputLocation = join(screenshotsPath_OutputLocation, f'{f[:-4]}.png')
                while True:
                    screenshot(screenshotTmp_OutputLocation, region=(locations_fixed['Screenshot Output Location'][0],
                                                                     locations_fixed['Screenshot Output Location'][1],
                                                                     134,
                                                                     20))
                    if OutputDir.split('\\')[-1] in image_to_string(Image.open(screenshotTmp_OutputLocation),
                                                                    lang='eng'):
                        break
                    else:
                        sleep(0.1)

                click(x=locations_fixed['Output Name'][0], y=locations_fixed['Output Name'][1], duration=0)
                sleep(0.5)
                typewrite(message=f'{f[:-4]}.txt', interval=0)
                press('enter')
                sleep(0.75)

                click(x=locations['Convert'][0], y=locations['Convert'][1], duration=0)
                sleep(0.5)

            for locations, f in zip(LOCATIONS[:len(F)], F):
                screenshotTmp_Convert = join(screenshotsPath_Convert, '%s.png' % f[:-4])

                if exists(screenshotTmp_Convert):
                    if 'Complete' in image_to_string(Image.open(screenshotTmp_Convert), lang='eng'):
                        continue

                while True:
                    screenshot(screenshotTmp_Convert,
                               region=(locations['Screenshot'][0], locations['Screenshot'][1], 280, 25))
                    if 'Complete' in image_to_string(Image.open(screenshotTmp_Convert), lang='eng'):
                        break
                    else:
                        sleep(2)
    except (KeyError, Exception, BaseException) as e:
        print(f"\033[1;34mError: '{e}'\nPlease check the parameters in the configuration file!\n"
              f"This terminal will closed in 5s...\033[0m")
        sleep(5)
        sys.exit(0)


def ascii2mat():
    if not exists(join(PROJECT_PATH, 'stream.json')):
        print('\033[1;34mConfig File Not Found!\nPlease Add Configuration File [stream.json] In This Directory.\n'
              'This terminal will closed in 5s...\033[0m')
        sleep(5)
        sys.exit(0)

    with open(join(PROJECT_PATH, 'stream.json'), 'r', encoding='utf-8') as f:
        js = load(f)

    try:
        asciiFold = js['asciiFold']
        matFold = js['matFold']
        processor = js['processor']
        magnification_dB = js['magnification_dB']
    except (KeyError, Exception, BaseException) as e:
        print(f"\033[1;34mError: '{e}'\nPlease check the parameters in the configuration file!\n"
              f"This terminal will closed in 5s...\033[0m")
        sleep(5)
        sys.exit(0)

    if not exists(asciiFold):
        print('\033[1;34mPlease Enter Correct Path of Stream Fold!\nThis terminal will closed in 5s...\033[0m')
        sleep(5)
        sys.exit(0)

    file_list = sorted(listdir(asciiFold), key=lambda x: int(x.split('-')[-2]))
    each_core = int(ceil(len(file_list) / float(processor)))

    if not exists(matFold):
        makedirs(matFold)

    with open(join(matFold, 'log'), 'a') as f:
        f.write('Converted Files\n')

    print("\033[1;34m" + "=" * 47 + " Start " + "=" * 46 + "\033[0m")
    start = time()

    # Multiprocessing acceleration
    pool = Pool(processes=processor)
    for idx, i in enumerate(range(0, len(file_list), each_core)):
        pool.apply_async(convert_ascii2mat, (file_list[i:i + each_core], asciiFold, matFold, magnification_dB,))

    pool.close()
    pool.join()

    end = time()
    print("\033[1;34m" + "=" * 46 + " Report " + "=" * 46 + "\033[0m")
    print("\033[1;34mCalculation Info--Quantity of streaming data: %s\033[0m" % len(file_list))
    print("\033[1;34mFinishing time: {}  |  Time consumption: {:.3f} min\033[0m".format(asctime(localtime(time())),
                                                                                        (end - start) / 60))


def detect():
    if not exists(join(PROJECT_PATH, 'stream.json')):
        print('\033[1;34mConfig File Not Found!\nPlease Add Configuration File [stream.json] In This Directory.\n'
              'This terminal will closed in 5s...\033[0m')
        sleep(5)
        sys.exit(0)

    with open(join(PROJECT_PATH, 'stream.json'), 'r', encoding='utf-8') as f:
        js = load(f)

    try:
        matFold = js['matFold']
        featuresMatFold = js['featuresMatFold']
        eventFold = js['eventFold']
        parallel = js['parallel']
        processor = js['processor']
        first = js['first']
        staLen = js['staLen']
        overlap = js['overlap']
        staWin = js['staWin']
        IZCRT = js['IZCRT']
        ITU = js['ITU']
        alpha = js['alpha']
        backNoiseTime = js['backNoiseTime']
        featuresMatFold = f'{featuresMatFold}_sL{staLen}_oL{overlap}'
    except (KeyError, Exception, BaseException) as e:
        print(f"\033[1;34mError: '{e}'\nPlease check the parameters in the configuration file!\n"
              f"This terminal will closed in 5s...\033[0m")
        sleep(5)
        sys.exit(0)

    if not exists(matFold):
        print('\033[1;34mPlease Enter Correct Path of Mat Fold!\nThis terminal will closed in 5s...\033[0m')
        sleep(5)
        sys.exit(0)

    if not exists(featuresMatFold):
        makedirs(featuresMatFold)

    if first:
        file_list = sorted(listdir(matFold)[1:], key=lambda x: int(x.split('-')[-2]))
    else:
        file_list = []
        for file in listdir(eventFold):
            if file != 'log':
                file_list.append(f"{file.split('_')[0]}_ch1.txt")
        file_list = list(set(file_list))

    each_core = int(ceil(len(file_list) / float(processor)))

    if not exists(eventFold if first else join(eventFold.split('\\')[:-1], f"waveforms_{ITU}")):
        makedirs(eventFold if first else join(eventFold.split('\\')[:-1], f"waveforms_{ITU}"))

    with open(join(eventFold if first else join(eventFold.split('\\')[:-1], f"waveforms_{ITU}"), 'log'), 'a') as f:
        f.write('Parameters config\n')
        f.write('StaLen\t%d\n' % staLen)
        f.write('Overlap\t%d\n' % overlap)
        f.write('StaWin\t%s\n' % staWin)
        f.write('IZCRT\t%f\n' % IZCRT)
        f.write('ITU\t%d\n' % ITU)
        f.write('Alpha\t%f\n' % alpha)
        f.write('BackNoise time\t%d\n\n' % backNoiseTime)
        f.write('Calculated Files\n')

    print("\033[1;34m" + "=" * 47 + " Start " + "=" * 46 + "\033[0m")
    start = time()

    if parallel:
        pool = Pool(processes=processor)
        for idx, i in enumerate(range(0, len(file_list), each_core)):
            pool.apply_async(cut_stream, (file_list[i:i + each_core], matFold,
                                          eventFold if first else join(eventFold.split('\\')[:-1], f"waveforms_{ITU}"),
                                          featuresMatFold, staWin, staLen, overlap, IZCRT, ITU, alpha, backNoiseTime,))

        pool.close()
        pool.join()
    else:
        cut_stream(file_list, matFold, eventFold if first else join(eventFold.split('\\')[:-1], f"waveforms_{ITU}"),
                   featuresMatFold, staWin, staLen, overlap, IZCRT, ITU, alpha, backNoiseTime)

    end = time()
    print("\033[1;34m" + "=" * 46 + " Report " + "=" * 46 + "\033[0m")
    print("\033[1;34mCalculation Info--Quantity of streaming data: %s\033[0m" % len(file_list))
    print("\033[1;34mFinishing time: {}  |  Time consumption: {:.3f} min\033[0m".format(asctime(localtime(time())),
                                                                                        (end - start) / 60))


if __name__ == '__main__':
    freeze_support()
    while True:
        ans = input("Please select an execution mode, enter \033[1;31;40m[check]\033[0m to Check Mouse Coordinates, "
                    "enter \033[1;31;40m[convert]\033[0m to Convert Stream To ASCII, "
                    "enter \033[1;31;40m[reconvert]\033[0m to Reconvert ASCII To Mat, "
                    "enter \033[1;31;40m[detect]\033[0m to Detect AE Events From Mat, "
                    "enter \033[1;31;40m[quit]\033[0m to close: ")
        if ans.strip().lower() == 'check':
            x, y = position()
            print(f'\033[1;34mCurrent position: [{x}, {y}]\033[0m')
        elif ans.strip().lower() == 'convert':
            stream2ascii()
        elif ans.strip().lower() == 'reconvert':
            ascii2mat()
        elif ans.strip().lower() == 'detect':
            detect()
        elif ans.strip().lower() == 'quit':
            sys.exit(0)
