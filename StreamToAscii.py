"""
@version: 1.0
@author: Jonah
@file: StreamToAscii.py
@Created time: 2022/05/14 20:00
@Last Modified: 2022/05/14 21:01
"""

import sys
from pyautogui import doubleClick, click, screenshot, typewrite, press, position
from time import sleep
from os.path import join, exists, dirname
from os import mkdir, listdir
from pytesseract import image_to_string
from PIL import Image
from tqdm import tqdm
from json import load


def app_path():
    """Returns the base application path."""
    if hasattr(sys, 'frozen'):
        # Handles PyInstaller
        return dirname(sys.executable)  # 打包后的exe目录
    return dirname(__file__)  # 没打包前的py目录


PROJECT_PATH = app_path()

if __name__ == '__main__':
    while True:
        ans = input("Please select an execution mode, enter [convert] to Convert Stream Files, "
                    "enter [check] to Check Mouse Coordinates, enter [quit] to close: ")
        if ans.strip() == 'convert':
            break
        elif ans.strip() == 'check':
            x, y = position()
            print(f'Current position: [{x}, {y}]')
        elif ans.strip() == 'quit':
            sys.exit(0)

    if not exists(join(PROJECT_PATH, 'position.json')):
        print(
            'Config File Not Found!\nPlease Add Configuration File [position.json] In This Directory.\nThis terminal '
            'will closed in 5s...')
        sleep(5)
        sys.exit(0)

    with open(join(PROJECT_PATH, 'position.json'), 'r', encoding='utf-8') as f:
        js = load(f)

    INPUT = js['INPUT']
    OUTPUT = js['OUTPUT']

    if not exists(INPUT):
        print('Please Enter Correct Input Path!\nThis terminal will closed in 5s...')
        sleep(5)
        sys.exit(0)

    while True:
        ans = input(
            "Please move this terminal to a suitable location, enter [yes] to continue, enter [quit] to close: ")
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
    OutputDir = join(OUTPUT, 'threshold')

    try:
        locations_fixed = js['locations_dialog']
        LOCATIONS = []
        for k in js['locations_software'].keys():
            LOCATIONS.append(js['locations_software'][k])

        for Path in [screenshotsPath_InputFileName, screenshotsPath_InputLocation, screenshotsPath_Search,
                     screenshotsPath_OutputFileName, screenshotsPath_OutputLocation, screenshotsPath_Convert, OutputDir]:
            if not exists(Path):
                mkdir(Path)

        files = listdir(INPUT)

        first = True
        pbar = tqdm(range(0, len(files), len(LOCATIONS)))
        for i in pbar:
            try:
                F = [files[i + j] for j in range(len(LOCATIONS))]
            except IndexError:
                F = [files[i + j] for j in range(len(files) % len(LOCATIONS))]
            pbar.set_description(f'Processing [{F}]')

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
                                                                    locations_fixed['Screenshot Input File Name'][1], 232,
                                                                    14))
                    if 'Please Select Waveform File to Convert' in image_to_string(Image.open(screenshotTmp_InputFileName),
                                                                                   lang='eng'):
                        break
                    else:
                        sleep(0.1)

                click(x=locations_fixed['Dir'][0], y=locations_fixed['Dir'][1], duration=0)
                typewrite(message=INPUT, interval=0)
                press('enter')
                screenshotTmp_InputLocation = join(screenshotsPath_InputLocation, f'{f[:-4]}.png')
                while True:
                    screenshot(screenshotTmp_InputLocation, region=(locations_fixed['Screenshot Input Location'][0],
                                                                    locations_fixed['Screenshot Input Location'][1], 134,
                                                                    9))
                    if INPUT.split('\\')[-1][:20] in image_to_string(Image.open(screenshotTmp_InputLocation), lang='eng'):
                        break
                    else:
                        sleep(0.1)

                click(x=locations_fixed['Search'][0], y=locations_fixed['Search'][1], duration=0)
                sleep(1)
                typewrite(message=f, interval=0)
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
                                                                     locations_fixed['Screenshot Output File Name'][1], 181,
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
                                                                     locations_fixed['Screenshot Output Location'][1], 134,
                                                                     20))
                    if OutputDir.split('\\')[-1] in image_to_string(Image.open(screenshotTmp_OutputLocation), lang='eng'):
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
        print(f"Error: '{e}'\nPlease check the parameters in the configuration file!\nThis terminal will closed in 5s...")
        sleep(5)
        sys.exit(0)
