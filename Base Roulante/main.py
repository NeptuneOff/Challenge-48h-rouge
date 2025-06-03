# ---------------------------------------------------
# main_robot.py
# ESP32 MicroPython : mode manuel ↔ mode autonome
# + lecture DHT11 + LED bleue indiquant hygrométrie > 50%
# ---------------------------------------------------

from motor import *          # av(), droite(), stop(), etc.
import network
import espnow
from machine import Pin
import time
from hcsr04 import HCSR04    # capteur ultrason
import dht                   # module pour DHT11

# ────────────────────────────────────────────────────
# 1. Initialisation ESP-NOW
# ────────────────────────────────────────────────────

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.disconnect()

e = espnow.ESPNow()
e.active(True)
# (Ne jamais purger la file ESP-NOW.)

# ────────────────────────────────────────────────────
# 2. Initialisation bouton local (GPIO4 en pull-up)
# ────────────────────────────────────────────────────

btn_pin = Pin(4, Pin.IN, Pin.PULL_UP)
etat_btn_precedent = btn_pin.value()

# ────────────────────────────────────────────────────
# 3. Initialisation capteur ultrason (GPIO33=Trig, GPIO34=Echo)
# ────────────────────────────────────────────────────

sensor = HCSR04(trigger_pin=33, echo_pin=34, echo_timeout_us=100000)

# ────────────────────────────────────────────────────
# 4. Initialisation DHT11 (GPIO12 / D12) et LED (GPIO2)
# ────────────────────────────────────────────────────

dht_sensor = dht.DHT11(Pin(12))
last_dht_read = time.ticks_ms() - 2000  # pour forcer une lecture immédiate
temp_val = None
hum_val = None

# LED bleue sur GPIO2 (GPIO35 est input-only et ne peut pas piloter une LED)
led = Pin(2, Pin.OUT)

# ────────────────────────────────────────────────────
# 5. Variables de mode
# ────────────────────────────────────────────────────

autonome = False   # False = manuel ; True = auto

# Seuils
SEUIL_AVANT = 15   # si > 15 cm → on avance
SEUIL_LIBRE = 20   # si > 20 cm → fin du pivot

print("→ Démarrage du robot. En attente de commandes ESP-NOW…")

# ────────────────────────────────────────────────────
# 6. Boucle principale unique
# ────────────────────────────────────────────────────

while True:

    # ────────────────────────────────────────────────────
    # 6.1 Lecture DHT11 (toutes les 2 secondes) + pilotage LED
    # ────────────────────────────────────────────────────
    now = time.ticks_ms()
    if time.ticks_diff(now, last_dht_read) >= 2000:
        try:
            dht_sensor.measure()
            temp_val = dht_sensor.temperature()
            hum_val = dht_sensor.humidity()
            print("[DHT] Temp = {}°C  Hum = {}%".format(temp_val, hum_val))
        except Exception as e_dht:
            print("[DHT] ERREUR lecture DHT11 :", e_dht)
        last_dht_read = now

    # Allume la LED si hygrométrie > 50 %, sinon l’éteint
    if hum_val is not None and hum_val > 50:
        led.value(1)
    else:
        led.value(0)

    # ────────────────────────────────────────────────────
    # 6.2 MODE AUTO
    # ────────────────────────────────────────────────────
    if autonome:
        # A) Affichage pour confirmer que l’on est en mode auto
        print("\n[DEBUG] → MODE AUTONOME actif")

        # B) Lecture de la distance
        try:
            dist = sensor.distance_cm()
            print("capteur ok")
        except Exception as e_sensor:
            print("[DEBUG] – ERREUR capteur :", e_sensor)
            stop()
            time.sleep(0.1)
            # On reste en auto, on va retenter la mesure au tour suivant
            continue

        print("[DEBUG] – DISTANCE (cm) mesurée =", dist)

        # C) Si pas d’obstacle proche, on avance
        if dist > SEUIL_AVANT:
            print("[DEBUG] – Aucun obstacle proche (> {} cm). On AVANCE.".format(SEUIL_AVANT))
            av()
            # Petit délai pour que le robot avance, puis on re-mesure
            time.sleep(0.05)

        else:
            # D) Obstacle détecté (dist ≤ SEUIL_AVANT) : STOP + PIVOT DROITE
            print("[DEBUG] – Obstacle à {} cm (≤ {}). STOP + PIVOT DROITE".format(dist, SEUIL_AVANT))
            stop()
            time.sleep(0.1)

            # E) Boucle de pivot : pivoter, mesurer, recommencer jusqu’à dist2 > SEUIL_LIBRE
            IsObstacle = True
            while IsObstacle:
                droite()
                print("[DEBUG] – PIVOT DROITE (tour)")
                time.sleep(0.3)
                stop()
                time.sleep(0.05)

                # Nouvelle mesure après chaque tour de pivot
                try:
                    dist2 = sensor.distance_cm()
                except Exception as e_sensor2:
                    print("[DEBUG] – ERREUR capteur pendant pivot :", e_sensor2)
                    stop()
                    time.sleep(0.1)
                    # On reste en pivot pour retenter la mesure
                    continue

                print("[DEBUG] – Distance après pivot (cm) =", dist2)

                if dist2 > SEUIL_LIBRE:
                    print("[DEBUG] – Espace libre détecté (> {} cm). Fin du PIVOT.".format(SEUIL_LIBRE))
                    IsObstacle = False
                # Sinon, on boucle pour pivoter à nouveau

            # F) Pivot terminé, on repart en avant
            print("[DEBUG] – PIVOT terminé, on repart en AVANT.")
            av()
            time.sleep(0.05)

        # G) Après action (avance ou pivot), on vérifie ESP-NOW / bouton pour revenir en manuel
        host2, msg2 = e.recv()
        if msg2:
            cmd2 = msg2.decode()
            print("[DEBUG] – Reçu en AUTO via ESP-NOW :", cmd2)
            if cmd2 == "manuel":
                autonome = False
                stop()
                print("→ Passage en mode MANUEL (commande ESP-NOW reçue)")
                time.sleep(0.1)
                # Passera ensuite dans le bloc manuel
                continue

        valeur_btn = btn_pin.value()
        if valeur_btn == 0 and etat_btn_precedent == 1:
            autonome = False
            stop()
            print("→ Passage en mode MANUEL (bouton local détecté)")
            time.sleep(0.5)    # anti-rebond
            etat_btn_precedent = valeur_btn
            continue
        etat_btn_precedent = valeur_btn

        # À la fin, si on est toujours en auto, on boucle pour une nouvelle mesure
        continue

    # ────────────────────────────────────────────────────
    # 6.3 MODE MANUEL (autonome == False)
    # ────────────────────────────────────────────────────

    host, msg = e.recv()
    if not msg:
        time.sleep(0.01)
        continue

    texte = msg.decode()
    print("\n[DEBUG] – Mode MANUEL – Commande reçue :", texte)

    # Si on reçoit “autonome”, on passe immédiatement en auto
    if texte == "autonome":
        autonome = True
        print("→ Passage en mode AUTONOME (commande ESP-NOW reçue)")
        time.sleep(0.1)
        continue  # la boucle repart dans “if autonome”

    # Si on reçoit “manuel” en mode manuel, on reste à l'arrêt (sécurité)
    if texte == "manuel":
        stop()
        print("→ On reste en mode MANUEL (commande ESP-NOW reçue)")
        continue

    # Sinon, commandes de déplacement manuel
    if "_" in texte:
        dir1, dir2 = texte.split("_")
        move_combined(dir1, dir2)
    else:
        if texte == "avant":
            av()
        elif texte == "arriere":
            ar()
        elif texte == "gauche":
            gauche()
        elif texte == "droite":
            droite()
        else:
            stop()

