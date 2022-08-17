#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join
from statistics import mean

import yaml
from psychopy import visual, event, logging, gui, core

from misc.screen_misc import get_screen_res, get_frame_rate
from itertools import combinations_with_replacement, product

@atexit.register
#Nie interesuje nas to, ma zosta?: zapisuje wyniki bada?, wywo?uje si? automatycznie jak co? si? zepsuje
def save_beh_results():
    """
    Save results of experiment. Decorated with @atexit in order to make sure, that intermediate
    results will be saved even if interpreter will broke.
    """
    with open(join('results', PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()

#w file_name pisz? nazw? pliku który chc? wy?wietli?, np przerw?
def show_image(win, file_name, size, key='f7'):
    """
    Show instructions in a form of an image.
    """
    image = visual.ImageStim(win=win, image=file_name,
                             interpolate=True, size=size)
    image.draw()
    win.flip()
    clicked = event.waitKeys(keyList=[key, 'return', 'enter'])
    if clicked == [key]:
        logging.critical(
            'Experiment finished by user! {} pressed.'.format(key[0]))
        exit(0)
    win.flip()

#pokazuje tekst, np. powitanie
def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'):
    """
    Check (during procedure) if experimentator doesn't want to terminate.
    """
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error(
            'Experiment finished by user! {} pressed.'.format(key))


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg,
                          height=20, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', '1', '2', '9', '0'])
    if key == ['f7']:
        abort_with_error(
            'Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err):
    logging.critical(err)
    raise Exception(err)

RESULTS = list()
RESULTS.append(['PART_ID', 'Part', 'Block_no', 'Trial_no', 'Reaction time', 'Correctness', '...'])

def main():
    trial_no=0
    global PART_ID

    info={'IDENTYFIKATOR': '', u'P\u0141EC': ['M', "K"], 'WIEK': '20'}
    dictDlg=gui.DlgFromDict(
        dictionary=info, title='Experiment title, fill by your name!')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    clock=core.Clock()
    conf=yaml.load(open('config.yaml', encoding='utf-8'))

    win=visual.Window(list(SCREEN_RES.values()), fullscr=False, monitor='testMonitor', units='pix',
                                       screen=0, color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    FRAME_RATE=60

    if FRAME_RATE != conf['FRAME_RATE']:
        dlg=gui.Dlg(title="Critical error")
        dlg.addText(
            'Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID=info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']
    logging.LogFile(join('results', PART_ID + '.log'),
                    level=logging.INFO)
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    # TUTAJ PRZYGOTOWUJEMY WSZYSTKIE BOD?CE (strza?k?, maski)

    fix_cross = visual.TextStim(win, text='+', height=100, color=conf['FIX_CROSS_COLOR'])
    stim = visual.TextStim(win, text='', height=conf['STIM_SIZE'], color=conf['STIM_COLOR'])

    # TRENING
    show_image(win, join('.', 'images', 'instrukcja.png'),700)

    trial_no += 1
    show_info(win, join('.', 'messages', 'before_training.txt'))
    for csi in range(15):
        keyPressed, rt=run_trial(win, conf, stim, fix_cross, clock)
        RESULTS.append([PART_ID, 'training', 0, trial_no, rt, keyPressed, stim.color])
        if (keyPressed==1 and stim.color=='pink') or (keyPressed==2 and stim.color=='red') or (keyPressed==9 and stim.color=='green') or (keyPressed==0 and stim.color=='blue'):
            corr=1
        else:
            corr=0


        # it's often good presenting feedback in trening trials
        feedb="Poprawnie" if corr==1 else "Niepoprawnie"
        feedb=visual.TextStim(win, text=feedb, height=50,
                              color=conf['FIX_CROSS_COLOR'])
        feedb.draw()
        win.flip()
        core.wait(1)
        win.flip()

        trial_no += 1


    show_info(win, join('.', 'messages', 'before_experiment.txt'))

    for block_no in range(conf['NO_BLOCKS']):
        for _ in range(conf['Trials in block']):#TRIALS IN BLOCK TRZEBA USTAWI? W CONIG
            keyPressed, rt=run_trial(win, conf, stim, fix_cross, clock)
            RESULTS.append([PART_ID, 'experiment', block_no, trial_no, rt, keyPressed, stim.color])
            trial_no += 1

        show_image(win, join('.', 'images', 'break.jpg'),
                   size=(SCREEN_RES['width'], SCREEN_RES['height']))
        for _ in range(conf['Trials in block']):#TRIALS IN BLOCK TRZEBA USTAWI? W CONIG
            keyPressed, rt=run_trial(win, conf, stim, fix_cross, clock)
            RESULTS.append([PART_ID, 'experiment', block_no, trial_no, rt, corr])
            trial_no += 1

        # === Cleaning time ===
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()
    core.quit


def run_trial(win, conf, stim, fix_cross, clock):
    """
    Prepare and present single trial of procedure.
    Input (params) should consist all data need for presenting stimuli.
    If some stimulus (eg. text, label, button) will be presented across many trials.
    Should be prepared outside this function and passed for .draw() or .setAutoDraw().
    All behavioral data (reaction time, answer, etc. should be returned from this function)
    """

    # Przygotowujemy wszystkie bod?ce

    slowa=["RÓ\u017BOWY","CZERWONY", "ZIELONY", "NIEBIESKI"]
    stim.text=random.choice(slowa)
    stim.color=random.choice(["pink", "red", "green", "blue"])

    # === Start pre-trial  stuff ===
    # wy?wietlanie fixation cross:
    for _ in range(conf['FIX_CROSS_TIME']):
        fix_cross.draw()
        win.flip()

    event.clearEvents()
    win.callOnFlip(clock.reset)

    for _ in range(conf['STIM_TIME']):
        reaction=event.getKeys(keyList=['1', '2', '9', '0'], timeStamped=clock)
        if reaction:
            break
        stim.draw()
        win.flip()

    if not reaction:  # no reaction during stim time, allow to answer after that
        #question_frame.draw()
        #question_label.draw()
        win.flip()
        reaction=event.waitKeys(keyList=['1', '2', '9', '0'], maxWait=conf['REACTION_TIME'], timeStamped=clock)
    # === Trial ended, prepare data for send  ===
    if reaction:
        keyPressed, rt=reaction[0]
    else:  # timeout
        keyPressed='no_key'
        rt=-1.0

    return keyPressed, rt  # return all data collected during trial

if __name__ == '__main__':
    PART_ID=''
    SCREEN_RES=get_screen_res()
    main()