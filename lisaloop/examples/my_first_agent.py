"""
Example: Your First Lisa Loop Agent

This is a starter template for building a custom poker agent.
Modify the decide() method to implement your strategy.

Run it:
    lisaloop quickplay --agent examples/my_first_agent.py --hands 5000
    lisaloop benchmark examples/my_first_agent.py

Or use it in code:
    from lisaloop import Arena, ArenaConfig
    from my_first_agent import MyAgent

    arena = Arena(ArenaConfig(hands=5000))
    arena.register(MyAgent())
    arena.register(LisaAgent())
    arena.run()
"""

from lisaloop import Agent, GameState, Action, ActionType, Street


class MyAgent(Agent):
    """
    Your custom poker agent.

    This example plays a simple strategy:
    - Preflop: play top 30% of hands
    - Postflop: bet with pairs or better, check/fold without
    - Adjust these to beat the built-in agents!

    Hints:
    - state.my_hand gives you your hole cards
    - state.board gives you community cards
    - state.pot.total gives you the pot size
    - state.pot_odds gives you pot odds as a ratio
    - state.position gives you position (0=SB, higher=later)
    - state.valid_actions lists all legal actions
    - state.street tells you PREFLOP, FLOP, TURN, or RIVER
    """

    name = "MyFirstAgent"
    version = "1.0"
    author = "Hackathon Hacker"

    def decide(self, state: GameState) -> Action:
        if state.street == Street.PREFLOP:
            return self.preflop_strategy(state)
        return self.postflop_strategy(state)

    def preflop_strategy(self, state: GameState) -> Action:
        r1 = state.my_hand.cards[0].rank.value
        r2 = state.my_hand.cards[1].rank.value
        high = max(r1, r2)
        low = min(r1, r2)
        is_pair = r1 == r2
        is_suited = state.my_hand.is_suited

        # Calculate a simple hand score
        score = high + low
        if is_pair:
            score += 10
        if is_suited:
            score += 2
        if abs(r1 - r2) <= 2:
            score += 1

        # Play top ~30% of hands
        if score >= 20:
            # Raise with strong hands
            for action in state.valid_actions:
                if action.type in (ActionType.RAISE, ActionType.BET):
                    size = min(state.big_blind * 2.5, action.max_raise)
                    return Action.raise_to(size)
            return Action.call(state.current_bet)

        # Check if free, otherwise fold
        if state.can_check():
            return Action.check()
        return Action.fold()

    def postflop_strategy(self, state: GameState) -> Action:
        has_pair = self.check_pair(state)

        if has_pair:
            # Bet ~60% pot with a made hand
            if state.can_check():
                for action in state.valid_actions:
                    if action.type == ActionType.BET:
                        size = min(state.pot.total * 0.6, action.max_raise)
                        return Action.bet(max(size, action.min_raise))

            # Call if facing a bet
            return Action.call(state.current_bet)

        # No hand — check or fold
        if state.can_check():
            return Action.check()

        # Call if pot odds are good (getting >3:1)
        if state.pot_odds < 0.25:
            return Action.call(state.current_bet)

        return Action.fold()

    def check_pair(self, state: GameState) -> bool:
        """Check if we have at least a pair with the board."""
        if not state.board:
            return state.my_hand.is_pair

        my_ranks = {c.rank for c in state.my_hand.cards}
        board_ranks = {c.rank for c in state.board}

        # Paired with board
        if my_ranks & board_ranks:
            return True

        # Pocket pair
        if state.my_hand.is_pair:
            return True

        return False
