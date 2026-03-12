#!/usr/bin/env python3
"""Runnable prototype app for a serverless P2P Parchis session.

Features:
- 2-4 players
- Host + shadow-host election
- Host migration when host leaves
- Turn timer/AFK autoplay policy
- Deterministic commit-reveal dice flow
"""

from __future__ import annotations

import argparse
import hashlib
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Peer:
    peer_id: str
    network_score: int
    battery_level: int
    sync_freshness: int
    join_order: int


class HostMigrationManager:
    def __init__(self) -> None:
        self._peers: List[Peer] = []
        self.current_host_id: Optional[str] = None
        self.shadow_host_id: Optional[str] = None

    def update_peers(self, peers: List[Peer]) -> None:
        self._peers = list(peers)
        ranked = self._ranked_peer_ids()
        if self.current_host_id not in ranked:
            self.current_host_id = ranked[0] if ranked else None
        self.shadow_host_id = next((pid for pid in ranked if pid != self.current_host_id), None)

    def on_peer_disconnected(self, peer_id: str) -> Optional[str]:
        self._peers = [p for p in self._peers if p.peer_id != peer_id]
        ranked = self._ranked_peer_ids()
        if self.current_host_id == peer_id:
            self.current_host_id = self.shadow_host_id or (ranked[0] if ranked else None)
        if self.current_host_id not in ranked:
            self.current_host_id = ranked[0] if ranked else None
        self.shadow_host_id = next((pid for pid in ranked if pid != self.current_host_id), None)
        return self.current_host_id

    def _ranked_peer_ids(self) -> List[str]:
        peers = sorted(
            self._peers,
            key=lambda p: (-p.network_score, -p.battery_level, -p.sync_freshness, p.join_order),
        )
        return [p.peer_id for p in peers]


class TurnPolicy:
    def __init__(self, turn_time_seconds: int = 20, afk_warnings_before_autoplay: int = 2) -> None:
        if not 5 <= turn_time_seconds <= 60:
            raise ValueError("Turn time must be between 5 and 60 seconds")
        if not 1 <= afk_warnings_before_autoplay <= 5:
            raise ValueError("AFK warning threshold must be between 1 and 5")
        self.turn_time_seconds = turn_time_seconds
        self.afk_warnings_before_autoplay = afk_warnings_before_autoplay

    def should_autoplay(self, afk_warnings: int) -> bool:
        return afk_warnings >= self.afk_warnings_before_autoplay


class CommitRevealDice:
    """Simple deterministic commit-reveal dice generator.

    For each turn, each peer contributes one secret seed.
    - Commit: SHA256(seed)
    - Reveal: seed provided later
    Dice value is derived from SHA256(all_revealed_seeds + turn_index).
    """

    def __init__(self, peer_ids: List[str]) -> None:
        self.peer_ids = list(peer_ids)

    def commit(self, seed: str) -> str:
        return hashlib.sha256(seed.encode()).hexdigest()

    def verify_reveal(self, seed: str, commit_hash: str) -> bool:
        return self.commit(seed) == commit_hash

    def roll(self, revealed_seeds: Dict[str, str], turn_index: int) -> int:
        payload = "|".join(f"{pid}:{revealed_seeds[pid]}" for pid in sorted(revealed_seeds)) + f"|t:{turn_index}"
        digest = hashlib.sha256(payload.encode()).hexdigest()
        return (int(digest[:8], 16) % 6) + 1


class P2PGameApp:
    def __init__(self, peers: List[Peer], policy: TurnPolicy) -> None:
        if not 2 <= len(peers) <= 4:
            raise ValueError("Game supports only 2 to 4 players")
        self.peers = list(peers)
        self.policy = policy
        self.host_manager = HostMigrationManager()
        self.host_manager.update_peers(self.peers)
        self.turn_index = 0
        self.afk_counters: Dict[str, int] = {p.peer_id: 0 for p in self.peers}
        self.dice = CommitRevealDice([p.peer_id for p in self.peers])

    def remove_peer(self, peer_id: str) -> Optional[str]:
        self.peers = [p for p in self.peers if p.peer_id != peer_id]
        self.afk_counters.pop(peer_id, None)
        return self.host_manager.on_peer_disconnected(peer_id)

    def run_turn(self, active_peer_id: str, simulate_afk: bool = False) -> Tuple[int, bool]:
        self.turn_index += 1
        if simulate_afk:
            self.afk_counters[active_peer_id] = self.afk_counters.get(active_peer_id, 0) + 1
        else:
            self.afk_counters[active_peer_id] = 0

        autoplay = self.policy.should_autoplay(self.afk_counters[active_peer_id])
        seeds = {p.peer_id: f"seed-{p.peer_id}-{self.turn_index}" for p in self.peers}
        commits = {pid: self.dice.commit(seed) for pid, seed in seeds.items()}

        for pid, seed in seeds.items():
            if not self.dice.verify_reveal(seed, commits[pid]):
                raise RuntimeError("Commit-reveal mismatch")

        dice_value = self.dice.roll(seeds, self.turn_index)
        return dice_value, autoplay



def _build_demo_peers(count: int) -> List[Peer]:
    rng = random.Random(42)
    peers = []
    for i in range(count):
        peers.append(
            Peer(
                peer_id=f"P{i+1}",
                network_score=rng.randint(60, 100),
                battery_level=rng.randint(35, 100),
                sync_freshness=rng.randint(70, 100),
                join_order=i,
            )
        )
    return peers


def main() -> None:
    parser = argparse.ArgumentParser(description="Run P2P game app demo")
    parser.add_argument("--players", type=int, default=4, help="Number of players (2-4)")
    parser.add_argument("--turns", type=int, default=6, help="How many turns to simulate")
    args = parser.parse_args()

    peers = _build_demo_peers(args.players)
    app = P2PGameApp(peers, TurnPolicy())

    print(f"Players: {[p.peer_id for p in peers]}")
    print(f"Host: {app.host_manager.current_host_id}, Shadow: {app.host_manager.shadow_host_id}")

    for i in range(args.turns):
        active_peer = app.peers[i % len(app.peers)].peer_id
        dice, autoplay = app.run_turn(active_peer, simulate_afk=(i % 3 == 2))
        print(f"Turn {i+1}: player={active_peer}, dice={dice}, autoplay={autoplay}")

        if i == 2 and app.host_manager.current_host_id:
            old_host = app.host_manager.current_host_id
            new_host = app.remove_peer(old_host)
            print(f"Host left: {old_host} -> migrated host: {new_host}, shadow: {app.host_manager.shadow_host_id}")


if __name__ == "__main__":
    main()
