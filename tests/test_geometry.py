import unittest
from src.domain.entities.geometry import Point, BoundingBox


class TestGeometry(unittest.TestCase):
    def test_point_offset(self):
        pt = Point(x=10, y=20)
        shifted = pt.offset(dx=5, dy=-10)
        self.assertEqual(shifted.x, 15)
        self.assertEqual(shifted.y, 10)
        self.assertEqual(shifted.to_tuple(), (15, 10))

    def test_bounding_box_properties(self):
        box = BoundingBox(x=100, y=200, width=50, height=80)
        self.assertEqual(box.left, 100)
        self.assertEqual(box.top, 200)
        self.assertEqual(box.right, 150)
        self.assertEqual(box.bottom, 280)
        self.assertEqual(box.center, Point(x=125, y=240))

    def test_bounding_box_containment(self):
        box = BoundingBox(x=10, y=10, width=100, height=100)
        self.assertTrue(box.contains(Point(x=50, y=50)))
        self.assertTrue(box.contains(Point(x=10, y=10)))
        self.assertTrue(box.contains(Point(x=110, y=110)))
        self.assertFalse(box.contains(Point(x=5, y=50)))
        self.assertFalse(box.contains(Point(x=50, y=120)))

    def test_bounding_box_intersection(self):
        b1 = BoundingBox(x=0, y=0, width=50, height=50)
        b2 = BoundingBox(x=25, y=25, width=50, height=50)
        b3 = BoundingBox(x=100, y=100, width=50, height=50)

        self.assertTrue(b1.intersects(b2))
        self.assertTrue(b2.intersects(b1))
        self.assertFalse(b1.intersects(b3))

