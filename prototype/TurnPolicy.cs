using System;

namespace P2PPrototype
{
    public sealed class TurnPolicy
    {
        public int TurnTimeSeconds { get; }
        public int AfkWarningsBeforeAutoPlay { get; }

        public TurnPolicy(int turnTimeSeconds = 20, int afkWarningsBeforeAutoPlay = 2)
        {
            if (turnTimeSeconds < 5 || turnTimeSeconds > 60)
            {
                throw new ArgumentOutOfRangeException(nameof(turnTimeSeconds), "Turn time must be between 5 and 60 seconds.");
            }

            if (afkWarningsBeforeAutoPlay < 1 || afkWarningsBeforeAutoPlay > 5)
            {
                throw new ArgumentOutOfRangeException(nameof(afkWarningsBeforeAutoPlay), "AFK warning threshold must be between 1 and 5.");
            }

            TurnTimeSeconds = turnTimeSeconds;
            AfkWarningsBeforeAutoPlay = afkWarningsBeforeAutoPlay;
        }

        public bool ShouldAutoPlay(int afkWarnings) => afkWarnings >= AfkWarningsBeforeAutoPlay;
    }
}
