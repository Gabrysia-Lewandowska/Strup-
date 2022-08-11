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
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error(
            'Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err):
    """
    Call if an error occured.
    """
    logging.critical(err)
    raise Exception(err)


# GLOBALS

RESULTS = list()  # list in which data will be colected
RESULTS.append(['PART_ID', 'Trial_no', 'Reaction time', 'Correctness', '...'])  # ... Results header

def main():
    trial_no=1
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global

    # === Dialog popup: PYTANIE O IDENTYFIKATOR ===
    info={'IDENTYFIKATOR': '', u'P\u0141EC': ['M', "K"], 'WIEK': '20'}
    dictDlg=gui.DlgFromDict(
        dictionary=info, title='Experiment title, fill by your name!')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    clock=core.Clock()
    # load config, all params are there
    conf=yaml.load(open('config.yaml', encoding='utf-8'))

    # === Scene init ===
    win=visual.Window(list(SCREEN_RES.values()), fullscr=False, monitor='testMonitor', units='pix',
                                       screen=0, color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    FRAME_RATE=60

    # check if a detected frame rate is consistent with a frame rate for witch experiment was designed
    # important only if milisecond precision design is used
    if FRAME_RATE != conf['FRAME_RATE']:
        dlg=gui.Dlg(title="Critical error")
        dlg.addText(
            'Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID=info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']
    logging.LogFile(join('results', PART_ID + '.log'),
                    level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    # === Prepare stimulus here ===
    # TUTAJ PRZYGOTOWUJEMY WSZYSTKIE BOD?CE (strza?k?, maski)

    fix_cross = visual.TextStim(win, text='+', height=100, color=conf['FIX_CROSS_COLOR'])
    stim = visual.TextStim(win, text='', height=conf['STIM_SIZE'], color=conf['STIM_COLOR'])


    # TRENING
    #show_info(win, join('.', 'messages', 'hello.txt'))
    show_image(win, join('.', 'images', 'instrukcja.png'),700)

    trial_no += 1
    #je?eli potrzebujemy dwóch kartek instrukcji, jak nie, to mo?na usun??)
    show_info(win, join('.', 'messages', 'before_training.txt'))
    csi_list=[conf['TRAINING_CSI']] * conf['NO_TRAINING_TRIALS'][1]
    for csi in csi_list:
        keyPressed, rt=run_trial(win, conf, stim, fix_cross, clock) # <- TRZEBA TU DOPISA? JAKIE? PARAMETRY, M IN CLOCK (we wszystkich wywo?aniach run trial)
        corr=...
        RESULTS.append([PART_ID, trial_no, 'training', ...])

        # it's often good presenting feedback in trening trials
        feedb="Poprawnie" if corr else "Niepoprawnie"
        feedb=visual.TextStim(win, text=feedb, height=50,
                              color=conf['FIX_CROSS_COLOR'])
        feedb.draw()
        win.flip()
        core.wait(1)
        win.flip()

        trial_no += 1
        # EKSPERYMENTnb

    show_info(win, join('.', 'messages', 'before_experiment.txt'))

    for block_no in range(conf['NO_BLOCKS']):
        for _ in range(conf['Trials in block']):#TRIALS IN BLOCK TRZEBA USTAWI? W CONIG
            keyPressed, rt=run_trial(win, conf, stim, fix_cross, clock)
            RESULTS.append([PART_ID, block_no, trial_no, 'experiment', ...])
            trial_no += 1

        show_image(win, os.path.join('.', 'images', 'break.jpg'),
                   size=(SCREEN_RES['width'], SCREEN_RES['height']))

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

    slowa=["RÓ?OWY", "ZIELONY", "NIEBIESKI", "CZERWONY"]
    stim.text = random.choice(slowa)
    stim.color=random.choice(["red", "green", "pink", "blue"])

    # === Start pre-trial  stuff ===
    # wy?wietlanie fixation cross:
    for _ in range(conf['FIX_CROSS_TIME']):
        fix_cross.draw()
        win.flip()

    # === Start trial ===
    # This part is time-crucial. All stims must be already prepared.
    # Only .draw() .flip() and reaction related stuff goes there.
    event.clearEvents()
    # make sure, that clock will be reset exactly when stimuli will be drawn
    win.callOnFlip(clock.reset)

    for _ in range(conf['STIM_TIME']):  # present stimuli
        reaction=event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
        if reaction:  # break if any button was pressed
            break
        stim.draw()
        win.flip()

    if not reaction:  # no reaction during stim time, allow to answer after that
        #question_frame.draw()
        #question_label.draw()
        win.flip()
        reaction=event.waitKeys(keyList=list(
            conf['REACTION_KEYS']), maxWait=conf['REACTION_TIME'], timeStamped=clock)
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