import unittest

from app.p2p_game_app import Peer, P2PGameApp, TurnPolicy


class TestP2PGameApp(unittest.TestCase):
    def setUp(self):
        self.peers = [
            Peer("A", 90, 80, 90, 0),
            Peer("B", 88, 85, 95, 1),
            Peer("C", 70, 70, 80, 2),
            Peer("D", 65, 90, 85, 3),
        ]

    def test_host_migration(self):
        app = P2PGameApp(self.peers, TurnPolicy())
        self.assertEqual(app.host_manager.current_host_id, "A")
        self.assertEqual(app.host_manager.shadow_host_id, "B")

        new_host = app.remove_peer("A")
        self.assertEqual(new_host, "B")
        self.assertEqual(app.host_manager.current_host_id, "B")

    def test_autoplay_trigger(self):
        app = P2PGameApp(self.peers[:2], TurnPolicy(turn_time_seconds=20, afk_warnings_before_autoplay=2))
        _, autoplay1 = app.run_turn("A", simulate_afk=True)
        _, autoplay2 = app.run_turn("A", simulate_afk=True)
        self.assertFalse(autoplay1)
        self.assertTrue(autoplay2)

    def test_dice_range(self):
        app = P2PGameApp(self.peers[:3], TurnPolicy())
        for _ in range(20):
            dice, _ = app.run_turn("A", simulate_afk=False)
            self.assertGreaterEqual(dice, 1)
            self.assertLessEqual(dice, 6)


if __name__ == "__main__":
    unittest.main()
