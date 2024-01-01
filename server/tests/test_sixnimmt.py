import uuid
from typing import Protocol
from unittest.mock import MagicMock

import pytest
from websockets import WebSocketServerProtocol

from server.sixnimmt.sixnimmt import Board, Card, Player, Position, Session


class PlayerMaker(Protocol):
    def __call__(self, player_id: str | None = None) -> Player:
        ...


@pytest.fixture
def player(make_player: PlayerMaker):
    return make_player()


@pytest.fixture
def make_player() -> PlayerMaker:
    def _make_player(player_id: str | None = None):
        mock_connection = MagicMock(spec=WebSocketServerProtocol)
        mock_connection.id = player_id or str(uuid.uuid4())
        return Player(mock_connection)

    return _make_player


@pytest.fixture
def board():
    board = Board()

    board.board[0].append(Card(5))
    board.board[1].append(Card(34))
    board.board[2].append(Card(72))
    board.board[3].append(Card(90))

    return board


@pytest.fixture
def session():
    session = Session("id")
    return session


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
    - When player plays a card, check that card is removed from hand, and function returns true
    - If player tries to play a card that is not in hand, returns false
    - score
    """

    def test_card_removed_from_hand_when_played(self, player: Player):
        player.hand.add(Card(23))

        result = player.play(Card(23))

        assert len(player.hand) == 0
        assert result is True

    def test_player_plays_invalid_card(self, player: Player):
        result = player.play(Card(1))
        assert result is False

    def test_player_score(self, player: Player):
        player.stack.add(Card(104))
        player.stack.add(Card(34))

        expected_score = Card(104).score + Card(34).score
        score = player.score

        assert score == expected_score


class TestBoard:
    """
    - Given a card, where() should return the right row index to place the card.

    - Given a card, and the card can be placed on the board, place() should return the position and an empty set.
    - Given a card, if the card is placed at len(row) > cols, place() should return the position, and stack.
    - Given a card and row, place() should return the position and stack.
    - Check that board[row] has placed card.
    """

    @pytest.mark.parametrize("card, expected_row", [(33, 0), (35, 1), (100, 3)])
    def test_where_to_place_card(self, board: Board, card: int, expected_row: int):
        assert board.where(Card(card)) == expected_row

    def test_board_place_valid_card(self, board: Board):
        position, stack = board.place(Card(50))

        assert board.board[position.row][position.col] == Card(50)
        assert position == Position(1, 1)
        assert len(stack) == 0

    def test_board_place_at_full_row(self, board: Board):
        for col in range(board.cols):
            board.board[0].append(Card(col + 1))

        card_value = board.cols + 4
        position, stack = board.place(Card(card_value))

        assert board.board[position.row][position.col] == Card(card_value)
        assert position == Position(0, 0)
        assert len(stack) == 5

    def test_board_place_card_and_player_row_selected(self, board: Board):
        expected_stack_length = len(board.board[0])

        position, stack = board.place(Card(1), 0)

        assert board.board[position.row][position.col] == Card(1)
        assert position == Position(0, 0)
        assert len(stack) == expected_stack_length


class TestSessionStart:
    """
    start()
    - If session has less than min players, return false
    - If session has more than max players, return false
    - If any players in session has cards in hand, return false
    - If the session board has any cards, return false
    - If session has already started, returns false
    - If session should start, session will deal cards,
    players should have 10 cards in hand, and board should have 4 rows of cards,
    session started should be true, return true
    """

    def test_start_session_only_when_there_is_min_players(
        self, session: Session, make_player: PlayerMaker
    ):
        assert session.start() is False

        for i in range(session.min_players):
            session.players.add(make_player(str(i)))

        assert session.start() is True


class TestSessionAddAndRemove:
    """
    add()
    - If session has started, return false
    - If session has max players, return false
    - Else session adds player, return true

    remove()
    - If player exists, remove player from session, return true
    - If player doesn't exist, return false
    """

    ...


class TestSessionPlay:
    """
    play()
    - If session is not started, return false
    - If turn has progressed, return false
    - If player has already played a card, return false
    - If player plays smallest card, and there is no smallest card player, smallest card player is player,
    return true
    - If player B plays smallest card, and there is smallest card player, smaller card player is now player B,
    return true
    """

    ...


class TestSessionSelect:
    """
    select()
    - If turn is not ready to progress, return false
    - If player is not smallest card player, return false
    - If player chooses an invalid row, return false
    - If selected row is not empty, return false
    - If given valid row, return true
    """

    ...


class TestSessionProgress:
    """
    progress()
    - If session has not started, return false
    - If session has progressed, return false
    - If not all players have played a card, return false
    - If some players have different number of cards in hand, return false
    - If there is a smallest card player, and said player has not select a row, return false
    - If session should progress, place the cards in the right rows and add stack to players (if applicable),
    cards played should have said cards and their positions, session progressed set to true, return true
    """

    ...


class TestSessionReset:
    """
    reset()
    - If turn has not progressed, return false
    - Reset smallest card player, selected row, cards to play, cards played, and progressed status to default values,
    return true

    should_end
    - If session has not start, return false
    - If there are players that has cards in hand, return false
    - else true
    """

    ...
