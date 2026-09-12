import math
import random
from typing import List, Tuple
from src.domain.entities.geometry import Point


def generate_bezier_trajectory(
    start: Point,
    end: Point,
    deviation_max: float = 60.0,
    overshoot: bool = False,
    steps: int = 35,
) -> List[Point]:
    """Generates human-like cursor trajectory using Cubic Bezier curves with natural velocity profile and optional overshoot."""
    dx = end.x - start.x
    dy = end.y - start.y
    distance = math.hypot(dx, dy)

    if distance < 5:
        return [end]

    # Adjust steps based on distance
    steps = max(15, min(75, int(distance / 12)))

    # Compute perpendicular vector for curvature
    perp_x = -dy / (distance + 1e-6)
    perp_y = dx / (distance + 1e-6)

    # Random deviation magnitude
    dev1 = (random.random() * 2 - 1) * min(deviation_max, distance * 0.3)
    dev2 = (random.random() * 2 - 1) * min(deviation_max, distance * 0.3)

    # Control points
    p0 = (float(start.x), float(start.y))
    p1 = (start.x + dx * 0.25 + perp_x * dev1, start.y + dy * 0.25 + perp_y * dev1)
    p2 = (start.x + dx * 0.75 + perp_y * dev2, start.y + dy * 0.75 + perp_x * dev2)

    target_x = float(end.x)
    target_y = float(end.y)

    # Add overshoot if requested
    if overshoot and distance > 100:
        overshoot_dist = random.uniform(5, 18)
        target_x += (dx / distance) * overshoot_dist
        target_y += (dy / distance) * overshoot_dist

    p3 = (target_x, target_y)

    points: List[Point] = []
    for i in range(steps + 1):
        # Ease-in-out time parameter (smooth acceleration and deceleration)
        t = i / steps
        # Smoothstep curve
        t_smooth = t * t * (3 - 2 * t)

        bx = (
            (1 - t_smooth) ** 3 * p0[0]
            + 3 * (1 - t_smooth) ** 2 * t_smooth * p1[0]
            + 3 * (1 - t_smooth) * t_smooth**2 * p2[0]
            + t_smooth**3 * p3[0]
        )
        by = (
            (1 - t_smooth) ** 3 * p0[1]
            + 3 * (1 - t_smooth) ** 2 * t_smooth * p1[1]
            + 3 * (1 - t_smooth) * t_smooth**2 * p2[1]
            + t_smooth**3 * p3[1]
        )

        # Micro-jitter (+- 1 px occasionally)
        if 0 < i < steps and random.random() < 0.2:
            bx += random.uniform(-0.8, 0.8)
            by += random.uniform(-0.8, 0.8)

        points.append(Point(x=int(round(bx)), y=int(round(by))))

    # If overshot, add small correction trajectory back to the true destination
    if overshoot and distance > 100:
        correction_steps = random.randint(4, 7)
        last_pt = points[-1]
        for c in range(1, correction_steps + 1):
            ct = c / correction_steps
            cx = last_pt.x + (end.x - last_pt.x) * ct
            cy = last_pt.y + (end.y - last_pt.y) * ct
            points.append(Point(x=int(round(cx)), y=int(round(cy))))

    return points
