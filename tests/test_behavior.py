import sys
import unittest

sys.path.insert(0, r"C:\Users\Shreya\lockedin\src")

from behavior.focus_state_machine import FocusStateMachine, BehaviorState


class TestLockedInBehavior(unittest.TestCase):
    def make_engine(self):
        return FocusStateMachine()

    def test_relevant_activity_stays_focused(self):
        b = self.make_engine()

        self.assertEqual(
            b.update(True, "Instagram", 0).state,
            BehaviorState.FOCUSED,
        )
        self.assertEqual(
            b.update(True, "Instagram", 30).state,
            BehaviorState.FOCUSED,
        )

    def test_unrelated_activity_under_20_seconds_is_ignored(self):
        b = self.make_engine()

        result = b.update(False, "Spotify", 10)

        self.assertEqual(result.state, BehaviorState.FOCUSED)
        self.assertFalse(result.trigger_intervention)

    def test_unrelated_to_unrelated_does_not_reset_timer(self):
        b = self.make_engine()

        b.update(True, "Instagram", 0)

        b.update(False, "Spotify", 1)
        b.update(False, "WhatsApp", 20)
        result = b.update(False, "VS Code", 46)

        self.assertEqual(result.state, BehaviorState.INTERVENTION)
        self.assertTrue(result.trigger_intervention)

    def test_take_me_back_clears_distraction_history(self):
        b = self.make_engine()

        b.update(True, "Instagram", 0)
        b.update(False, "Spotify", 50)

        result = b.take_me_back(50)

        self.assertEqual(result.state, BehaviorState.FOCUSED)
        self.assertTrue(result.reset_history)
        self.assertIsNone(b.distraction_started)
        self.assertEqual(b.distraction_episodes, [])

    def test_relevant_to_relevant_never_becomes_distraction(self):
        b = self.make_engine()

        b.update(True, "VS Code", 0)
        result = b.update(True, "ML lecture", 30)

        self.assertEqual(result.state, BehaviorState.FOCUSED)
        self.assertFalse(result.trigger_intervention)

    def test_recovery_requires_more_than_10_seconds(self):
        b = self.make_engine()

        b.update(True, "Instagram", 0)
        b.update(False, "Spotify", 30)

        b.update(True, "Instagram", 40)
        self.assertIsNotNone(b.distraction_started)

        result = b.update(True, "Instagram", 49)

        self.assertEqual(result.state, BehaviorState.FOCUSED)
        self.assertIsNotNone(b.distraction_started)

        result = b.update(True, "Instagram", 51)

        self.assertEqual(result.state, BehaviorState.FOCUSED)
        self.assertIsNone(b.distraction_started)
        self.assertEqual(b.distraction_episodes, [])

    def test_continuous_distraction_triggers_at_45_seconds(self):
        b = self.make_engine()

        b.update(True, "Instagram", 0)

        b.update(False, "Spotify", 1)
        b.update(False, "WhatsApp", 20)
        b.update(False, "VS Code", 30)

        result = b.update(False, "ChatGPT", 46)

        self.assertEqual(result.state, BehaviorState.INTERVENTION)
        self.assertTrue(result.trigger_intervention)

    def test_short_switch_does_not_create_recovery(self):
        b = self.make_engine()

        b.update(True, "Instagram", 0)
        b.update(False, "Spotify", 20)
        b.update(True, "Instagram", 22)
        result = b.update(False, "Spotify", 24)

        self.assertEqual(result.state, BehaviorState.FOCUSED)
        self.assertFalse(result.trigger_intervention)

    def test_repeated_distraction_sessions_trigger_at_60_seconds(self):
        b = self.make_engine()

        # First distraction session: 30 seconds.
        b.update(True, "Instagram", 0)
        b.update(False, "Spotify", 1)
        b.update(False, "Spotify", 31)

        # Brief relevant switch: <10 seconds.
        # Distraction history must survive.
        b.update(True, "Instagram", 32)
        b.update(True, "Instagram", 38)

        # Second distraction session: 31 seconds.
        # Total distraction = 30 + 31 = 61 seconds.
        b.update(False, "WhatsApp", 39)
        result = b.update(False, "WhatsApp", 70)

        self.assertEqual(result.state, BehaviorState.INTERVENTION)
        self.assertTrue(result.trigger_intervention)

    def test_working_enters_cooldown(self):
        b = self.make_engine()

        b.update(False, "Spotify", 0)

        result = b.acknowledge_working(50)

        self.assertEqual(result.state, BehaviorState.COOLDOWN)
        self.assertTrue(result.reset_history)

        result = b.update(False, "Spotify", 100)

        self.assertEqual(result.state, BehaviorState.COOLDOWN)
        self.assertFalse(result.trigger_intervention)

    def test_break_silences_intervention(self):
        b = self.make_engine()

        result = b.take_break(0)

        self.assertEqual(result.state, BehaviorState.BREAK)

        result = b.update(False, "Spotify", 300)

        self.assertEqual(result.state, BehaviorState.BREAK)
        self.assertFalse(result.trigger_intervention)


if __name__ == "__main__":
    unittest.main(verbosity=2)