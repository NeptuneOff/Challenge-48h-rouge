from machine import ADC, Pin
from time import sleep
import network
import espnow

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()

e = espnow.ESPNow()
e.active(True)
# Adresse MAC de la base roulante
peer = b'\xFC\xE8\xC0\x7D\x90\xF0'
e.add_peer(peer)


class Joystick:
    def __init__(self, pin_x, pin_y):
        self.x = ADC(Pin(pin_x))
        self.y = ADC(Pin(pin_y))
        self.x.atten(ADC.ATTN_11DB)
        self.y.atten(ADC.ATTN_11DB)

    def read(self):
        return self.x.read(), self.y.read()

def get_direction(x, y):
    dir_x = "neutre"
    dir_y = "neutre"

    if x > 3000:
        dir_x = "droite"
    elif x < 200:
        dir_x = "gauche"

    if y > 3000:
        dir_y = "arriere"
    elif y < 300:
        dir_y = "avant"

    return dir_y, dir_x 

# Joystick
joystick = Joystick(pin_x=1, pin_y=2)
button = Pin(3, Pin.IN, Pin.PULL_UP)
etat_btn_precedent = button.value()

# Bouton autonome
# button = Pin(22, Pin.IN, Pin.PULL_UP)
last_button_state = 1
autonome_mode = False

last_command = None

while True:
    # Gestion du bouton toggle autonome
    current_button_state = button.value()
    if last_button_state == 1 and current_button_state == 0:
        autonome_mode = not autonome_mode
        mode = "autonome" if autonome_mode else "manuel"
        e.send(peer, mode.encode())
        print(f"Commande envoyée : {mode}")
    last_button_state = current_button_state

    # Si en mode autonome → ignorer le joystick
    if autonome_mode:
        sleep(0.2)
        continue

    # Lecture du joystick
    x, y = joystick.read()
    dir1, dir2 = get_direction(x, y)

    if dir1 == "neutre" and dir2 == "neutre":
        command = "stop"
    elif dir1 != "neutre" and dir2 == "neutre":
        command = dir1
    elif dir1 == "neutre" and dir2 != "neutre":
        command = dir2
    else:
        command = dir1 + "_" + dir2

    if command != last_command:
        e.send(peer, command.encode())
        print(f"Commande envoyée : {command}")
        last_command = command
    sleep(0.2)

