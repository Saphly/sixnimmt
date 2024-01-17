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
def board() -> Board:
    board = Board()

    board.board[0].append(Card(5))
    board.board[1].append(Card(34))
    board.board[2].append(Card(72))
    board.board[3].append(Card(90))

    return board


@pytest.fixture
def session() -> Session:
    session = Session("id")
    return session


@pytest.fixture
def session_with_min_players(make_player: PlayerMaker) -> Session:
    session = Session("id")

    for i in range(session.min_players):
        session.players.add(make_player(str(i)))

    return session


@pytest.fixture
def started_session(
    session_with_min_players: Session,
    player_one: Player,
    player_two: Player,
    board: Board,
) -> Session:
    session_with_min_players.start()

    player_one.hand.pop()
    player_one.hand.add(Card(1))

    player_two.hand.pop()
    player_two.hand.add(Card(2))

    session_with_min_players.board = board

    return session_with_min_players


@pytest.fixture
def player_one(session_with_min_players: Session) -> Player:
    return next(
        player for player in session_with_min_players.players if player.player_id == "0"
    )


@pytest.fixture
def player_two(session_with_min_players: Session) -> Player:
    return next(
        player for player in session_with_min_players.players if player.player_id == "1"
    )


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

    def test_start_session_if_under_max_players(
        self, session: Session, make_player: PlayerMaker
    ):
        for i in range(session.max_players):
            session.players.add(make_player(str(i)))

        session.players.add(make_player("extra"))

        assert session.start() is False

    def test_start_session_if_player_has_hand(
        self, session: Session, make_player: PlayerMaker
    ):
        for i in range(session.min_players):
            new_player = make_player(str(i))
            new_player.hand.add(Card(i + 1))
            session.players.add(new_player)

        assert session.start() is False

    def test_start_session_if_session_board_has_cards(
        self, session_with_min_players: Session, make_player: PlayerMaker
    ):
        session_with_min_players.board.board[0].append(Card(55))
        assert session_with_min_players.start() is False

    def test_start_session_if_session_already_started(
        self, session_with_min_players: Session
    ):
        session_with_min_players.started = True

        assert session_with_min_players.start() is False

    def test_start_session(self, session_with_min_players: Session):
        assert session_with_min_players.start() is True

        for player in session_with_min_players.players:
            assert len(player.hand) == session_with_min_players.cards_per_player

        for row in session_with_min_players.board.board:
            assert len(row) == 1

        assert (
            len(session_with_min_players.board.board)
            == session_with_min_players.board.rows
        )
        assert session_with_min_players.started is True


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

    def test_add_player_after_started(
        self, session_with_min_players: Session, make_player: PlayerMaker
    ):
        session_with_min_players.start()

        assert session_with_min_players.add(make_player("new")) is False

    def test_add_to_max_player_session(
        self, session: Session, make_player: PlayerMaker
    ):
        for i in range(session.max_players):
            session.add(make_player(str(i)))

        assert session.add(make_player("new")) is False

    def test_add_player(self, session: Session, make_player: PlayerMaker):
        assert session.add(make_player("new")) is True

    def test_remove_existing_player(self, session: Session, make_player: PlayerMaker):
        new_player = make_player("new")
        session.add(new_player)

        assert session.remove(new_player) is True

    def test_remove_nonexisting_player(
        self, session_with_min_players: Session, player: Player
    ):
        assert session_with_min_players.remove(player) is False


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

    def test_play_if_session_not_started(
        self, session_with_min_players: Session, player_one: Player
    ):
        assert session_with_min_players.play(player_one, Card(22)) is False

        session_with_min_players.start()
        player_one_card = next(iter(player_one.hand))

        assert session_with_min_players.play(player_one, player_one_card) is True
        assert player_one in session_with_min_players.cards_to_play
        assert session_with_min_players.cards_to_play[player_one] is player_one_card

    def test_play_when_turn_progressed(
        self, session_with_min_players: Session, player_one: Player
    ):
        session_with_min_players.start()
        session_with_min_players.progressed = True

        player_one_card = next(iter(player_one.hand))

        assert session_with_min_players.play(player_one, player_one_card) is False

    def test_play_when_player_already_played_a_card(
        self, session_with_min_players: Session, player_one: Player
    ):
        session_with_min_players.start()

        player_one_card = next(iter(player_one.hand))
        session_with_min_players.play(player_one, player_one_card)
        next_card = next(iter(player_one.hand))

        assert session_with_min_players.play(player_one, next_card) is False

    def test_play_smallest_card_player(
        self, started_session: Session, player_one: Player
    ):
        assert started_session.smallest_card_player is None

        started_session.play(player_one, Card(1))

        assert started_session.smallest_card_player is not None
        assert started_session.smallest_card_player is player_one

    def test_play_new_smallest_card_player(
        self, started_session: Session, player_one: Player, player_two: Player
    ):
        started_session.play(player_two, Card(2))
        assert started_session.smallest_card_player is player_two

        started_session.play(player_one, Card(1))
        assert started_session.smallest_card_player is player_one

    ...


class TestSessionSelectRow:
    """
    select()
    - If turn is not ready to progress, return false
    - If player is not smallest card player, return false
    - If player chooses an invalid row, return false
    - If a row is already selected, return false
    - If given valid row, return true
    """

    def test_select_when_turn_not_progressed(
        self, started_session: Session, player_one: Player
    ):
        assert started_session.select(player_one, 1) is False

    def test_select_if_not_from_smallest_card_player(
        self, started_session: Session, player_one: Player, player_two: Player
    ):
        started_session.play(player_one, Card(1))
        started_session.play(player_two, Card(2))

        assert len(player_one.hand) == len(player_two.hand)
        assert started_session.smallest_card_player is player_one
        assert started_session.selected_row is None

        assert started_session.select(player_two, 1) is False
        assert started_session.select(player_one, 1) is True

    def test_select_invalid_row(
        self, started_session: Session, player_one: Player, player_two: Player
    ):
        started_session.play(player_one, Card(1))
        started_session.play(player_two, Card(2))

        assert started_session.select(player_one, 100) is False

    def test_select_when_already_selected_row(
        self, started_session: Session, player_one: Player, player_two: Player
    ):
        started_session.play(player_one, Card(1))
        started_session.play(player_two, Card(2))

        assert started_session.select(player_one, 2) is True
        assert started_session.select(player_one, 0) is False


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

    def test_progress_when_session_not_started(self, session_with_min_players: Session):
        assert session_with_min_players.progress() is False

    def test_progress_when_session_has_progressed(self, started_session: Session):
        started_session.progressed = True

        assert started_session.progress() is False

    def test_progress_when_not_everyone_played_card(
        self, started_session: Session, player_one: Player
    ):
        started_session.play(player_one, next(iter(player_one.hand)))

        assert started_session.progress() is False

    def test_progress_when_player_has_different_number_in_hand(
        self, started_session: Session, player_one: Player, player_two: Player
    ):
        player_one_card = next(iter(player_one.hand))

        started_session.play(player_one, player_one_card)
        started_session.play(player_two, next(iter(player_two.hand)))

        player_one.hand.add(player_one_card)

        assert started_session.progress() is False

    def test_progress_when_smallest_row_not_selected(
        self, started_session: Session, player_one: Player, player_two: Player
    ):
        started_session.play(player_one, Card(1))
        started_session.play(player_two, Card(2))

        assert started_session.progress() is False

    def test_progress(
        self, started_session: Session, player_one: Player, player_two: Player
    ):
        started_session.play(player_one, Card(1))
        started_session.play(player_two, Card(2))

        started_session.select(player_one, 1)
        assert started_session.progress() is True

        assert len(player_one.stack) == 1
        assert len(player_two.stack) == 0

        assert started_session.cards_played[player_one] == (Card(1), Position(1, 0))
        assert started_session.cards_played[player_two] == (Card(2), Position(1, 1))

        assert started_session.board.board[1] == [Card(1), Card(2)]
        assert started_session.progressed is True

    ...


class TestSessionReset:
    """
    reset()
    - If turn has not progressed, return false
    - Reset smallest card player, selected row, cards to play, cards played, and progressed status to default values,
    return true
    """

    def test_reset_when_not_progressed(self, started_session: Session):
        assert started_session.progressed is False
        assert started_session.reset() is False

    def test_reset(
        self, started_session: Session, player_one: Player, player_two: Player
    ):
        started_session.play(player_one, Card(1))
        started_session.play(player_two, Card(2))

        started_session.select(player_one, 1)
        assert started_session.smallest_card_player is player_one

        started_session.progress()
        assert started_session.progressed is True

        assert started_session.reset() is True
        assert started_session.smallest_card_player is None
        assert started_session.selected_row is None
        assert started_session.cards_to_play == {}
        assert started_session.cards_played == {}
        assert started_session.progressed is False

    ...


class TestSessionShouldEnd:
    """
    should_end
    - If session has not start, return false
    - If there are players that has cards in hand, return false
    - else true
    """

    def test_session_should_end_when_not_started(self, session: Session):
        assert session.started is False
        assert session.should_end is False

    def test_session_should_end_when_players_still_have_cards(
        self, started_session: Session, player_one: Player
    ):
        assert len(player_one.hand) > 0
        assert started_session.should_end is False

    def test_session_should_end(self, started_session: Session):
        for player in started_session.players:
            player.hand = set()

        assert started_session.should_end is True
