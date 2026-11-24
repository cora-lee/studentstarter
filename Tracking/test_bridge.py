import unittest
from types import SimpleNamespace
from bridge import (CollectivePauseDetector, PerformerTracker,
                    associate_hand_gestures, everyone_shows_open_palm,
                    extract_features, requested_count)


class TrackingTests(unittest.TestCase):
    @staticmethod
    def pose_points():
        points = [SimpleNamespace(x=.5, y=.5, presence=1., visibility=1.) for _ in range(33)]
        for i, xy in {11:(.4,.3), 12:(.6,.3), 15:(.4,.5), 16:(.6,.5),
                      23:(.43,.6), 24:(.57,.6)}.items():
            points[i].x, points[i].y = xy
        return points

    def test_gestures_are_matched_to_nearest_performer_wrist(self):
        first, second = self.pose_points(), self.pose_points()
        first[15].x, first[16].x = .2, .4
        second[15].x, second[16].x = .6, .8
        observations = [((.3, .5), [], [], first), ((.7, .5), [], [], second)]
        result = SimpleNamespace(
            hand_landmarks=[[SimpleNamespace(x=.21, y=.5)],
                            [SimpleNamespace(x=.79, y=.5)]],
            gestures=[[SimpleNamespace(category_name='Open_Palm', score=.9)],
                      [SimpleNamespace(category_name='Victory', score=.8)]])
        matched = associate_hand_gestures(result, {1: 0, 2: 1}, observations)
        self.assertEqual(matched[1]['leftGesture'], 'Open_Palm')
        self.assertEqual(matched[2]['rightGesture'], 'Victory')
        self.assertTrue(everyone_shows_open_palm({1: matched[1]}, 1))
        self.assertFalse(everyone_shows_open_palm(matched, 2))

    def test_low_confidence_or_distant_gesture_is_not_assigned(self):
        pose = self.pose_points()
        observations = [((.5, .5), [], [], pose)]
        result = SimpleNamespace(
            hand_landmarks=[[SimpleNamespace(x=.5, y=.5)],
                            [SimpleNamespace(x=.95, y=.95)]],
            gestures=[[SimpleNamespace(category_name='Open_Palm', score=.54)],
                      [SimpleNamespace(category_name='Closed_Fist', score=.99)]])
        matched = associate_hand_gestures(result, {1: 0}, observations)
        self.assertEqual(matched[1]['leftGesture'], '')
        self.assertEqual(matched[1]['rightGesture'], '')

    def test_collective_pause_is_debounced_and_releases_immediately(self):
        detector = CollectivePauseDetector(hold_seconds=.6)
        self.assertFalse(detector.update(True, 10.0))
        self.assertFalse(detector.update(True, 10.59))
        self.assertTrue(detector.update(True, 10.6))
        self.assertFalse(detector.update(False, 10.61))
        self.assertFalse(detector.update(True, 11.0))

    def test_roles_survive_detection_reordering_and_dropout(self):
        t = PerformerTracker(3)
        self.assertEqual(t.assign([(.8, .5), (.2, .5)]), {})
        self.assertEqual(t.assign([(.8, .5), (.2, .5), (.5, .5)]), {1: 1, 2: 2, 3: 0})
        self.assertEqual(t.assign([(.51, .5), (.81, .5), (.21, .5)]), {1: 2, 2: 0, 3: 1})
        self.assertEqual(t.assign([(.52, .5), (.22, .5)]), {1: 1, 2: 0})
        self.assertEqual(t.assign([(.82, .5)]), {3: 0})

    def test_ambiguous_assignment_is_rejected(self):
        t = PerformerTracker(3)
        t.assign([(.2, .5), (.4, .5), (.8, .5)])
        self.assertEqual(t.assign([(.3, .5), (.8, .5)]), {})
        t.reset()
        self.assertIsNone(t.positions)

    def test_one_and_two_people_with_extra_bystanders(self):
        for count in (1, 2):
            t = PerformerTracker(count)
            assigned = t.assign([(.8, .5), (.2, .5), (.5, .5)])
            self.assertEqual(len(assigned), count)
            self.assertEqual(assigned[1], 1)
            self.assertEqual(t.assign([(.21, .5)]), {1: 0})

    def test_count_request_validation(self):
        for count in (1, 2, 3, 4):
            self.assertEqual(requested_count('{"version":1,"performerCount":%d}' % count), count)
        for data in ('null', '[]', 'bad', '{"version":1,"performerCount":0}',
                     '{"version":1,"performerCount":5}', '{"version":1,"performerCount":true}',
                     '{"version":1,"performerCount":"2"}', '{"version":2,"performerCount":2}'):
            self.assertIsNone(requested_count(data))

    def test_four_people(self):
        t = PerformerTracker(4)
        self.assertEqual(len(t.assign([(.1, .5), (.35, .5), (.6, .5), (.85, .5)])), 4)
        self.assertEqual(t.assign([]), {})

    def test_upper_body_works_with_no_visible_lower_body(self):
        points = [SimpleNamespace(x=.5, y=.5, presence=0., visibility=0.) for _ in range(33)]
        for i, xy in {11:(.4,.3), 12:(.6,.3), 15:(.3,.5), 16:(.7,.5)}.items():
            points[i] = SimpleNamespace(x=xy[0], y=xy[1], presence=1., visibility=1.)
        center, baseline, confidence = extract_features(points, True)
        self.assertEqual(center, (.5, .3))
        self.assertEqual(confidence, [1.] * 6)
        self.assertEqual(extract_features(points)[2][4], 0.)
        points[15].y -= .1
        _, raised, _ = extract_features(points, True)
        self.assertGreater(raised[0], baseline[0])
        self.assertEqual(raised[0], raised[2])
        self.assertEqual(raised[1], raised[3])
        points[11].y -= .05
        self.assertLess(extract_features(points, True)[1][4], baseline[4])
        points[15].visibility = 0.
        _, _, confidence = extract_features(points, True)
        self.assertEqual(confidence, [0., 1., 0., 1., 1., 0.])

    def test_features_are_translation_and_scale_invariant(self):
        points = [SimpleNamespace(x=.5, y=.5, presence=1., visibility=1.) for _ in range(33)]
        for i, xy in {11:(.4,.3),12:(.6,.3),23:(.4,.6),24:(.6,.6),15:(.2,.1),16:(.8,.2),27:(.4,.9),28:(.6,.9)}.items():
            points[i].x, points[i].y = xy
        _, first, _ = extract_features(points)
        for p in points:
            p.x = p.x * .5 + .1
            p.y = p.y * .5 + .2
        _, second, _ = extract_features(points)
        for a, b in zip(first, second):
            self.assertAlmostEqual(a, b)
        points[15].visibility = .1
        _, _, confidence = extract_features(points)
        self.assertEqual(confidence[0], .1)
        self.assertEqual(confidence[1], 1.)


if __name__ == '__main__':
    unittest.main()
