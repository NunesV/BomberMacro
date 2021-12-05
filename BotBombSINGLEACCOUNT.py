
import telegram
import colorama
import pyautogui
import time
import threading
import configparser
import random
from colorama import Fore
from datetime import datetime
import glob
import cv2
import requests
from cv2 import cv2
import numpy as np
import mss
import sys
import yaml

if __name__ == '__main__':

    stream = open("naoalterarporenquanto.yaml", 'r')
    c = yaml.safe_load(stream)
ct = c['threshold']

pyautogui.PAUSE = c['time_intervals']['interval_between_moviments']

pyautogui.FAILSAFE = True


go_work_img = cv2.imread('targets/go-work.png')
commom_img = cv2.imread('targets/commom-text.png')
arrow_img = cv2.imread('targets/go-back-arrow.png')
hero_img = cv2.imread('targets/hero-icon.png')
x_button_img = cv2.imread('targets/x.png')
teasureHunt_icon_img = cv2.imread('targets/treasure-hunt-icon.png')
ok_btn_img = cv2.imread('targets/ok.png')
connect_wallet_btn_img = cv2.imread('targets/connect-wallet.png')
select_wallet_hover_img = cv2.imread('targets/select-wallet-1-hover.png')
select_metamask_no_hover_img = cv2.imread('targets/select-wallet-1-no-hover.png')
sign_btn_img = cv2.imread('targets/select-wallet-2.png')
new_map_btn_img = cv2.imread('targets/new-map.png')
green_bar = cv2.imread('targets/green-bar.png')
full_stamina = cv2.imread('targets/full-stamina.png')
puzzle_img = cv2.imread('targets/puzzle.png')
piece = cv2.imread('targets/piece.png')
robot = cv2.imread('targets/robot.png')
slider = cv2.imread('targets/slider.png')



def logger(message, progress_indicator = False):
    global last_log_is_progress



    # Start progress indicator and append dots to in subsequent progress calls
    if progress_indicator:
        if not last_log_is_progress:
            last_log_is_progress = True
            sys.stdout.write('\n => .')
            sys.stdout.flush()
        else:
            sys.stdout.write('.')
            sys.stdout.flush()

        return

    if last_log_is_progress:
        sys.stdout.write('\n\n')
        sys.stdout.flush()
        last_log_is_progress = False



    datetime = time.localtime()
    formatted_datetime = time.strftime("%d/%m/%Y %H:%M:%S", datetime)

    formatted_message = "[{}] \n => {} \n\n".format(formatted_datetime, message)


    print(formatted_message)

    if (c['save_log_to_file'] == True):
        logger_file = open("logger.log", "a")
        logger_file.write(formatted_message)
        logger_file.close()

    return True



def clickGreenBarButtons():
    # ele clicka nos q tao trabaiano mas axo q n importa
    offset = 130
    green_bars = positions(green_bar, threshold=ct['green_bar'])
    logger('%d green bars detected' % len(green_bars))
    buttons = positions(go_work_img, threshold=ct['go_to_work_btn'])
    logger('%d buttons detected' % len(buttons))

    not_working_green_bars = []
    for bar in green_bars:
        if not isWorking(bar, buttons):
            not_working_green_bars.append(bar)
    if len(not_working_green_bars) > 0:
        logger('%d buttons with green bar detected' % len(not_working_green_bars))
        logger('Clicking in %d heroes.' % len(not_working_green_bars))

    # se tiver botao com y maior que bar y-10 e menor que y+10
    for (x, y, w, h) in not_working_green_bars:
        # isWorking(y, buttons)
        pyautogui.moveTo(x+offset+(w/2),y+(h/2),1)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1
        if hero_clicks > 20:
            logger('too many hero clicks, try to increase the go_to_work_btn threshold')
            return
        #cv2.rectangle(sct_img, (x, y) , (x + w, y + h), (0,255,255),2)
    return len(not_working_green_bars)

def clickFullBarButtons():
    offset = 100
    full_bars = positions(full_stamina, threshold=ct['default'])
    buttons = positions(go_work_img, threshold=ct['go_to_work_btn'])

    not_working_full_bars = []
    for bar in full_bars:
        if not isWorking(bar, buttons):
            not_working_full_bars.append(bar)

    if len(not_working_full_bars) > 0:
        logger('Clicking in %d heroes.' % len(not_working_full_bars))

    for (x, y, w, h) in not_working_full_bars:
        pyautogui.moveTo(x+offset+(w/2),y+(h/2),1)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1

    return len(not_working_full_bars)


def refreshHeroesPositions():
    clickBtn(arrow_img)
    clickBtn(teasureHunt_icon_img)
    # time.sleep(random.randrange(3, 6))
    clickBtn(teasureHunt_icon_img)



def sobelOperator(img):
    scale = 1
    delta = 0
    ddepth = cv2.CV_16S

    img = cv2.GaussianBlur(img, (3, 3), 0)
    gray = img
    grad_x = cv2.Sobel(gray, ddepth, 1, 0, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    grad_y = cv2.Sobel(gray, ddepth, 0, 1, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)
    grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    return cv2.cvtColor(grad, cv2.COLOR_BGR2GRAY)

def findPuzzlePieces(result, piece_img, threshold=0.5):
    piece_w = piece_img.shape[1]
    piece_h = piece_img.shape[0]
    yloc, xloc = np.where(result >= threshold)


    r= []
    for (piece_x, piece_y) in zip(xloc, yloc):
        r.append([int(piece_x), int(piece_y), int(piece_w), int(piece_h)])
        r.append([int(piece_x), int(piece_y), int(piece_w), int(piece_h)])


    r, weights = cv2.groupRectangles(r, 1, 0.2)

    if len(r) < 2:
        print('threshold = %.3f' % threshold)
        return findPuzzlePieces(result, piece_img,threshold-0.01)

    if len(r) == 2:
        print('match')
        return r

    if len(r) > 2:
        print('overshoot by %d' % len(r))

        return r

def getRightPiece(puzzle_pieces):
    xs = [row[0] for row in puzzle_pieces]
    index_of_right_rectangle = xs.index(max(xs))

    right_piece = puzzle_pieces[index_of_right_rectangle]
    return right_piece

def getLeftPiece(puzzle_pieces):
    xs = [row[0] for row in puzzle_pieces]
    index_of_left_rectangle = xs.index(min(xs))

    left_piece = puzzle_pieces[index_of_left_rectangle]
    return left_piece

def show(rectangles, img = None):

    if img is None:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            img = np.array(sct.grab(monitor))

    for (x, y, w, h) in rectangles:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255,255,255,255), 2)

    # cv2.rectangle(img, (result[0], result[1]), (result[0] + result[2], result[1] + result[3]), (255,50,255), 2)
    cv2.imshow('img',img)
    cv2.waitKey(0)

def getPiecesPosition(t = 150):
    popup_pos = positions(robot)
    if len(popup_pos) == 0:
        print('puzzle not found')
        return
    rx, ry, _, _ = popup_pos[0]

    w = 380
    h = 200
    x_offset = -40
    y_offset = 65

    y = ry + y_offset
    x = rx + x_offset

    img = printSreen()
    #TODO tirar um poco de cima

    cropped = img[ y : y + h , x: x + w]
    blurred = cv2.GaussianBlur(cropped, (3, 3), 0)
    edges = cv2.Canny(blurred, threshold1=t/2, threshold2=t,L2gradient=True)
    # img = cv2.Laplacian(img,cv2.CV_64F)

    # gray_piece_img = cv2.cvtColor(piece, cv2.COLOR_BGR2GRAY)
    piece_img = cv2.cvtColor(piece, cv2.COLOR_BGR2GRAY)
    print('----')
    print(piece_img.shape)
    print(edges.shape)
    print('----')
    # piece_img = cv2.Canny(gray_piece_img, threshold1=t/2, threshold2=t,L2gradient=True)
    # result = cv2.matchTemplate(edges,piece_img,cv2.TM_CCOEFF_NORMED)
    result = cv2.matchTemplate(edges,piece_img,cv2.TM_CCORR_NORMED)

    puzzle_pieces = findPuzzlePieces(result, piece_img)

    if puzzle_pieces is None:
        return

    # show(puzzle_pieces, edges)
    # exit()

    absolute_puzzle_pieces = []
    for i, puzzle_piece in enumerate(puzzle_pieces):
        px, py, pw, ph = puzzle_piece
        absolute_puzzle_pieces.append( [ x + px, y + py, pw, ph])

    absolute_puzzle_pieces = np.array(absolute_puzzle_pieces)
    # show(absolute_puzzle_pieces)
    return absolute_puzzle_pieces

def getSliderPosition():
    slider_pos = positions(slider)
    if len (slider_pos) == 0:
        return False
    x, y, w, h = slider_pos[0]
    position = [x+w/2,y+h/2]
    return position

def solveCapcha():
    robote = glob.glob("Captcha/robot*.png")
    robo = pyautogui.locateCenterOnScreen(robote[0], confidence =0.5)
    if robo != None :
        pieces_start_pos = getPiecesPosition()
        if pieces_start_pos is None :
            return
        slider_start_pos = getSliderPosition()

        x,y = slider_start_pos
        pyautogui.moveTo(x,y,1)
        pyautogui.mouseDown()
        pyautogui.moveTo(x+300 ,y,0.5)
        pieces_end_pos = getPiecesPosition()


        piece_start, _, _, _ = getLeftPiece(pieces_start_pos)
        piece_end, _, _, _ = getRightPiece(pieces_end_pos)
        piece_middle, _, _, _  = getRightPiece(pieces_start_pos)
        slider_start, _, = slider_start_pos
        slider_end, _ = getSliderPosition()


        piece_domain = piece_end - piece_start
        middle_piece_in_percent = (piece_middle - piece_start)/piece_domain


        slider_domain = slider_end - slider_start
        slider_awnser = slider_start + (middle_piece_in_percent * slider_domain)
        # arr = np.array([[int(piece_start),int(y-20),int(10),int(10)],[int(piece_middle),int(y-20),int(10),int(10)],[int(piece_end-20),int(y),int(10),int(10)],[int(slider_awnser),int(y),int(20),int(20)]])

        pyautogui.moveTo(slider_awnser,y,0.5)
        pyautogui.mouseUp()

        return()
    else:
        return()

    # show(arr)



pyautogui.FAILSAFE = False
now = datetime.now()
current_time = now.strftime("[%H:%M:%S]")


colorama.init()
config = configparser.ConfigParser()
config.read('settings.ini')


MapsCleared = 0
CiclesDone = 0
ErrorsFound = 0


BotaoWork = eval(config.get('settings', 'BotaoWork'), {}, {})
BotaoClose = eval(config.get('settings', 'BotaoClose'), {}, {})
BotaoMapa = eval(config.get('settings', 'BotaoMapa'), {}, {})
BotaoVoltar = eval(config.get('settings', 'BotaoVoltar'), {}, {})
BotaoHeroes = eval(config.get('settings', 'BotaoHeroes'), {}, {})
BotaoConnect = eval(config.get('settings', 'BotaoConnect'), {}, {})
BotaoMeta = eval(config.get('settings', 'BotaoMeta'), {}, {})
BotaoNewMap = eval(config.get('settings', 'BotaoNewMap'), {}, {})
Botaobau = eval(config.get('settings', 'Botaobau'), {}, {})
Botaobauclose = eval(config.get('settings', 'Botaobauclose'), {}, {})


IdTelegram = str(config['settings']['IdTelegram'])
tokent = str(config['settings']['tokenapitelegram'])

PosicaoScroll = eval(config.get('settings', 'PosicaoScroll'), {}, {})
NumScroll = int(config['settings']['NumScroll'])
VelScroll = int(config['settings']['VelScroll'])

DelayFarm = int(config['settings']['DelayFarm'])
DelayStats = int(config['settings']['DelayStats'])
Heroes = int(config['settings']['Heroes'])


DelayToStart = int(config['settings']['DelayToStart'])
AntiDetection = bool(config.getboolean('settings', 'AntiDetection'))
AntiBot = int
MultiAccount = bool(config.getboolean('settings', 'MultiAccount'))
Accounts = int(config['settings']['Accounts'])

bot = telegram.Bot(token=tokent)


# Put the heroes to work function
def work():
    global CiclesDone
    print(datetime.now().strftime("[%H:%M:%S]") + '- Colocando a galera pra trampar...')
    time.sleep(random.randrange(3, 8))
    pyautogui.moveTo(BotaoVoltar[0]-random.randrange(-7, 7),(BotaoVoltar[1]-random.randrange(-6, 6)))
    pyautogui.click()
    time.sleep(random.randrange(3, 8))
    pyautogui.moveTo(BotaoHeroes[0]-random.randrange(-7, 7),(BotaoHeroes[1]-random.randrange(-6, 6)))
    pyautogui.click()
    time.sleep(random.randrange(10, 16))
    solveCapcha()
    time.sleep(random.randrange(10, 16))
    pyautogui.moveTo(PosicaoScroll)
    time.sleep(0.5)
    pyautogui.click()

    for s in range(NumScroll):
        pyautogui.scroll(VelScroll)
        time.sleep(0.5)
    time.sleep(random.randrange(2, 4))

    for _ in range(Heroes):
        pyautogui.moveTo((BotaoWork[0]-random.randrange(-7, 7)),(BotaoWork[1]-random.randrange(-6, 6)))
        pyautogui.click()
        time.sleep(random.randrange(2, 4))

    time.sleep(1)
    pyautogui.moveTo(BotaoClose[0]-random.randrange(-7, 7),(BotaoClose[1]-random.randrange(-6, 6)))
    pyautogui.click()
    CiclesDone = CiclesDone + 1



# Open map from initial page
def abrir_mapa():
    time.sleep(random.randrange(3, 8))
    solveCapcha()
    print(datetime.now().strftime("[%H:%M:%S]") + "Opening map...")
    time.sleep(random.randrange(3, 6))
    pyautogui.moveTo(BotaoMapa[0]-random.randrange(-7, 7),(BotaoMapa[1]-random.randrange(-6, 6)))
    pyautogui.click()

#Single Account farm
def bot():
    while True:
        abrir_mapa()
        time.sleep(random.randrange(3, 8))
        work()
        time.sleep(random.randrange(3, 8))
        abrir_mapa()
        time.sleep(random.randrange(3, 8))
        tempo_farm()
        if stop_threads:
            break


def sendprint():
    global IdTelegram
    global tokent
    bot = telegram.Bot(token=tokent)
    bauzin = glob.glob("Imgs/bauzi*.png")
    bauzin = pyautogui.locateCenterOnScreen(bauzin[0], confidence =0.5)
    if bauzin != None :
        pyautogui.moveTo(Botaobau[0]-random.randrange(-7, 7),(Botaobau[1]-random.randrange(-6, 6)))
        time.sleep(random.randrange(2, 4))
        pyautogui.dragTo(button='left')
        time.sleep(random.randrange(2, 4))
        print = pyautogui.screenshot(region=(610,314,750,500))
        print = print.save('Imgs/prints.png')
        print = glob.glob("Imgs/prints*.png")
        time.sleep(random.randrange(2, 4))
        pyautogui.moveTo(Botaobauclose[0]-random.randrange(-7, 7),(Botaobauclose[1]-random.randrange(-6, 6)))
        time.sleep(random.randrange(2, 4))
        pyautogui.dragTo(button='left')
        time.sleep(random.randrange(2, 4))
        bot.send_photo(chat_id=IdTelegram, caption=("\U0001F4A3 "+datetime.now().strftime("%H:%M:%S")+" \U0001F911 "), photo=open(print[0], 'rb'))
        return()
        pass
    else:
        pass




# Time to delay the work function
def tempo_farm():
    global DelayFarm
    global AntiBot
    global AntiDetection
    if AntiDetection:
        AntiBot = random.randint(300, 1500)
    else:
        AntiBot = 0

    anti_bot = int(AntiBot)
    mins, secs = divmod(anti_bot, 60)
    formatTime = (f'{mins:02d}:{secs:02d}')
    print(datetime.now().strftime("[%H:%M:%S]") + f"- Adicionado: [{formatTime}] Adicionado os minutos para descaraterizar o bot")
    countdown = DelayFarm + anti_bot

    while countdown:
        if stop_threads:
            break
        mins, secs = divmod(countdown, 60)
        hours, mins = divmod(mins, 60)
        timeformat = (f'{hours:d}:{mins:02d}:{secs:02d}')
        print(datetime.now().strftime("[%H:%M:%S]") + f"- Heroes trabalhando ou descansando. Aguardando o tempo:\t[{timeformat}]\r",
              end="")
        time.sleep(1)
        countdown -= 1


stop_threads = False
# Check for errors
def check_errors():
    global ErrorsFound
    global stop_threads


    while True:

        errors = glob.glob("Captcha/*.png")
        for erro in errors:
            erro = pyautogui.locateCenterOnScreen(erro, confidence=0.8)
            if erro:
                print("\n Captcha do demonio encontrato, sera resolvido e continuara normalmente \n")
                solveCapcha()
                time.sleep(60)

        errors = glob.glob("Errors/*.png")
        for erro in errors:
            erro = pyautogui.locateCenterOnScreen(erro, confidence=0.8)
            if erro:
                print("\n Erro encontrado, jogo será reiniciado e logado novamente \n")
                pyautogui.moveTo(erro)
                time.sleep(0.7)
                pyautogui.click(erro)
                pyautogui.hotkey('ctrl','shift', 'r')
                ErrorsFound = ErrorsFound + 1
                stop_threads = True
                connect()
                time.sleep(60)


#Click next map
def check_map():
    global MapsCleared
    maps = glob.glob("NewMap/*.png")
    time.sleep(random.randrange(3, 8))
    while True:
        for map in maps:
            map = pyautogui.locateOnScreen(map, confidence=0.5)
            if map != None:
                pyautogui.moveTo(BotaoNewMap[0]-random.randrange(-5, 5),(BotaoNewMap[0]-random.randrange(-5, 5)))
                time.sleep(0.8)
                pyautogui.click()
                time.sleep(1)
                pyautogui.click()
                MapsCleared = MapsCleared + 1
                solveCapcha()



# Connect from mainpage
def connect():
    retries = 0

    time.sleep(random.randrange(3, 8))


    while True:
        aux = None
        auxAba = None

        img = glob.glob("Imgs/MAI*.png")
        img = pyautogui.locateCenterOnScreen(img[0], confidence =0.5)
        aux = img

        logadog = glob.glob("Imgs\logad*.png")
        logado = pyautogui.locateOnScreen(logadog[0], confidence =0.5)
        if logado != None:
            print("Game já aberto, bot iniciando!\n")
            threads()
            break
        else:
            print("Procurando o botão do conect\n" )
            if aux != None:
                print("\n")
                print(Fore.MAGENTA)
                print("\n")
                aux2 = aux
                pyautogui.moveTo(BotaoConnect)
                pyautogui.dragTo(button='left')
                time.sleep(random.randrange(3, 6))
                retries = retries + 1
                print(f"\Tentativas de login:{retries}\n")
                time.sleep(random.randrange(3, 8))
                solveCapcha()
                time.sleep(5 )
                signg = glob.glob("Imgs/SIG*.png")
                sign = pyautogui.locateOnScreen(signg[0], confidence =0.5)
                if sign != None:
                    print("Botao connect encontrado")
                    aux = sign
                    pyautogui.moveTo(BotaoMeta)
                    time.sleep(random.randrange(3, 6))
                    pyautogui.click()
                    print("Botao de assinar clicado")
                    time.sleep(random.randrange(10, 16))
                else:
                    time.sleep(10)
                    print("Assinar nao encontrado, atualizando.")
                    pyautogui.hotkey('ctrl','shift', 'r')

                time.sleep(12)
                logadog = glob.glob("Imgs\logad*.png")
                logado = pyautogui.locateOnScreen(logadog[0], confidence =0.5)
                if logado != None:
                    print("Login realizado com sucesso, bot iniciando!")
                    threads()
                else:
                    pyautogui.hotkey('ctrl','shift', 'r')
                    time.sleep(10)
                    print("Login nao realizado com sucesso, atualizando.")

                if retries >= 10:
                    telegram_bot_sendtext("\U000023F3"+ datetime.now().strftime("[%H:%M:%S]") + "\n 10 tentativas de login realizadas, verifique por que pode ter dado ruim! " )
                    pyautogui.hotkey('ctrl','shift', 'r')
                    retries = 0
                else:
                    pass
            else:
                print("Conectar nao encontrado, atualizando.")
                pyautogui.hotkey('ctrl','shift', 'r')


        time.sleep(20)

# Show farm stats
def show_stats():
    global bot
    mapsreported = 0
    cliclesreported = 0
    errorsreported = 0
    while True:
        time.sleep(300)
        if CiclesDone > cliclesreported:
            cliclesreported = CiclesDone
            print(Fore.BLUE + ("\n") + datetime.now().strftime("[%H:%M:%S]") + "- Quantidade de vezes que foram colocados para trabalhar: " + str(CiclesDone))
            bot.send_message(chat_id=IdTelegram, text=("\U000023F3 "+ datetime.now().strftime("[%H:%M:%S]") + " \U0001F477 Quantidade de vezes que foram colocados para trabalhar: " + str(CiclesDone)))
        if MapsCleared > mapsreported:
            mapsreported = MapsCleared
            print(Fore.BLUE + ("\n") + datetime.now().strftime("[%H:%M:%S]") + "- Mapas feitos: " + str(MapsCleared))
            bot.send_message(chat_id=IdTelegram, text=("\U000023F3"+ datetime.now().strftime("[%H:%M:%S]") + " \U0001F5FA Mapas explodidos: " + str(MapsCleared)))
        if ErrorsFound > errorsreported:
            ErrorsFound = errorsreported
            print(Fore.BLUE + ("\n") + datetime.now().strftime("[%H:%M:%S]") + "- Erros encontrados: " + str(ErrorsFound))
            bot.send_message(chat_id=IdTelegram, text=("\U00001F6D1"+ datetime.now().strftime("[%H:%M:%S]") + " \U0001F6A8 Erros encontrados: " + str(ErrorsFound)))
        sendprint()

        time.sleep(DelayStats)

threadss = []

# Start threading
def threads():
    global threadss
    global stop_threads
    stop_threads = False
    t1 = threading.Thread(target=check_errors)
    t2 = threading.Thread(target=check_map)

    if MultiAccount:
        t3 = threading.Thread(target=multiacc)
    else:
        t3 = threading.Thread(target=bot)

    t4 = threading.Thread(target=show_stats)
    #t5 = threading.Thread(target=connect)
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    #t5.start()
    threadss.append(t1)
    threadss.append(t2)
    threadss.append(t3)
    threadss.append(t4)
    #threadss.append(t5)

    for thread in threadss:
        thread.join()



def botmenu():
    menu = int(input(
        "Opçoes :\n1)Rodar bot\n2)Testar as funcoes(use para testar as funcoes e mapeamentos caso tiver problemas ou for primeiro uso)\n3)Sair\n\n"))
    print(Fore.MAGENTA)
    if menu == 1:
        defaultdelay = 10
        print(datetime.now().strftime(
            "[%H:%M:%S]") + f"Bot vai iniciar em  {defaultdelay + DelayToStart} segundos. Va para a pagina inicial do jogo ou na tela de connect.")
        time.sleep(10 + DelayToStart)
        connect()
    elif menu == 2:
        menu2 = int(input(datetime.now().strftime(
            "\n[%H:%M:%S]") + "Escolha uma funcao para testar:\n1)Abrir mapa \n2)Colocando heroes para trabalhar\n3)Conectar na pagina de login\n4)Procurar e clicar no prox mapa\n5)Procurar erros / captcha \n7)Sair\n\n"))
        if menu2 == 1:
            print(Fore.CYAN + datetime.now().strftime(
                "[%H:%M:%S]") + "Va para pagina que quer testar e aguarde 5 segundos.")
            time.sleep(random.randrange(3, 8))
            abrir_mapa()
            botmenu()
        if menu2 == 2:
            print(Fore.CYAN + datetime.now().strftime(
                "[%H:%M:%S]") + "Va para pagina que quer testar e aguarde 5 segundos.")
            time.sleep(random.randrange(3, 8))
            work()
            botmenu()
        if menu2 == 3:
            print(Fore.CYAN + datetime.now().strftime(
                "[%H:%M:%S]") + "Va para pagina que quer testar e aguarde 5 segundos.")
            time.sleep(random.randrange(3, 8))
            connect()
            botmenu()
        if menu2 == 4:
            print(Fore.CYAN + datetime.now().strftime(
                "[%H:%M:%S]") + "Va para pagina que quer testar e aguarde 5 segundos.")
            time.sleep(random.randrange(3, 8))
            check_map()
            botmenu()
        if menu2 == 5:
            print(Fore.CYAN + datetime.now().strftime(
                "[%H:%M:%S]") + "Va para pagina que quer testar e aguarde 5 segundos.")
            time.sleep(random.randrange(3, 8))
            check_errors()
            botmenu()
        if menu2 == 6:
            print(Fore.CYAN + datetime.now().strftime(
                "[%H:%M:%S]") + "Va para pagina que quer testar e aguarde 5 segundos.")
            time.sleep(random.randrange(3, 8))
            botmenu()
        if menu2 == 7:
            print(Fore.GREEN)
            botmenu()
        else:
            print(Fore.RED + datetime.now().strftime("[%H:%M:%S]") + "Escolheu errado")
    elif menu == 3:
        print("Erro")
        #sys.exit()
    else:
        print(Fore.RED + datetime.now().strftime("[%H:%M:%S]") + "Escolheu errado")

botmenu()
