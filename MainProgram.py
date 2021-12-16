from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier
from credentials import *
import json
from websocket import create_connection
import ssl
import time
import requests
import joblib
import numpy as np
import pandas as pd
import warnings
import os
import sys
warnings.filterwarnings("ignore")

def menu():
    print('1 - Sterowanie Live')
    print('2 - Trening modelu')
    print('3 - Test modelu')
    print('4 - Klasyfikacja Live (bez wysyłania komend)')
    print('0 - Wyjście')


def cechy():
    print('1 - Napięcie')
    print('2 - Moc pasma')
    print('3 - Wariancja')
    print('4 - FFT')
    print('5 - FFT-Pasma')
    print('0 - Wyjście')


def connect():
    ws = create_connection("wss://localhost:6868/", sslopt={"cert_reqs": ssl.CERT_NONE})

    ws.send(json.dumps({
        "id": 1,
        "jsonrpc": "2.0",
        "method": "controlDevice",
        "params": {
            "command": "connect",
            "headset": "INSIGHT-A2D2043D"
        }
    }))

    #print(ws.recv())
    ws.recv()
    time.sleep(1)
    # print(ws.recv())

    ws.send(json.dumps({
        "id": 1,
        "jsonrpc": "2.0",
        "method": "authorize",
        "params": {
            "clientId": client_id,
            "clientSecret": client_secret
        }
    }))

    odp = ws.recv()
    #print(odp)
    result_dic = json.loads(odp)
    token = result_dic['result']['cortexToken']

    ws.send(json.dumps({
        "jsonrpc": "2.0",
        "method": "createSession",
        "params": {
            "cortexToken": token,
            "headset": "INSIGHT-A2D2043D",
            "status": "active"
        },
        "id": 1
    }))

    odp = ws.recv()
    #print(odp)
    result_dic = json.loads(odp)
    session_id = result_dic['result']['id']
    return [ws, token, session_id]


def subscribe(ws, token, session_id, data):
    ws.send(json.dumps({
        "jsonrpc": "2.0",
        "method": "subscribe",
        "params": {
            "cortexToken": token,
            "session": session_id,
            "streams": [
                data
            ]
        },
        "id": 2
    }))
    print(ws.recv())


def unsubscribe(ws, token, session_id, data):
    ws.send(json.dumps({
        "jsonrpc": "2.0",
        "method": "unsubscribe",
        "params": {
            "cortexToken": token,
            "session": session_id,
            "streams": [
                data
            ]
        },
        "id": 2
    }))
    print(ws.recv())


def bands_calculate(widmo_amp, band, i):
    band[i * 5 + 0] = widmo_amp[0] + widmo_amp[1] + widmo_amp[2] + widmo_amp[3] + widmo_amp[4]  # 4-8Hz Theta
    band[i * 5 + 1] = widmo_amp[4] + widmo_amp[5] + widmo_amp[6] + widmo_amp[7] + widmo_amp[8]  # 8-12Hz Alpha
    band[i * 5 + 2] = widmo_amp[8] + widmo_amp[9] + widmo_amp[10] + widmo_amp[11] + widmo_amp[12]  # 12-16Hz BetaL
    band[i * 5 + 3] = widmo_amp[12] + widmo_amp[13] + widmo_amp[14] + widmo_amp[15] + widmo_amp[16] + widmo_amp[17] + \
                        widmo_amp[18] + widmo_amp[19] + widmo_amp[20] + widmo_amp[21]  # 16-25Hz BetaH
    band[i * 5 + 4] = widmo_amp[21] + widmo_amp[22] + widmo_amp[23] + widmo_amp[24] + widmo_amp[25] + widmo_amp[26] + \
                        widmo_amp[27] + widmo_amp[28] + widmo_amp[29] + widmo_amp[30] + widmo_amp[31] + widmo_amp[32] + \
                        widmo_amp[33] + widmo_amp[34] + widmo_amp[35] + widmo_amp[36] + widmo_amp[37] + widmo_amp[38] + \
                        widmo_amp[39] + widmo_amp[40] + widmo_amp[41]  # 25-45Hz Gamma
    band[i * 5 + 0] /= 5
    band[i * 5 + 1] /= 5
    band[i * 5 + 2] /= 5
    band[i * 5 + 3] /= 10
    band[i * 5 + 4] /= 21
    return band


def klasa2ruch(klasy, decyzja):
    if decyzja == int(klasy[0]):
        url_get = "http://192.168.88.124:5000/"
        res = requests.get(url_get)
        return "stop"
    elif decyzja == int(klasy[1]):
        url_get = "http://192.168.88.124:5000/pivot_left"
        res = requests.get(url_get)
        return "lewo"
    elif decyzja == int(klasy[2]):
        url_get = "http://192.168.88.124:5000/forward"
        res = requests.get(url_get)
        return "naprzód"
    elif decyzja == int(klasy[3]):
        url_get = "http://192.168.88.124:5000/pivot_right"
        res = requests.get(url_get)
        return "prawo"
    else:
        return "!!!!!!!!Błąd!!!!!!!!"


WS, Token, Session_id = connect()
menu()
option = int(input('Wybierz opcję: '))

while option != 0:
    if option == 1:
        while True:
            print('\nSterowanie Live\n')
            #if os.getcwd()=="C:\\Users\\Toshiba\\Desktop\\inz":
            os.chdir("C:\\Users\\Toshiba\\Desktop\\inz\\modele")
            #print(os.getcwd())
            print('Lista modeli:')
            l = list(os.listdir())
            print(l)
            option = input('Wybierz model (0 = Wyjście): ')
            while option not in l and option != '0':
                print("Nie ma takiego modelu\n")
                print('Lista modeli:')
                print(l)
                option = input('\nWybierz model (0 = Wyjście): ')
            if option == '0':
                break
            model = joblib.load(option)
            klasy = model.classes_
            print ('Ten model posiada następujące klasy:')
            print(klasy)
            print ("\nPrzyporządkuj klasy do komend sterujących. \nPodaj klasy w kolejności: brak ruchu, obrót w lewo,"
                   " jazda naprzód, obrót w prawo")
            option = input('Twoja kolejność (Enter = domyślna): ')

            if len(option)>0:
                option = option.split(' ')
                print(option)
                bad_data=True
                while bad_data:
                    przerwanie = False
                    for elem in option:
                        if int(elem) not in klasy:
                            print("Podane klasy nie należą do modelu!")
                            przerwanie = True
                            break
                    if przerwanie==True:
                        bad_data = True
                        print(klasy)
                        option = input('Twoja kolejność: ')
                    else:
                        bad_data=False
                klasy=option
            print(klasy)
            cechy()
            option = int(input('Wybierz cechy: '))
            while option != 0:
                if option == 1:
                    subscribe(WS, Token, Session_id, "eeg")
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    counter = 0
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["eeg"][2:7]
                            array = np.array(dane_new).reshape(1, -1)
                            dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            # print(dane)
                            dane_all = dane_all.append(dane)
                            # print(dane_all)
                            counter += 1
                            if counter >= 32 and len(dane_all.index) >= 128:
                                # print(dane_all)
                                counter = 0
                                thought = model.predict(dane_all)
                                # print(thought)
                                counts = np.bincount(thought)
                                print(counts)
                                decyzja = np.argmax(counts)
                                ruch = klasa2ruch(klasy, decyzja)
                                print(decyzja)
                                print(ruch)
                                dane_all = dane_all.iloc[32:]
                    except KeyboardInterrupt:
                        #unsubscribe(WS, Token, Session_id, "eeg")
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                    except:
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        e = sys.exc_info()[0]
                        print(e)

                elif option == 2:
                    subscribe(WS, Token, Session_id, "pow")
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["pow"]
                            # print(dane_new)
                            array = np.array(dane_new).reshape(1, -1)
                            decyzja = model.predict(array)
                            ruch = klasa2ruch(klasy, decyzja)
                            print(decyzja)
                            print(ruch)
                    except KeyboardInterrupt:
                        #unsubscribe(WS, Token, Session_id, "pow")
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                    except:
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        e = sys.exc_info()[0]
                        print(e)
                elif option == 4:
                    subscribe(WS, Token, Session_id, "eeg")
                    elektrody = ["EEG.AF3", "EEG.T7", "EEG.Pz", "EEG.T8", "EEG.AF4"]
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    counter = 0
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["eeg"][2:7]
                            array = np.array(dane_new).reshape(1, -1)
                            dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            dane_all = dane_all.append(dane)
                            counter += 1
                            if counter >= 32 and len(dane_all.index) >= 128:
                                counter = 0
                                fft_1s = [0] * 210
                                dane_1s = dane_all.copy()
                                dane_1s -= dane_1s.mean()
                                for i in range(5):
                                    widmo_amp = np.abs(np.fft.rfft(dane_1s[elektrody[i]]))[4:46] / 64
                                    for j in range(42):
                                        fft_1s[i * 42 + j] = widmo_amp[j]
                                fft_1s = np.array(fft_1s).reshape(1, -1)
                                decyzja = model.predict(pd.DataFrame(fft_1s))
                                ruch = klasa2ruch(klasy, decyzja)
                                print(decyzja)
                                print(ruch)
                                dane_all = dane_all.iloc[32:]
                    except KeyboardInterrupt:
                        # unsubscribe(WS, Token, Session_id, "eeg")
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                    except:
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        e = sys.exc_info()[0]
                        print(e)
                elif option == 3:
                    subscribe(WS, Token, Session_id, "eeg")
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    counter = 0
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["eeg"][2:7]
                            array = np.array(dane_new).reshape(1, -1)
                            dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            dane_all = dane_all.append(dane)
                            counter += 1
                            if counter >= 32 and len(dane_all.index) >= 128:
                                counter = 0
                                s2 = np.var(dane_all, ddof=1)
                                decyzja = model.predict(pd.DataFrame(np.sqrt(s2)).T)
                                ruch = klasa2ruch(klasy, decyzja)
                                print(decyzja)
                                print(ruch)
                                dane_all = dane_all.iloc[32:]
                    except KeyboardInterrupt:
                        # unsubscribe(WS, Token, Session_id, "eeg")
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                    except:
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        e = sys.exc_info()[0]
                        print(e)
                elif option == 5:
                    subscribe(WS, Token, Session_id, "eeg")
                    elektrody = ["EEG.AF3", "EEG.T7", "EEG.Pz", "EEG.T8", "EEG.AF4"]
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    counter = 0
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["eeg"][2:7]
                            array = np.array(dane_new).reshape(1, -1)
                            dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            dane_all = dane_all.append(dane)
                            counter += 1
                            if counter >= 32 and len(dane_all.index) >= 128:
                                counter = 0
                                dane_1s = dane_all.copy()
                                dane_1s -= dane_1s.mean()
                                band1s = [0] * 25
                                for i in range(5):
                                    widmoAmp = np.abs(np.fft.rfft(dane_1s[elektrody[i]]))[4:46] / 64
                                    band1s = bands_calculate(widmoAmp,band1s,i)
                                band1s = np.array(band1s).reshape(1, -1)
                                decyzja = model.predict(pd.DataFrame(band1s))
                                ruch = klasa2ruch(klasy, decyzja)
                                print(decyzja)
                                print(ruch)
                                dane_all = dane_all.iloc[32:]
                    except KeyboardInterrupt:
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                    except:
                        url_get = "http://192.168.88.124:5000/"
                        res = requests.get(url_get)
                        e = sys.exc_info()[0]
                        print(e)
                else:
                    print("Błąd! Nie ma takiej opcji")
                cechy()
                option = int(input('Wybierz cechy: '))

    elif option == 2:
        while True:
            print('\nTrening modelu\n')
            klasyfikatory = {'tree': DecisionTreeClassifier(), 'forest': RandomForestClassifier(random_state=42),
                             'sgd': SGDClassifier(random_state=42), 'knn': KNeighborsClassifier(),
                             'svm_lin': Pipeline([("scaler", StandardScaler()), ("linear_svc", LinearSVC(C=1, loss="hinge"))]),
                             'svm_pol': Pipeline([("scaler", StandardScaler()), ("svm_clf", SVC(kernel="poly", degree=3, coef0=1, C=5))]),
                             'svm_rbf': Pipeline([("scaler", StandardScaler()), ("svm_clf", SVC(kernel="rbf", gamma=5, C=1000))]),
                             'bayes': GaussianNB(), 'lda': LinearDiscriminantAnalysis(),
                             'qda': QuadraticDiscriminantAnalysis(), 'mlp': MLPClassifier(random_state=1, max_iter=300)
                             }
            cecha = ["np", "pow", "var", "fft", "band"]
            print('Lista klasyfikatorów:')
            print(klasyfikatory.keys())
            option = input('Wybierz klasyfikator (0 = Wyjście): ')
            while option not in klasyfikatory.keys() and option != '0':
                print("Nie ma takiego klasyfikatora\n")
                print('Lista klasyfikatorów:')
                print(klasyfikatory.keys())
                option = input('Wybierz model (0 = Wyjście): ')
            if option == '0':
                break
            model = klasyfikatory[option]
            nazwa = option
            cechy()
            option = int(input('Wybierz cechy: '))
            while option != 0:
                if option == 1:
                    try:
                        dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4', 'etykieta'])
                        for i in range(4):
                            print('Nauka klasy: ' + str(i))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            subscribe(WS, Token, Session_id, "eeg")
                            dane_class = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            for j in range(2560):
                                dane_new = json.loads(WS.recv())["eeg"][2:7]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                                dane_class = dane_class.append(dane)
                            dane_class['etykieta'] = i
                            dane_all = dane_all.append(dane_class)
                            print('Pozytywnie zakończono naukę klasy: '+str(i))
                            WS.close()
                            WS, Token, Session_id = connect()
                        model.fit(dane_all.drop('etykieta', axis=1), dane_all['etykieta'])
                        joblib.dump(model, "C:\\Users\\Toshiba\\Desktop\\inz\\modele\\new_"+nazwa+"_"+cecha[option-1])
                        break

                    except KeyboardInterrupt:
                        # unsubscribe(WS, Token, Session_id, "eeg")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 2:
                    try:
                        dane_all = pd.DataFrame(columns=['POW.AF3.Theta','POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma', 'POW.T7.Theta','POW.T7.Alpha', 'POW.T7.BetaL', 'POW.T7.BetaH', 'POW.T7.Gamma','POW.Pz.Theta','POW.Pz.Alpha', 'POW.Pz.BetaL', 'POW.Pz.BetaH', 'POW.Pz.Gamma','POW.T8.Theta','POW.T8.Alpha', 'POW.T8.BetaL', 'POW.T8.BetaH', 'POW.T8.Gamma','POW.AF4.Theta','POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma','etykieta'])
                        for i in range(4):
                            print('Nauka klasy: ' + str(i))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            subscribe(WS, Token, Session_id, "pow")
                            dane_class = pd.DataFrame(columns=['POW.AF3.Theta','POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma', 'POW.T7.Theta','POW.T7.Alpha', 'POW.T7.BetaL', 'POW.T7.BetaH', 'POW.T7.Gamma','POW.Pz.Theta','POW.Pz.Alpha', 'POW.Pz.BetaL', 'POW.Pz.BetaH', 'POW.Pz.Gamma','POW.T8.Theta','POW.T8.Alpha', 'POW.T8.BetaL', 'POW.T8.BetaH', 'POW.T8.Gamma','POW.AF4.Theta','POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma'])
                            for j in range(160):
                                dane_new = json.loads(WS.recv())["pow"]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['POW.AF3.Theta','POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma', 'POW.T7.Theta','POW.T7.Alpha', 'POW.T7.BetaL', 'POW.T7.BetaH', 'POW.T7.Gamma','POW.Pz.Theta','POW.Pz.Alpha', 'POW.Pz.BetaL', 'POW.Pz.BetaH', 'POW.Pz.Gamma','POW.T8.Theta','POW.T8.Alpha', 'POW.T8.BetaL', 'POW.T8.BetaH', 'POW.T8.Gamma','POW.AF4.Theta','POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma'])
                                dane_class = dane_class.append(dane)
                            dane_class['etykieta'] = i
                            print(dane_class)
                            dane_all = dane_all.append(dane_class)
                            print('Pozytywnie zakończono naukę klasy: ' + str(i))
                            WS.close()
                            WS, Token, Session_id = connect()
                        print(dane_all)
                        model.fit(dane_all.drop('etykieta', axis=1), dane_all['etykieta'].astype(np.uint8))
                        joblib.dump(model, "C:\\Users\\Toshiba\\Desktop\\inz\\modele\\new_" + nazwa+"_"+cecha[option-1])
                        break
                    except KeyboardInterrupt:
                        # unsubscribe(WS, Token, Session_id, "pow")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 4:
                    elektrody = ["EEG.AF3", "EEG.T7", "EEG.Pz", "EEG.T8", "EEG.AF4"]
                    nazwy_kolumn = pd.read_csv("C:\\Users\\Toshiba\\Desktop\\ML\\pom2311_1_fft\\0.csv")
                    nazwy_kolumn = nazwy_kolumn.columns
                    nazwy_kolumn = np.delete(np.array(nazwy_kolumn), 0)
                    try:
                        fft_all = pd.DataFrame(columns=np.append(nazwy_kolumn, 'etykieta'))#.drop("Unnamed: 0",axis=1)
                        for i in range(4):
                            print('Nauka klasy: ' + str(i))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            counter = 0
                            subscribe(WS, Token, Session_id, "eeg")
                            dane_class = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            fft_class = pd.DataFrame(columns=nazwy_kolumn)#.drop("Unnamed: 0", axis=1)
                            for j in range(2560):
                                dane_new = json.loads(WS.recv())["eeg"][2:7]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                                dane_class = dane_class.append(dane)
                                counter += 1
                                if counter >= 32 and len(dane_class.index) >= 128:
                                    counter = 0
                                    fft_1s = [0] * 210
                                    dane_1s = dane_class.copy()
                                    dane_1s -= dane_1s.mean()
                                    for k1 in range(5):
                                        widmo_amp = np.abs(np.fft.rfft(dane_1s[elektrody[k1]]))[4:46] / 64
                                        for k2 in range(42):
                                            fft_1s[k1 * 42 + k2] = widmo_amp[k2]
                                    fft_1s = np.array(fft_1s).reshape(1, -1)
                                   # print(fft_1s)
                                   # print(fft_class)
                                    fft_df = pd.DataFrame(fft_1s, columns=nazwy_kolumn)
                                   # print(fft_df)
                                    fft_class = fft_class.append(fft_df)
                                    #print(fft_class)
                                    dane_class = dane_class.iloc[32:]
                            fft_class['etykieta'] = i
                            #print(fft_class)
                            #print(fft_all)
                            fft_all = fft_all.append(fft_class)
                            print('Pozytywnie zakończono naukę klasy: ' + str(i))
                            WS.close()
                            WS, Token, Session_id = connect()
                        #print(fft_all)
                        model.fit(fft_all.drop('etykieta', axis=1), fft_all['etykieta'].astype(np.uint8))
                        joblib.dump(model,
                                    "C:\\Users\\Toshiba\\Desktop\\inz\\modele\\new_" + nazwa + "_" + cecha[option-1])
                        break

                    except KeyboardInterrupt:
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 3:
                    try:
                        wariancja = pd.DataFrame(
                            columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4', 'etykieta'])
                        for i in range(4):
                            print('Nauka klasy: ' + str(i))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            counter = 0
                            subscribe(WS, Token, Session_id, "eeg")
                            dane_class = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            wariancja_class = pd.DataFrame(
                                columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            for j in range(2560):
                                dane_new = json.loads(WS.recv())["eeg"][2:7]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                                dane_class = dane_class.append(dane)
                                counter += 1
                                if counter >= 32 and len(dane_class.index) >= 128:
                                    counter = 0
                                    s2 = np.var(dane_class, ddof=1)
                                    wariancja_class = wariancja_class.append(pd.DataFrame(np.sqrt(s2)).T)
                                    wariancja_class['etykieta'] = i
                                    dane_class = dane_class.iloc[32:]
                            wariancja=wariancja.append(wariancja_class)
                            print('Pozytywnie zakończono naukę klasy: ' + str(i))
                            WS.close()
                            WS, Token, Session_id = connect()
                        model.fit(wariancja.drop('etykieta', axis=1), wariancja['etykieta'].astype(np.uint8))
                        joblib.dump(model,
                                    "C:\\Users\\Toshiba\\Desktop\\inz\\modele\\new_" + nazwa + "_" + cecha[option-1])
                        break

                    except KeyboardInterrupt:
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 5:
                    nazwy_kolumn = ['EEG.AF3/Theta', 'EEG.AF3/Alpha', 'EEG.AF3/BetaL', 'EEG.AF3/BetaH', 'EEG.AF3/Gamma',
                     'EEG.T7/Theta', 'EEG.T7/Alpha', 'EEG.T7/BetaL', 'EEG.T7/BetaH', 'EEG.T7/Gamma', 'EEG.Pz/Theta',
                     'EEG.Pz/Alpha', 'EEG.Pz/BetaL', 'EEG.Pz/BetaH', 'EEG.Pz/Gamma', 'EEG.T8/Theta', 'EEG.T8/Alpha',
                     'EEG.T8/BetaL', 'EEG.T8/BetaH', 'EEG.T8/Gamma', 'EEG.AF4/Theta', 'EEG.AF4/Alpha', 'EEG.AF4/BetaL',
                     'EEG.AF4/BetaH', 'EEG.AF4/Gamma']
                    elektrody = ["EEG.AF3", "EEG.T7", "EEG.Pz", "EEG.T8", "EEG.AF4"]
                    try:
                        band_all = pd.DataFrame(columns=nazwy_kolumn)
                        band_all['etykieta'] = 0
                        #print(band_all)
                        for iter1 in range(4):
                            print('Nauka klasy: ' + str(iter1))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            counter = 0
                            subscribe(WS, Token, Session_id, "eeg")
                            band_class = pd.DataFrame(columns=nazwy_kolumn)
                            dane_class = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            for iter2 in range(2560):
                                dane_new = json.loads(WS.recv())["eeg"][2:7]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                                dane_class = dane_class.append(dane)
                                counter += 1
                                if counter >= 32 and len(dane_class.index) >= 128:
                                    counter = 0
                                    dane_1s = dane_class.copy()
                                    dane_1s -= dane_1s.mean()
                                    band1s = [0] * 25
                                    for i in range(5):
                                        widmoAmp = np.abs(np.fft.rfft(dane_1s[elektrody[i]]))[4:46] / 64
                                        #print(widmoAmp)
                                        band1s = bands_calculate(widmoAmp, band1s, i)
                                        #print(band1s)
                                    band1s = np.array(band1s).reshape(1, -1)
                                    band_class = band_class.append(pd.DataFrame(band1s,columns=nazwy_kolumn))
                                    dane_class = dane_class.iloc[32:]
                            band_class['etykieta'] = iter1
                            band_all = band_all.append(band_class)
                            #print(band_all)
                            print('Pozytywnie zakończono naukę klasy: ' + str(iter1))
                            WS.close()
                            WS, Token, Session_id = connect()
                        model.fit(band_all.drop('etykieta', axis=1), band_all['etykieta'].astype(np.uint8))
                        joblib.dump(model,
                                    "C:\\Users\\Toshiba\\Desktop\\inz\\modele\\new_" + nazwa + "_" + cecha[option-1])
                        break

                    except KeyboardInterrupt:
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                else:
                    print("Błąd! Nie ma takiej opcji")
                cechy()
                option = int(input('Wybierz cechy: '))
    elif option == 3:
        while True:
            print('\nTest modelu\n')
            os.chdir("C:\\Users\\Toshiba\\Desktop\\inz\\modele")
            print('Lista modeli:')
            l = list(os.listdir())
            print(l)
            option = input('Wybierz model (0 = Wyjście): ')
            while option not in l and option != '0':
                print("Nie ma takiego modelu\n")
                print('Lista modeli:')
                print(l)
                option = input('\nWybierz model (0 = Wyjście): ')
            if option == '0':
                break
            model = joblib.load(option)
            klasy = model.classes_
            cechy()
            option = int(input('Wybierz cechy: '))
            while option != 0:
                if option == 1:
                    try:
                        stats = [0]*5
                        for i in range(4):
                            print('Test klasy: '+str(klasy[i]))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            subscribe(WS, Token, Session_id, "eeg")
                            dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            counter = 0
                            good = 0
                            all = 0
                            for j in range(1280):
                                dane_new = json.loads(WS.recv())["eeg"][2:7]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                                dane_all = dane_all.append(dane)
                                counter += 1
                                if counter >= 32 and len(dane_all.index) >= 128:
                                    counter = 0
                                    thought = model.predict(dane_all)
                                    counts = np.bincount(thought)
                                    print(counts)
                                    decyzja = np.argmax(counts)
                                    if decyzja == klasy[i]:
                                        good += 1
                                    all += 1
                                    print(decyzja)
                                    dane_all = dane_all.iloc[32:]
                            stats[i] = good / all
                            print('Wynik dla komendy ' + str(i) + ':  ' + str(100 * stats[i]) + '%')
                            WS.close()
                            WS, Token, Session_id = connect()
                        stats[4] = (stats[0]+stats[1]+stats[2]+stats[3])/4
                        print('Wynik ogólny:  ' + str(100 * stats[4]) + '%')
                        time.sleep(2)
                        break

                    except KeyboardInterrupt:
                        #unsubscribe(WS, Token, Session_id, "eeg")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 2:
                    try:
                        stats = [0] * 5
                        for i in range(4):
                            print('Test klasy: ' + str(klasy[i]))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            subscribe(WS, Token, Session_id, "pow")
                            good = 0
                            all = 0
                            for j in range(80):
                                dane_new = json.loads(WS.recv())["pow"]
                                # print(dane_new)
                                array = np.array(dane_new).reshape(1, -1)
                                decyzja = model.predict(array)
                                if decyzja == klasy[i]:
                                    good += 1
                                all += 1
                                print(decyzja)
                            stats[i] = good / all
                            print('Wynik dla komendy ' + str(i) + ':  ' + str(100 * stats[i]) + '%')
                            WS.close()
                            WS, Token, Session_id = connect()
                        stats[4] = (stats[0] + stats[1] + stats[2] + stats[3]) / 4
                        print('Wynik ogólny:  ' + str(100 * stats[4]) + '%')
                        time.sleep(2)
                        break
                    except KeyboardInterrupt:
                        #unsubscribe(WS, Token, Session_id, "pow")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 4:
                    elektrody = ["EEG.AF3", "EEG.T7", "EEG.Pz", "EEG.T8", "EEG.AF4"]
                    try:
                        stats = [0] * 5
                        for iter1 in range(4):
                            print('Test klasy: ' + str(klasy[iter1]))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            subscribe(WS, Token, Session_id, "eeg")
                            dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            counter = 0
                            good = 0
                            all = 0
                            for iter2 in range(1280):
                                dane_new = json.loads(WS.recv())["eeg"][2:7]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                                dane_all = dane_all.append(dane)
                                counter += 1
                                if counter >= 32 and len(dane_all.index) >= 128:
                                    counter = 0
                                    fft_1s = [0] * 210
                                    dane_1s = dane_all.copy()
                                    dane_1s -= dane_1s.mean()
                                    for i in range(5):
                                        widmo_amp = np.abs(np.fft.rfft(dane_1s[elektrody[i]]))[4:46] / 64
                                        for j in range(42):
                                            fft_1s[i * 42 + j] = widmo_amp[j]
                                    fft_1s = np.array(fft_1s).reshape(1, -1)
                                    decyzja = model.predict(pd.DataFrame(fft_1s))
                                    if decyzja == klasy[iter1]:
                                        good += 1
                                    all += 1
                                    print(decyzja)
                                    dane_all = dane_all.iloc[32:]
                            stats[iter1] = good / all
                            print('Wynik dla komendy ' + str(iter1) + ':  ' + str(100 * stats[iter1]) + '%')
                            WS.close()
                            WS, Token, Session_id = connect()
                        stats[4] = (stats[0] + stats[1] + stats[2] + stats[3]) / 4
                        print('Wynik ogólny:  ' + str(100 * stats[4]) + '%')
                        time.sleep(2)
                        break

                    except KeyboardInterrupt:
                        # unsubscribe(WS, Token, Session_id, "eeg")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 3:
                    try:
                        stats = [0] * 5
                        for i in range(4):
                            print('Test klasy: ' + str(klasy[i]))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            subscribe(WS, Token, Session_id, "eeg")
                            dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            counter = 0
                            good = 0
                            all = 0
                            for j in range(1280):
                                dane_new = json.loads(WS.recv())["eeg"][2:7]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                                dane_all = dane_all.append(dane)
                                counter += 1
                                if counter >= 32 and len(dane_all.index) >= 128:
                                    counter = 0
                                    s2 = np.var(dane_all, ddof=1)
                                    decyzja = model.predict(pd.DataFrame(np.sqrt(s2)).T)
                                    if decyzja == klasy[i]:
                                        good += 1
                                    all += 1
                                    print(decyzja)
                                    dane_all = dane_all.iloc[32:]
                            stats[i] = good / all
                            print('Wynik dla komendy ' + str(i) + ':  ' + str(100 * stats[i]) + '%')
                            WS.close()
                            WS, Token, Session_id = connect()
                        stats[4] = (stats[0] + stats[1] + stats[2] + stats[3]) / 4
                        print('Wynik ogólny:  ' + str(100 * stats[4]) + '%')
                        time.sleep(2)
                        break

                    except KeyboardInterrupt:
                        # unsubscribe(WS, Token, Session_id, "eeg")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 5:
                    elektrody = ["EEG.AF3", "EEG.T7", "EEG.Pz", "EEG.T8", "EEG.AF4"]
                    try:
                        stats = [0] * 5
                        for iter1 in range(4):
                            print('Test klasy: ' + str(klasy[iter1]))
                            print('Odliczanie: 3s')
                            time.sleep(1)
                            print('Odliczanie: 2s')
                            time.sleep(1)
                            print('Odliczanie: 1s')
                            time.sleep(1)
                            print('Start')
                            subscribe(WS, Token, Session_id, "eeg")
                            dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            counter = 0
                            good = 0
                            all = 0
                            for iter2 in range(1280):
                                dane_new = json.loads(WS.recv())["eeg"][2:7]
                                array = np.array(dane_new).reshape(1, -1)
                                dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                                dane_all = dane_all.append(dane)
                                counter += 1
                                if counter >= 32 and len(dane_all.index) >= 128:
                                    counter = 0
                                    dane_1s = dane_all.copy()
                                    dane_1s -= dane_1s.mean()
                                    band1s = [0] * 25
                                    for i in range(5):
                                        widmoAmp = np.abs(np.fft.rfft(dane_1s[elektrody[i]]))[4:46] / 64
                                        band1s = bands_calculate(widmoAmp, band1s, i)
                                    band1s = np.array(band1s).reshape(1, -1)
                                    decyzja = model.predict(pd.DataFrame(band1s))
                                    if decyzja == klasy[iter1]:
                                        good += 1
                                    all += 1
                                    print(decyzja)
                                    dane_all = dane_all.iloc[32:]
                            stats[iter1] = good / all
                            print('Wynik dla komendy ' + str(iter1) + ':  ' + str(100 * stats[iter1]) + '%')
                            WS.close()
                            WS, Token, Session_id = connect()
                        stats[4] = (stats[0] + stats[1] + stats[2] + stats[3]) / 4
                        print('Wynik ogólny:  ' + str(100 * stats[4]) + '%')
                        time.sleep(2)
                        break

                    except KeyboardInterrupt:
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                else:
                    print("Błąd! Nie ma takiej opcji")
                cechy()
                option = int(input('Wybierz cechy: '))
    elif option == 4:
        while True:
            print('\nKlasyfikacja Live (bez wysyłania komend)')
            #if os.getcwd()=="C:\\Users\\Toshiba\\Desktop\\inz":
            os.chdir("C:\\Users\\Toshiba\\Desktop\\inz\\modele")
            #print(os.getcwd())
            print('Lista modeli:')
            l = list(os.listdir())
            print(l)
            option = input('Wybierz model (0 = Wyjście): ')
            while option not in l and option != '0':
                print("Nie ma takiego modelu\n")
                print('Lista modeli:')
                print(l)
                option = input('\nWybierz model (0 = Wyjście): ')
            if option == '0':
                break
            model = joblib.load(option)
            cechy()
            option = int(input('Wybierz cechy: '))
            while option != 0:
                if option == 1:
                    subscribe(WS, Token, Session_id, "eeg")
                    #time.sleep(1)
                    #print(WS.recv())
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    counter = 0
                    try:
                        while True:
                            #json.loads(WS.recv())

                            dane_new = json.loads(WS.recv())["eeg"][2:7]
                            # print(dane_new)
                            array = np.array(dane_new).reshape(1, -1)
                            dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            # print(dane)
                            dane_all = dane_all.append(dane)  # np.append(dane_all, dane_new, axis=1)
                            # print(dane_all)
                            counter += 1
                            if counter >= 32 and len(dane_all.index) >= 128:
                                # print(dane_all)
                                counter = 0
                                thought = model.predict(dane_all)
                                # print(thought)
                                counts = np.bincount(thought)
                                print(counts)
                                decyzja = np.argmax(counts)
                                if decyzja == 3 and counts[3] < 100:
                                    decyzja = 0
                                print(decyzja)
                                dane_all = dane_all.iloc[32:]
                    except KeyboardInterrupt:
                        #unsubscribe(WS, Token, Session_id, "eeg")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 2:
                    subscribe(WS, Token, Session_id, "pow")
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["pow"]
                            # print(dane_new)
                            array = np.array(dane_new).reshape(1, -1)
                            thought = model.predict(array)
                            print(thought)
                    except KeyboardInterrupt:
                        #unsubscribe(WS, Token, Session_id, "pow")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 4:
                    subscribe(WS, Token, Session_id, "eeg")
                    elektrody = ["EEG.AF3", "EEG.T7", "EEG.Pz", "EEG.T8", "EEG.AF4"]
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    counter = 0
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["eeg"][2:7]
                            array = np.array(dane_new).reshape(1, -1)
                            dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            dane_all = dane_all.append(dane)
                            counter += 1
                            if counter >= 32 and len(dane_all.index) >= 128:
                                counter = 0
                                fft_1s = [0] * 210
                                dane_1s = dane_all.copy()
                                dane_1s -= dane_1s.mean()
                                for i in range(5):
                                    widmo_amp = np.abs(np.fft.rfft(dane_1s[elektrody[i]]))[4:46] / 64
                                    for j in range(42):
                                        fft_1s[i * 42 + j] = widmo_amp[j]
                                fft_1s = np.array(fft_1s).reshape(1, -1)
                                thought = model.predict(pd.DataFrame(fft_1s))
                                print(thought)
                                dane_all = dane_all.iloc[32:]
                    except KeyboardInterrupt:
                        # unsubscribe(WS, Token, Session_id, "eeg")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 3:
                    subscribe(WS, Token, Session_id, "eeg")
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    counter = 0
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["eeg"][2:7]
                            array = np.array(dane_new).reshape(1, -1)
                            dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            dane_all = dane_all.append(dane)
                            counter += 1
                            if counter >= 32 and len(dane_all.index) >= 128:
                                counter = 0
                                s2 = np.var(dane_all, ddof=1)
                                thought = model.predict(pd.DataFrame(np.sqrt(s2)).T)
                                print(thought)
                                dane_all = dane_all.iloc[32:]
                    except KeyboardInterrupt:
                        # unsubscribe(WS, Token, Session_id, "eeg")
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                elif option == 5:
                    subscribe(WS, Token, Session_id, "eeg")
                    elektrody = ["EEG.AF3", "EEG.T7", "EEG.Pz", "EEG.T8", "EEG.AF4"]
                    dane_all = pd.DataFrame(columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                    counter = 0
                    try:
                        while True:
                            dane_new = json.loads(WS.recv())["eeg"][2:7]
                            array = np.array(dane_new).reshape(1, -1)
                            dane = pd.DataFrame(array, columns=['EEG.AF3', 'EEG.T7', 'EEG.Pz', 'EEG.T8', 'EEG.AF4'])
                            dane_all = dane_all.append(dane)
                            counter += 1
                            if counter >= 32 and len(dane_all.index) >= 128:
                                counter = 0
                                dane_1s = dane_all.copy()
                                dane_1s -= dane_1s.mean()
                                band1s = [0] * 25
                                for i in range(5):
                                    widmoAmp = np.abs(np.fft.rfft(dane_1s[elektrody[i]]))[4:46] / 64
                                    band1s = bands_calculate(widmoAmp,band1s,i)
                                band1s = np.array(band1s).reshape(1, -1)
                                decyzja = model.predict(pd.DataFrame(band1s))
                                print(decyzja)
                                dane_all = dane_all.iloc[32:]
                    except KeyboardInterrupt:
                        WS.close()
                        WS, Token, Session_id = connect()
                        break
                else:
                    print("Błąd! Nie ma takiej opcji")
                cechy()
                option = int(input('Wybierz cechy: '))


    else:
        print("Błąd! Nie ma takiej opcji")
    menu()
    option = int(input('Wybierz opcję: '))


