"""Tests for card representation and hand evaluation."""

from lisaloop.core.cards import Card, Hand, Deck, HandEvaluator, HandCategory


def test_card_creation():
    card = Card("Ah")
    assert card.rank.value == 14
    assert card.suit.value == 2
    assert repr(card) == "A♥"


def test_card_comparison():
    ace = Card("As")
    king = Card("Ks")
    assert ace > king
    assert not king > ace


def test_hand_creation():
    hand = Hand.from_str("AhKs")
    assert hand.cards[0].rank.value == 14
    assert not hand.is_pair
    assert not hand.is_suited


def test_hand_suited():
    hand = Hand.from_str("AhKh")
    assert hand.is_suited


def test_hand_pair():
    hand = Hand.from_str("AsAh")
    assert hand.is_pair


def test_deck():
    deck = Deck(seed=42)
    deck.shuffle()
    assert deck.remaining == 52
    cards = deck.deal(5)
    assert len(cards) == 5
    assert deck.remaining == 47


def test_evaluator_pair():
    evaluator = HandEvaluator()
    hand = Hand.from_str("AhKs")
    board = [Card("Ad"), Card("7c"), Card("3h"), Card("9s"), Card("2d")]
    result = evaluator.evaluate(hand, board)
    assert result.category == HandCategory.ONE_PAIR


def test_evaluator_flush():
    evaluator = HandEvaluator()
    hand = Hand.from_str("AhKh")
    board = [Card("Qh"), Card("Jh"), Card("2h"), Card("9s"), Card("3d")]
    result = evaluator.evaluate(hand, board)
    assert result.category == HandCategory.FLUSH


def test_evaluator_straight():
    evaluator = HandEvaluator()
    hand = Hand.from_str("5h6s")
    board = [Card("7d"), Card("8c"), Card("9h"), Card("2s"), Card("Kd")]
    result = evaluator.evaluate(hand, board)
    assert result.category == HandCategory.STRAIGHT


def test_evaluator_full_house():
    evaluator = HandEvaluator()
    hand = Hand.from_str("AhAs")
    board = [Card("Ad"), Card("Kc"), Card("Kh"), Card("2s"), Card("3d")]
    result = evaluator.evaluate(hand, board)
    assert result.category == HandCategory.FULL_HOUSE


def test_evaluator_comparison():
    evaluator = HandEvaluator()
    board = [Card("Td"), Card("7c"), Card("3h"), Card("Qs"), Card("2d")]

    hand_a = Hand.from_str("AhAs")  # pair of aces
    hand_b = Hand.from_str("KhKs")  # pair of kings

    rank_a = evaluator.evaluate(hand_a, board)
    rank_b = evaluator.evaluate(hand_b, board)
    assert rank_a > rank_b
