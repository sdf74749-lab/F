using System;
using System.Collections.Generic;
using System.Linq;

namespace P2PPrototype
{
    public sealed class HostMigrationManager
    {
        private readonly List<PeerState> _peers = new();

        public string? CurrentHostId { get; private set; }

        public string? ShadowHostId { get; private set; }

        public void UpdatePeers(IEnumerable<PeerState> peers)
        {
            _peers.Clear();
            _peers.AddRange(peers);

            if (CurrentHostId == null || !_peers.Any(p => p.PeerId == CurrentHostId))
            {
                CurrentHostId = ElectRankedHosts().FirstOrDefault();
            }

            ShadowHostId = ElectRankedHosts()
                .Where(id => id != CurrentHostId)
                .FirstOrDefault();
        }

        public string? OnPeerDisconnected(string peerId)
        {
            _peers.RemoveAll(p => p.PeerId == peerId);

            if (CurrentHostId == peerId)
            {
                CurrentHostId = ShadowHostId ?? ElectRankedHosts().FirstOrDefault();
            }

            ShadowHostId = ElectRankedHosts()
                .Where(id => id != CurrentHostId)
                .FirstOrDefault();

            return CurrentHostId;
        }

        public IReadOnlyList<string> GetHostPriorityOrder()
        {
            return ElectRankedHosts().ToList();
        }

        private IEnumerable<string> ElectRankedHosts()
        {
            return _peers
                .OrderByDescending(p => p.NetworkScore)
                .ThenByDescending(p => p.BatteryLevel)
                .ThenByDescending(p => p.SyncFreshness)
                .ThenBy(p => p.JoinOrder)
                .Select(p => p.PeerId);
        }
    }

    public sealed record PeerState(
        string PeerId,
        int NetworkScore,
        int BatteryLevel,
        int SyncFreshness,
        int JoinOrder
    );
}
