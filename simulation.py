# simulation.py - Simulation visuelle 2D du robot dans une petite maison
import math
from pathlib import Path

import pygame

from house_config import ROOM_ORDER, SIMULATION_LAYOUT, room_name
from iot_store import load_state
from robot import RobotVirtuel

# Constantes
LARGEUR = 980
HAUTEUR = 720
FPS = 60
ECHELLE = 2  # 1 pixel = 2cm

# Couleurs
BLANC = (250, 248, 243)
NOIR = (20, 26, 36)
GRIS = (188, 196, 208)
GRIS_FONCE = (94, 107, 124)
BLEU = (60, 136, 255)
BLEU_CLAIR = (217, 231, 255)
VERT = (53, 185, 112)
VERT_CLAIR = (224, 247, 233)
ROUGE = (210, 76, 76)
ROUGE_CLAIR = (252, 232, 232)
JAUNE = (244, 188, 74)
SABLE = (242, 236, 222)
MUR = (110, 88, 64)

BASE_DIR = Path(__file__).resolve().parent


class SimulationRobot:
    """Simulation visuelle simple du robot dans une maison."""

    def __init__(self):
        pygame.init()
        self.ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
        pygame.display.set_caption("Robot Assistant - House Simulation")
        self.horloge = pygame.time.Clock()

        self.robot = RobotVirtuel()
        self.robot.position = {"x": -120, "y": -40}
        self.taille_robot = 18

        self.origine_x = LARGEUR // 2
        self.origine_y = HAUTEUR // 2 + 30

        self.font = pygame.font.Font(None, 30)
        self.font_petit = pygame.font.Font(None, 21)
        self.font_room = pygame.font.Font(None, 24)

        self.trace = []
        self.iot_snapshot = {}
        self._last_state_refresh = 0

        self.rooms = {
            room_id: {
                "label": room_name(room_id),
                "rect": pygame.Rect(*SIMULATION_LAYOUT[room_id]["rect"]),
                "door": SIMULATION_LAYOUT[room_id]["door"],
            }
            for room_id in ROOM_ORDER
            if room_id in SIMULATION_LAYOUT
        }

    def pos_robot_ecran(self):
        x = self.origine_x + (self.robot.position["x"] / ECHELLE)
        y = self.origine_y - (self.robot.position["y"] / ECHELLE)
        return int(x), int(y)

    def _refresh_iot_state(self):
        now = pygame.time.get_ticks()
        if now - self._last_state_refresh < 1000:
            return
        self._last_state_refresh = now
        try:
            self.iot_snapshot = load_state()
        except Exception:
            self.iot_snapshot = {}

    def _room_state(self, room_id):
        return self.iot_snapshot.get("rooms", {}).get(room_id, {})

    def _room_fill_color(self, room_id):
        room = self._room_state(room_id)
        sensors = room.get("sensors", {})
        devices = room.get("devices", {})

        if sensors.get("gas_ppm", 0) > 400:
            return ROUGE_CLAIR
        if devices.get("light_main", {}).get("state") == "on":
            return SABLE
        return BLEU_CLAIR

    def _robot_room_name(self):
        x, y = self.pos_robot_ecran()
        for room in self.rooms.values():
            if room["rect"].collidepoint(x, y):
                return room["label"]
        return "Hallway"

    def dessiner_grille(self):
        for x in range(0, LARGEUR, 40):
            pygame.draw.line(self.ecran, (235, 237, 241), (x, 0), (x, HAUTEUR), 1)
        for y in range(0, HAUTEUR, 40):
            pygame.draw.line(self.ecran, (235, 237, 241), (0, y), (LARGEUR, y), 1)

    def dessiner_maison(self):
        title = self.font.render("Smart House Simulation", True, NOIR)
        self.ecran.blit(title, (32, 24))

        subtitle = self.font_petit.render(
            ", ".join(room_name(room_id) for room_id in self.rooms), True, GRIS_FONCE
        )
        self.ecran.blit(subtitle, (34, 56))

        for room_id, room_meta in self.rooms.items():
            rect = room_meta["rect"]
            room_state = self._room_state(room_id)
            sensors = room_state.get("sensors", {})
            devices = room_state.get("devices", {})

            pygame.draw.rect(self.ecran, self._room_fill_color(room_id), rect, border_radius=14)
            pygame.draw.rect(self.ecran, MUR, rect, 4, border_radius=14)
            pygame.draw.line(self.ecran, BLANC, room_meta["door"][0], room_meta["door"][1], 8)

            label = self.font_room.render(room_meta["label"], True, NOIR)
            self.ecran.blit(label, (rect.x + 14, rect.y + 12))

            temp = sensors.get("temperature", "--")
            humidity = sensors.get("humidity", "--")
            gas_ppm = sensors.get("gas_ppm", 0)
            light_on = devices.get("light_main", {}).get("state") == "on"
            door_state = devices.get("door_main", {}).get("state", "n/a")

            status_lines = [
                f"Light: {'ON' if light_on else 'OFF'}",
                f"Temp: {temp} C",
                f"Humidity: {humidity}%",
            ]
            if "gas_ppm" in sensors:
                status_lines.append(f"Gas: {gas_ppm} ppm")
            if "door_main" in devices:
                status_lines.append(f"Door: {door_state}")

            y_offset = rect.y + 48
            for line in status_lines:
                line_surface = self.font_petit.render(line, True, NOIR)
                self.ecran.blit(line_surface, (rect.x + 16, y_offset))
                y_offset += 22

            self._draw_room_components(room_id, rect, devices, sensors)

            if gas_ppm > 400:
                warning = self.font_petit.render("Gas alert", True, ROUGE)
                self.ecran.blit(warning, (rect.right - 86, rect.y + 14))

    def _draw_room_components(self, room_id, rect, devices, sensors):
        component_y = rect.y + 138
        if room_id == "living_room":
            self._draw_light_component(rect.x + 245, rect.y + 74, devices.get("light_main", {}).get("state") == "on", "Main Light")
            self._draw_ac_component(rect.x + 232, rect.y + 126, devices.get("ac_main", {}).get("state") == "on", "Main AC")
            self._draw_door_component(rect.x + 246, rect.y + 180, devices.get("door_main", {}).get("state") == "unlocked", "Front Door")
        elif room_id == "kitchen":
            self._draw_light_component(rect.x + 96, rect.y + 76, devices.get("light_main", {}).get("state") == "on", "Kitchen Light")
            self._draw_gas_component(rect.x + 92, rect.y + 132, sensors.get("gas_ppm", 0), "Kitchen Gas")
        elif room_id == "bedroom":
            self._draw_light_component(rect.x + 95, rect.y + 78, devices.get("light_main", {}).get("state") == "on", "Bedroom Light")
            self._draw_ac_component(rect.x + 90, rect.y + 128, devices.get("ac_main", {}).get("state") == "on", "Bedroom AC")
            self._draw_door_component(rect.x + 98, rect.y + 178, devices.get("door_main", {}).get("state") == "unlocked", "Bedroom Door")
        elif room_id == "toilet":
            self._draw_light_component(rect.x + 14, rect.y + 70, devices.get("light_main", {}).get("state") == "on", "Toilet Light")
            self._draw_door_component(rect.x + 14, rect.y + 120, devices.get("door_main", {}).get("state") == "unlocked", "Toilet Door")

    def _draw_device_badge(self, x, y, label, active):
        width = 58 if len(label) <= 4 else 68
        badge_rect = pygame.Rect(x, y, width, 22)
        fill = VERT_CLAIR if active else (236, 239, 244)
        border = VERT if active else GRIS_FONCE
        pygame.draw.rect(self.ecran, fill, badge_rect, border_radius=9)
        pygame.draw.rect(self.ecran, border, badge_rect, 2, border_radius=9)
        text = self.font_petit.render(label, True, NOIR)
        self.ecran.blit(text, (x + 8, y + 3))
        return x + width + 8

    def _draw_light_component(self, x, y, active, label):
        bulb_color = JAUNE if active else GRIS
        pygame.draw.circle(self.ecran, bulb_color, (x + 14, y + 12), 11)
        pygame.draw.circle(self.ecran, NOIR, (x + 14, y + 12), 11, 2)
        pygame.draw.rect(self.ecran, NOIR, (x + 10, y + 22, 8, 8), border_radius=2)
        text = self.font_petit.render(label, True, NOIR)
        self.ecran.blit(text, (x + 34, y + 4))

    def _draw_ac_component(self, x, y, active, label):
        fill = BLEU if active else GRIS
        unit = pygame.Rect(x, y, 34, 22)
        pygame.draw.rect(self.ecran, fill, unit, border_radius=5)
        pygame.draw.rect(self.ecran, NOIR, unit, 2, border_radius=5)
        for offset in (5, 11, 17):
            pygame.draw.line(self.ecran, BLANC if active else NOIR, (x + 6, y + offset), (x + 28, y + offset), 1)
        text = self.font_petit.render(label, True, NOIR)
        self.ecran.blit(text, (x + 42, y + 2))

    def _draw_door_component(self, x, y, unlocked, label):
        color = VERT if unlocked else MUR
        door = pygame.Rect(x, y, 20, 34)
        pygame.draw.rect(self.ecran, color, door, border_radius=3)
        pygame.draw.rect(self.ecran, NOIR, door, 2, border_radius=3)
        pygame.draw.circle(self.ecran, BLANC, (x + 15, y + 17), 2)
        text = self.font_petit.render(label, True, NOIR)
        self.ecran.blit(text, (x + 30, y + 8))

    def _draw_gas_component(self, x, y, gas_ppm, label):
        active = gas_ppm > 0
        body_color = ROUGE if gas_ppm > 400 else (JAUNE if active else GRIS)
        body = pygame.Rect(x, y, 18, 30)
        pygame.draw.rect(self.ecran, body_color, body, border_radius=6)
        pygame.draw.rect(self.ecran, NOIR, body, 2, border_radius=6)
        pygame.draw.rect(self.ecran, NOIR, (x + 5, y - 5, 8, 6), border_radius=2)
        text = self.font_petit.render(label, True, NOIR)
        self.ecran.blit(text, (x + 28, y + 2))

    def dessiner_robot(self):
        x, y = self.pos_robot_ecran()

        couleur = VERT if self.robot.batterie > 20 else ROUGE
        pygame.draw.circle(self.ecran, couleur, (x, y), self.taille_robot)
        pygame.draw.circle(self.ecran, NOIR, (x, y), self.taille_robot, 2)

        angle_rad = math.radians(self.robot.direction)
        fin_x = x + self.taille_robot * math.sin(angle_rad)
        fin_y = y - self.taille_robot * math.cos(angle_rad)
        pygame.draw.line(self.ecran, BLANC, (x, y), (fin_x, fin_y), 3)
        pygame.draw.circle(self.ecran, BLANC, (x, y), 3)

    def dessiner_trace(self):
        if len(self.trace) > 1:
            pygame.draw.lines(self.ecran, JAUNE, False, self.trace, 3)

    def dessiner_interface(self):
        etat = self.robot.etat()
        robot_room = self._robot_room_name()

        panel = pygame.Rect(32, 590, 916, 98)
        pygame.draw.rect(self.ecran, (255, 255, 255), panel, border_radius=16)
        pygame.draw.rect(self.ecran, GRIS, panel, 2, border_radius=16)

        info_lines = [
            f"Robot room: {robot_room}",
            f"Position: ({etat['position']['x']:.1f}, {etat['position']['y']:.1f}) cm",
            f"Direction: {etat['direction']} deg ({etat['direction_text']})",
            f"Battery: {etat['batterie']:.1f}%",
            f"Actions: {etat['nb_actions']}",
        ]

        x_positions = [52, 240, 470, 700, 840]
        for idx, line in enumerate(info_lines):
            surface = self.font_petit.render(line, True, NOIR)
            self.ecran.blit(surface, (x_positions[idx], 626))

        aide = self.font_petit.render(
            "Arrows move | SPACE scan | R recharge | C clear trace | ESC quit",
            True,
            GRIS_FONCE,
        )
        self.ecran.blit(aide, (52, 653))

    def ajouter_trace(self):
        self.trace.append(self.pos_robot_ecran())
        if len(self.trace) > 500:
            self.trace.pop(0)

    def executer(self):
        en_cours = True

        print("=" * 60)
        print("HOUSE SIMULATION STARTED")
        print("=" * 60)
        print("Use arrow keys to move the robot inside the house")
        print("Press ESC to quit\n")

        while en_cours:
            self.horloge.tick(FPS)
            self._refresh_iot_state()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    en_cours = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        print(self.robot.avancer(20))
                        self.ajouter_trace()
                    elif event.key == pygame.K_DOWN:
                        print(self.robot.reculer(20))
                        self.ajouter_trace()
                    elif event.key == pygame.K_LEFT:
                        print(self.robot.tourner_gauche(15))
                    elif event.key == pygame.K_RIGHT:
                        print(self.robot.tourner_droite(15))
                    elif event.key == pygame.K_SPACE:
                        message, _distances = self.robot.scanner()
                        print(message)
                    elif event.key == pygame.K_r:
                        print(self.robot.recharger())
                    elif event.key == pygame.K_c:
                        self.trace.clear()
                        print("Trace cleared")
                    elif event.key == pygame.K_ESCAPE:
                        en_cours = False

            self.ecran.fill(BLANC)
            self.dessiner_grille()
            self.dessiner_maison()
            self.dessiner_trace()
            self.dessiner_robot()
            self.dessiner_interface()
            pygame.display.flip()

        print("\n" + "=" * 60)
        print("FINAL ROBOT STATE:")
        etat = self.robot.etat()
        print(f"  Final position: ({etat['position']['x']:.1f}, {etat['position']['y']:.1f})")
        print(f"  Direction: {etat['direction']} deg ({etat['direction_text']})")
        print(f"  Battery: {etat['batterie']:.1f}%")
        print(f"  Total actions: {etat['nb_actions']}")
        print("=" * 60)

        pygame.quit()


if __name__ == "__main__":
    simulation = SimulationRobot()
    simulation.executer()
