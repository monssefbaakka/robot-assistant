# robot.py - Virtual robot with simple indoor navigation rules
import math
from datetime import datetime

from house_config import ROBOT_SIMULATION_WORLD


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class RobotVirtuel:
    """Virtual robot with collision-aware movement and map-based scanning."""

    def __init__(self):
        spawn = ROBOT_SIMULATION_WORLD["spawn"]
        self.position = {"x": float(spawn["x"]), "y": float(spawn["y"])}
        self.direction = 0
        self.vitesse = 20
        self.batterie = 100
        self.historique = []
        self.etat_actuel = "idle"
        self.robot_radius_cm = float(ROBOT_SIMULATION_WORLD.get("robot_radius_cm", 12.0))
        self.walkable_areas = list(ROBOT_SIMULATION_WORLD.get("walkable_areas", []))
        self.obstacles = list(ROBOT_SIMULATION_WORLD.get("obstacles", []))
        self.last_scan = None

    def avancer(self, distance_cm=None):
        """Move forward or backward while respecting walls and obstacles."""
        if distance_cm is None:
            distance_cm = self.vitesse

        if self.batterie < 5:
            return "Battery too low to move."

        requested_distance = float(distance_cm)
        step_size = 4.0
        moved_distance = 0.0
        remaining = abs(requested_distance)
        direction_sign = 1.0 if requested_distance >= 0 else -1.0
        angle_rad = math.radians(self.direction)
        blocked = False

        self.etat_actuel = "moving"

        while remaining > 0:
            step = min(step_size, remaining)
            delta = step * direction_sign
            candidate_x = self.position["x"] + delta * math.sin(angle_rad)
            candidate_y = self.position["y"] + delta * math.cos(angle_rad)
            if not self._can_place(candidate_x, candidate_y):
                blocked = True
                break

            self.position["x"] = round(candidate_x, 1)
            self.position["y"] = round(candidate_y, 1)
            moved_distance += step
            remaining -= step

        battery_cost = moved_distance * 0.08
        self.batterie = max(0.0, self.batterie - battery_cost)
        zone = self._get_current_zone_label()
        signed_moved = moved_distance * direction_sign

        if moved_distance == 0 and blocked:
            message = f"Blocked by wall or furniture in {zone}."
        elif blocked:
            message = (
                f"Moved {signed_moved:.0f}cm, then stopped by an obstacle in {zone} "
                f"at ({self.position['x']:.1f}, {self.position['y']:.1f})."
            )
        else:
            message = (
                f"Moved {signed_moved:.0f}cm in {zone} -> "
                f"({self.position['x']:.1f}, {self.position['y']:.1f})"
            )

        self._log("move", message)
        self.etat_actuel = "idle"
        return message

    def reculer(self, distance_cm=None):
        """Move backward."""
        if distance_cm is None:
            distance_cm = self.vitesse
        return self.avancer(-distance_cm)

    def tourner_droite(self, angle_degres=90):
        """Turn right."""
        return self.tourner(angle_degres)

    def tourner_gauche(self, angle_degres=90):
        """Turn left."""
        return self.tourner(-angle_degres)

    def tourner(self, angle_degres):
        """Rotate the robot in place."""
        self.direction = (self.direction + angle_degres) % 360
        self.batterie = max(0.0, self.batterie - abs(angle_degres) * 0.015)
        direction_text = self._get_direction_text()
        zone = self._get_current_zone_label()
        message = f"Turned {angle_degres}deg in {zone} -> {self.direction}deg ({direction_text})"
        self._log("turn", message)
        return message

    def scanner(self):
        """Return scan distances based on the current map."""
        self.etat_actuel = "scanning"
        distances = {
            "avant": self._raycast(self.direction),
            "droite": self._raycast(self.direction + 90),
            "gauche": self._raycast(self.direction - 90),
            "arriere": self._raycast(self.direction + 180),
        }
        self.last_scan = distances

        zone = self._get_current_zone_label()
        message = (
            f"Scan in {zone}:\n"
            f"   Front: {distances['avant']}cm\n"
            f"   Right: {distances['droite']}cm\n"
            f"   Left: {distances['gauche']}cm\n"
            f"   Back: {distances['arriere']}cm"
        )
        self._log("scan", message)
        self.etat_actuel = "idle"
        self.batterie = max(0.0, self.batterie - 0.5)
        return message, distances

    def recharger(self):
        """Recharge battery."""
        self.etat_actuel = "charging"
        old_bat = self.batterie
        self.batterie = 100
        message = f"Battery recharged: {old_bat:.0f}% -> 100%"
        self._log("charge", message)
        self.etat_actuel = "idle"
        return message

    def etat(self):
        """Return the full robot state."""
        return {
            "position": self.position,
            "direction": self.direction,
            "direction_text": self._get_direction_text(),
            "batterie": round(self.batterie, 1),
            "etat": self.etat_actuel,
            "nb_actions": len(self.historique),
            "zone": self._get_current_zone_id(),
            "zone_label": self._get_current_zone_label(),
            "last_scan": self.last_scan,
        }

    def afficher_historique(self):
        """Print action history."""
        print("\nACTION HISTORY:")
        for index, entry in enumerate(self.historique, 1):
            print(f"  {index}. [{entry['timestamp']}] {entry['message']}")

    def reset(self):
        """Reset the robot to the default spawn point."""
        spawn = ROBOT_SIMULATION_WORLD["spawn"]
        self.position = {"x": float(spawn["x"]), "y": float(spawn["y"])}
        self.direction = 0
        self.batterie = 100
        self.historique = []
        self.etat_actuel = "idle"
        self.last_scan = None
        return "Robot reset."

    def _log(self, action, message):
        self.historique.append(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "action": action,
                "message": message,
            }
        )

    def _get_direction_text(self):
        angle = self.direction % 360
        if 337.5 <= angle or angle < 22.5:
            return "North"
        if 22.5 <= angle < 67.5:
            return "North-East"
        if 67.5 <= angle < 112.5:
            return "East"
        if 112.5 <= angle < 157.5:
            return "South-East"
        if 157.5 <= angle < 202.5:
            return "South"
        if 202.5 <= angle < 247.5:
            return "South-West"
        if 247.5 <= angle < 292.5:
            return "West"
        return "North-West"

    def _can_place(self, x, y):
        if not any(self._circle_inside_rect(x, y, area) for area in self.walkable_areas):
            return False
        return not any(self._circle_intersects_rect(x, y, obstacle) for obstacle in self.obstacles)

    def _circle_inside_rect(self, x, y, rect):
        radius = self.robot_radius_cm
        return (
            x - radius >= rect["x1"]
            and x + radius <= rect["x2"]
            and y - radius >= rect["y1"]
            and y + radius <= rect["y2"]
        )

    def _circle_intersects_rect(self, x, y, rect):
        nearest_x = _clamp(x, rect["x1"], rect["x2"])
        nearest_y = _clamp(y, rect["y1"], rect["y2"])
        dx = x - nearest_x
        dy = y - nearest_y
        return dx * dx + dy * dy < self.robot_radius_cm * self.robot_radius_cm

    def _get_current_zone_id(self):
        for area in self.walkable_areas:
            if area["x1"] <= self.position["x"] <= area["x2"] and area["y1"] <= self.position["y"] <= area["y2"]:
                return area["id"]
        return "unknown"

    def _get_current_zone_label(self):
        for area in self.walkable_areas:
            if area["x1"] <= self.position["x"] <= area["x2"] and area["y1"] <= self.position["y"] <= area["y2"]:
                return area["label"]
        return "Unknown Area"

    def _raycast(self, angle_degrees, max_distance=240):
        angle_rad = math.radians(angle_degrees)
        step = 2.0
        distance = 0.0
        while distance <= max_distance:
            probe_x = self.position["x"] + math.sin(angle_rad) * distance
            probe_y = self.position["y"] + math.cos(angle_rad) * distance
            if not self._can_place(probe_x, probe_y):
                return max(0, int(distance - step))
            distance += step
        return int(max_distance)


if __name__ == "__main__":
    print("=" * 50)
    print("ROBOT SIMULATION TEST")
    print("=" * 50)

    robot = RobotVirtuel()
    print(robot.avancer(60))
    print(robot.tourner_droite(90))
    print(robot.avancer(40))
    message, distances = robot.scanner()
    print(message)
    print(robot.recharger())
    print(robot.etat())
