import pytest
from sixnimmt.sixnimmt import Card


class TestCard:
    @pytest.mark.parametrize(
        "card, expected_score", [(55, 7), (22, 5), (50, 3), (15, 2), (104, 1)]
    )
    def test_score(self, card: int, expected_score: int):
        assert Card(card).score == expected_score

    @pytest.mark.parametrize(
        "card, other_card, expected_result",
        [
            (55, 64, True),
            (22, 25, True),
            pytest.param(45, 31, True, marks=pytest.mark.xfail),
        ],
    )
    def test_cards_are_ordered(self, card: int, other_card: int, expected_result: bool):
        assert (Card(card) < Card(other_card)) == expected_result


class TestPlayer:
    """
    - Player should have no hand, and no stack
    - When player plays a card, check that card is removed from hand, and function returns true
    - If player tries to play a card that is not in hand, returns false
    - score
    """

    def test_one(self):
        x = "this"
        assert "h" in x


class TestBoard:
    """
    - Given a card, where() should return the right row index to place the card.

    - Given a card, and the card can be placed on the board, place() should return the position and an empty set.
    - Given a card, if the card is placed at len(row) > cols, place() should return the position, and stack.
    - Given a card and row, place() should return the position and stack.
    - Check that board[row] has placed card.
    """

    def test_two(self):
        x = "hello"
        assert hasattr(x, "check")


class TestSession:
    """
    start() / should_start?
    - If session has less than min players, return false
    - If session has more than max players, return false
    - If any players in session has cards in hand, return false
    - If the session board has any cards, return false
    - If session has already started, returns false
    - If session should start, session will deal cards,
    players should have 10 cards in hand, and board should have 4 rows of cards,
    session started should be true, return true

    add()
    - If session has started, return false
    - If session has max players, return false
    - Else session adds player, return true

    remove()
    - If player exists, remove player from session, return true
    - If player doesn't exist, return false

    play()
    - If session is not started, return false
    - If turn has progressed, return false
    - If player has already played a card, return false
    - If player plays smallest card, and there is no smallest card player, smallest card player is player,
    return true
    - If player B plays smallest card, and there is smallest card player, smaller card player is now player B,
    return true

    select()
    - If turn is not ready to progress, return false
    - If player is not smallest card player, return false
    - If player chooses an invalid row, return false
    - If selected row is not empty, return false
    - If given valid row, return true

    progress() / should_progress?
    - If session has not started, return false
    - If session has progressed, return false
    - If not all players have played a card, return false
    - If some players have different number of cards in hand, return false
    - If there is a smallest card player, and said player has not select a row, return false
    - If session should progress, place the cards in the right rows and add stack to players (if applicable),
    cards played should have said cards and their positions, session progressed set to true, return true

    reset()
    - If turn has not progressed, return false
    - Reset smallest card player, selected row, cards to play, cards played, and progressed status to default values,
    return true

    should_end
    - If session has not start, return false
    - If there are players that has cards in hand, return false
    - else true
    """

    def test_three(self):
        x = "lol :')"
        assert hasattr(x, "lol :')")
