from machine import Pin, PWM, time_pulse_us
from time import sleep, sleep_us

# PWM moteurs (vérifie bien les pins et fréquences adaptés à ton matériel)
ena = PWM(Pin(32), freq=20000, duty_u16=512)
enb = PWM(Pin(13), freq=20000, duty_u16=512)

in1 = Pin(25, Pin.OUT)
in2 = Pin(26, Pin.OUT)
in3 = Pin(14, Pin.OUT)
in4 = Pin(27, Pin.OUT)
def moteur_dc(vitesse, direction):
    if direction == "avant":
        in1.value(1)
        in2.value(0)
        in3.value(1)
        in4.value(0)
    elif direction == "arriere":
        in1.value(0)
        in2.value(1)
        in3.value(0)
        in4.value(1)
    elif direction == "gauche":
        in1.value(1)
        in2.value(0)
        in3.value(0)
        in4.value(1)
    elif direction == "droite":
        in1.value(0)
        in2.value(1)
        in3.value(1)
        in4.value(0)
    else:
        in1.value(0)
        in2.value(0)
        in3.value(0)
        in4.value(0)

    # Conversion du duty
    duty = int(vitesse * 65535 / 150)
    ena.duty_u16(duty)
    enb.duty_u16(duty)

def av():
    print("moteur avant")
    moteur_dc(150, "avant")
    sleep(0.1)

def ar():
    print("moteur arrière")
    moteur_dc(150, "arriere")
    sleep(0.1)

def gauche():
    print("moteur gauche")
    moteur_dc(150, "gauche")
    sleep(0.1)

def droite():
    print("moteur droite")
    moteur_dc(150, "droite")
    sleep(0.1)

def stop():
    print("stop")
    moteur_dc(0, "stop")
    sleep(0.1)

def move_combined(dir1, dir2):
    dir1 = dir1.lower()
    dir2 = dir2.lower()
    print(f"commande combinée: {dir1} + {dir2}")

    if dir1 == "avant":
        in1.value(1)
        in2.value(0)
        in3.value(1)
        in4.value(0)
    elif dir1 == "arriere":
        in1.value(0)
        in2.value(1)
        in3.value(0)
        in4.value(1)
    else:
        in1.value(0)
        in2.value(0)

    if dir2 == "droite":
        in3.value(0)
        in4.value(1)
    elif dir2 == "gauche":
        in3.value(1)
        in4.value(0)
    else:
        in3.value(0)
        in4.value(0)

    ena.duty(150)
    enb.duty(150)
    sleep(0.1)

# Capteur ultrason (Trigger = GPIO33, Echo = GPIO34)
# trigger = Pin(33, Pin.OUT)
# echo = Pin(34, Pin.IN)
trigger = Pin(33, Pin.OUT)
echo = Pin(34, Pin.IN)


def distance_cm():
    trigger.value(0)
    sleep_us(2)
    trigger.value(1)
    sleep_us(10)
    trigger.value(0)

    duration = time_pulse_us(echo, 1, 30000)  # Timeout à 30 ms
    if duration < 0:
        return 999  # Aucun écho reçu (trop loin)

    dist = (duration / 2) / 29.1
    return round(dist, 1)


