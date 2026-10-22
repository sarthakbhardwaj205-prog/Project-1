import unittest

import code1


class TournamentTests(unittest.TestCase):
	def setUp(self):
		code1.TOURNAMENTS.clear()
		self.code, self.alice, self.tournament = code1.create_tournament("Alice")
		self.bob = "bob-player-token"
		self.casey = "casey-player-token"
		self.tournament["players"][self.bob] = "Bob"
		self.tournament["players"][self.casey] = "Casey"
		self.tournament["started"] = True
		code1.tournament_round(self.tournament, list(self.tournament["players"]))
		code1.advance_tournament(self.tournament)

	def win_game(self, winner_id):
		match = next(
			match for match in self.tournament["rounds"][self.tournament["current_round"]]
			if winner_id in match["players"] and match["winner"] is None
		)
		loser_id = next(player for player in match["players"] if player != winner_id)
		if code1.tournament_mark(match, winner_id) == "X":
			moves = (
				(winner_id, 0), (loser_id, 3), (winner_id, 1),
				(loser_id, 4), (winner_id, 2),
			)
		else:
			moves = (
				(loser_id, 3), (winner_id, 0), (loser_id, 4),
				(winner_id, 1), (loser_id, 8), (winner_id, 2),
			)
		for player, index in moves:
			self.assertIsNone(code1.tournament_move(self.tournament, player, index))

	def test_bye_and_match_winner_advance_through_final(self):
		first_round = self.tournament["rounds"][0]
		self.assertTrue(first_round[1]["bye"])
		casey_state = code1.tournament_view(self.tournament, self.casey)
		self.assertIsNone(casey_state["yourMatch"])
		self.assertFalse(casey_state["eliminated"])

		self.win_game(self.alice)
		self.assertEqual(first_round[0]["score"], [1, 0])
		self.win_game(self.alice)
		self.assertEqual(first_round[0]["winner"], self.alice)
		self.assertEqual(self.tournament["current_round"], 1)
		self.assertEqual(self.tournament["rounds"][1][0]["players"], [self.alice, self.casey])
		self.assertTrue(code1.tournament_view(self.tournament, self.bob)["eliminated"])

		self.win_game(self.alice)
		self.win_game(self.alice)
		self.assertEqual(self.tournament["winner"], self.alice)
		self.assertEqual(code1.tournament_view(self.tournament, self.alice)["winner"], "Alice")

	def test_draw_replays_and_alternates_first_mark(self):
		match = self.tournament["rounds"][0][0]
		self.assertEqual(code1.tournament_mark(match, self.alice), "X")
		self.assertEqual(
			code1.tournament_move(self.tournament, self.bob, 0),
			"It is the other player's turn",
		)
		draw_squares = (0, 1, 2, 3, 4, 6, 5, 8, 7)
		for turn, index in enumerate(draw_squares):
			mark = "X" if turn % 2 == 0 else "O"
			player = next(
				player for player in match["players"]
				if code1.tournament_mark(match, player) == mark
			)
			self.assertIsNone(code1.tournament_move(self.tournament, player, index))

		self.assertEqual(match["last_result"], "draw")
		self.assertEqual(match["game_number"], 2)
		self.assertEqual(match["board"], [""] * 9)
		self.assertEqual(match["score"], [0, 0])
		self.assertEqual(code1.tournament_mark(match, self.alice), "O")


if __name__ == "__main__":
	unittest.main()
