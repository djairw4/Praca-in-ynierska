# Importowanie potrzebnych pakietow i bibliotek
from flask import Flask
import RPi.GPIO as gpio

#Utworzenie instancji aplikacji Flask
app = Flask(__name__)

#Funkcja inicjalizujaca piny RPi
def init():   
    gpio.setmode(gpio.BOARD)
    gpio.setup(7,gpio.OUT)
    gpio.setup(11,gpio.OUT)
    gpio.setup(13,gpio.OUT)
    gpio.setup(15,gpio.OUT)
    gpio.setup(33,gpio.OUT)
    gpio.setup(35,gpio.OUT)
    motor1=gpio.PWM(33, 1000)
    motor2=gpio.PWM(35, 1000)
    motor1.start(50)
    motor2.start(50)
    

# Jazda do przodu
@app.route('/forward')
def forward():
    gpio.output(7,False)
    gpio.output(11,True)
    gpio.output(13,True)
    gpio.output(15,False)
    return 'forward'


# Obrot w lewo
@app.route('/pivot_left')
def pivot_left():
    gpio.output(7,True)
    gpio.output(11,False)
    gpio.output(13,True)
    gpio.output(15,False)
    return 'left'


# Obrot w prawo
@app.route('/pivot_right')
def pivot_right():
    gpio.output(7,False)
    gpio.output(11,True)
    gpio.output(13,False)
    gpio.output(15,True)
    return 'right'


# Brak sterowania
@app.route('/')
def neutral():
    return 'neutral'



init()

if __name__ == '__main__':
	app.run(debug=True,host='192.168.88.124')