"""Team-based allegiance on the board: different team = enemy, same = ally."""

from engine.board import (
    TEAM_MONSTERS,
    TEAM_PLAYERS,
    Board,
    GridPosition,
    Token,
    is_flanking,
    tokens_in_range,
)
from engine.inference import suggest_targets


def _mon(tid: str, col: int, row: int, team: str = "") -> Token:
    return Token(id=tid, kind="monster", data_ref=tid, pos=GridPosition(col, row), team=team)


def test_default_team_from_kind():
    assert _mon("a", 0, 0).team == TEAM_MONSTERS
    player = Token(id="p", kind="player", data_ref="p", pos=GridPosition(0, 0))
    assert player.team == TEAM_PLAYERS


def test_same_kind_different_team_are_enemies():
    # Two monsters on opposing teams should see each other as targets.
    a = _mon("a", 0, 0, team="A")
    b = _mon("b", 1, 0, team="B")
    board = Board(tokens=[a, b])
    assert tokens_in_range(a, board, 5) == [b]
    assert suggest_targets(a, board, range_ft=10) == [b]


def test_same_team_are_allies_even_if_monsters():
    a = _mon("a", 0, 0, team="A")
    b = _mon("b", 1, 0, team="A")
    board = Board(tokens=[a, b])
    assert tokens_in_range(a, board, 5) == []
    assert suggest_targets(a, board, range_ft=10) == []


def test_monster_allied_to_players_attacks_monsters():
    # A mind-controlled monster placed on the Players team targets its own kind.
    traitor = _mon("traitor", 5, 5, team=TEAM_PLAYERS)
    orc = _mon("orc", 5, 6, team=TEAM_MONSTERS)
    board = Board(tokens=[traitor, orc])
    assert suggest_targets(traitor, board, range_ft=5) == [orc]


def test_flanking_uses_team_not_kind():
    # Two team-A monsters flanking a team-B monster between them.
    left = _mon("L", 4, 5, team="A")
    target = _mon("T", 5, 5, team="B")
    right = _mon("R", 6, 5, team="A")
    board = Board(tokens=[left, target, right], flank_geometry="hard")
    assert is_flanking(left, target, board) is True
