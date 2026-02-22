"""
Self-Play Training Demo.

Shows how to use the training module to improve an agent
through self-play and pool training.
"""

from lisaloop.training import SelfPlayTrainer, TrainingConfig
from lisaloop.agents import LisaAgent, TAGAgent, LAGAgent, GTOApproxAgent


def main():
    # ── Self-Play Training ───────────────────────────
    trainer = SelfPlayTrainer(TrainingConfig(
        epochs=5,
        hands_per_epoch=3000,
        seed=42,
    ))

    print("\n  Part 1: Self-Play (Lisa vs Lisa)")
    results = trainer.train(LisaAgent(seed=42))

    # ── Pool Training ────────────────────────────────
    print("\n  Part 2: Pool Training (Lisa vs everyone)")
    pool_trainer = SelfPlayTrainer(TrainingConfig(
        epochs=5,
        hands_per_epoch=3000,
        table_size=4,
        seed=42,
    ))

    pool_results = pool_trainer.train_against_pool(
        hero=LisaAgent(seed=42),
        opponents=[TAGAgent(seed=42), LAGAgent(seed=42), GTOApproxAgent(seed=42)],
    )

    print("  Done!")


if __name__ == "__main__":
    main()
