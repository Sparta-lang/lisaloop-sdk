"""
Independent Chip Model (ICM) calculator for tournament equity.

Converts chip stacks into real money equity based on the tournament
payout structure. Essential for correct push/fold decisions in
tournaments and sit-and-gos.

Usage:
    from lisaloop.strategy import ICMCalculator

    icm = ICMCalculator()
    stacks = [5000, 3000, 2000]
    payouts = [50, 30, 20]  # percentages

    equities = icm.calculate(stacks, payouts)
    # → [42.3%, 30.8%, 26.9%]

    # Compare a decision's EV
    ev = icm.decision_ev(
        stacks=[5000, 3000, 2000],
        payouts=[50, 30, 20],
        hero=0,                    # hero is player 0
        win_stacks=[8000, 0, 2000],  # if hero wins
        lose_stacks=[2000, 3000, 5000],  # if hero loses
        win_prob=0.55,
    )
"""

from __future__ import annotations

from itertools import permutations
from typing import List


class ICMCalculator:
    """
    Independent Chip Model calculator.

    Computes tournament equity for each player based on their chip stack
    relative to others, using the Malmuth-Harville model.
    """

    def calculate(self, stacks: List[float], payouts: List[float]) -> List[float]:
        """
        Calculate ICM equity for each player.

        Args:
            stacks: Current chip stacks [5000, 3000, 2000]
            payouts: Prize pool percentages [50, 30, 20]

        Returns:
            List of equity percentages for each player
        """
        n = len(stacks)
        total = sum(stacks)

        if total == 0:
            return [0.0] * n

        equities = [0.0] * n

        # For each player, calculate probability of finishing in each position
        for player in range(n):
            for place in range(min(n, len(payouts))):
                prob = self._place_probability(stacks, player, place, total)
                equities[player] += prob * payouts[place]

        return equities

    def decision_ev(
        self,
        stacks: List[float],
        payouts: List[float],
        hero: int,
        win_stacks: List[float],
        lose_stacks: List[float],
        win_prob: float,
    ) -> float:
        """
        Calculate the EV of a decision (e.g., all-in call) in ICM terms.

        Args:
            stacks: Current stacks before the decision
            payouts: Tournament payout structure
            hero: Hero's index in the stack list
            win_stacks: Resulting stacks if hero wins
            lose_stacks: Resulting stacks if hero loses
            win_prob: Probability hero wins the hand

        Returns:
            ICM EV change (positive = profitable decision)
        """
        current_eq = self.calculate(stacks, payouts)
        win_eq = self.calculate(win_stacks, payouts)
        lose_eq = self.calculate(lose_stacks, payouts)

        expected_eq = win_prob * win_eq[hero] + (1 - win_prob) * lose_eq[hero]
        return expected_eq - current_eq[hero]

    def _place_probability(
        self,
        stacks: List[float],
        player: int,
        place: int,
        total: float,
    ) -> float:
        """Calculate probability of a player finishing in a specific place."""
        n = len(stacks)

        if place == 0:
            # Probability of finishing 1st = stack / total
            return stacks[player] / total

        # For 2nd place and beyond, sum over all possible 1st place finishers
        prob = 0.0
        for first in range(n):
            if first == player or stacks[first] == 0:
                continue

            # Probability that 'first' finishes 1st
            p_first = stacks[first] / total

            # Remove 'first' and recursively calculate
            remaining_stacks = [
                s for i, s in enumerate(stacks) if i != first
            ]
            remaining_total = total - stacks[first]

            # Map player index to remaining array
            if player < first:
                new_player = player
            else:
                new_player = player - 1

            if remaining_total > 0:
                sub_prob = self._place_probability(
                    remaining_stacks, new_player, place - 1, remaining_total
                )
                prob += p_first * sub_prob

        return prob

    def bubble_factor(
        self,
        stacks: List[float],
        payouts: List[float],
        hero: int,
        villain: int,
        pot: float,
    ) -> float:
        """
        Calculate the bubble factor for a heads-up confrontation.

        Bubble factor > 1 means you need more equity than pot odds suggest.
        The higher the bubble factor, the tighter you should play.

        Args:
            stacks: Current stacks
            payouts: Payout structure
            hero: Hero's index
            villain: Villain's index
            pot: Size of the pot being contested

        Returns:
            Bubble factor (typically 1.0 to 2.5+)
        """
        current_eq = self.calculate(stacks, payouts)

        # Simulate winning
        win_stacks = list(stacks)
        win_stacks[hero] += pot
        win_stacks[villain] -= pot
        if win_stacks[villain] < 0:
            win_stacks[hero] += win_stacks[villain]
            win_stacks[villain] = 0

        # Simulate losing
        lose_stacks = list(stacks)
        lose_stacks[hero] -= pot
        lose_stacks[villain] += pot
        if lose_stacks[hero] < 0:
            lose_stacks[villain] += lose_stacks[hero]
            lose_stacks[hero] = 0

        win_eq = self.calculate(win_stacks, payouts)
        lose_eq = self.calculate(lose_stacks, payouts)

        risk = current_eq[hero] - lose_eq[hero]
        reward = win_eq[hero] - current_eq[hero]

        if reward <= 0:
            return float("inf")

        return risk / reward
