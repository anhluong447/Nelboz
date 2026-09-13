import unittest
from src.domain.entities.geometry import Point
from src.infrastructure.input.bezier import generate_bezier_trajectory


class TestBezier(unittest.TestCase):
    def test_bezier_trajectory_reaches_destination(self):
        start = Point(x=100, y=100)
        end = Point(x=500, y=600)

        points = generate_bezier_trajectory(start=start, end=end, overshoot=False)

        self.assertGreater(len(points), 10)
        self.assertEqual(points[0], start)
        self.assertEqual(points[-1], end)

    def test_bezier_trajectory_with_overshoot(self):
        start = Point(x=50, y=50)
        end = Point(x=400, y=400)

        points = generate_bezier_trajectory(start=start, end=end, overshoot=True)

        self.assertGreater(len(points), 15)
        self.assertEqual(points[0], start)
        self.assertEqual(points[-1], end)

    def test_bezier_short_distance(self):
        start = Point(x=10, y=10)
        end = Point(x=12, y=12)

        points = generate_bezier_trajectory(start=start, end=end)
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0], end)

