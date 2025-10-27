# -*- coding: utf-8 -*-
import random
import string
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison"""
    return answer.strip().lower()


def check_answer(user_answer: str, correct_answer: str, acceptable_answers: Optional[str] = None) -> bool:
    """Check if user answer is correct"""
    normalized_user = normalize_answer(user_answer)
    normalized_correct = normalize_answer(correct_answer)

    if normalized_user == normalized_correct:
        return True

    # Check acceptable answers
    if acceptable_answers:
        acceptable_list = [normalize_answer(a) for a in acceptable_answers.split(',')]
        return normalized_user in acceptable_list

    return False


class GamePhase(str, Enum):
    """Game phases"""
    WAITING = "waiting"
    SUBMITTING_FAKE = "submitting_fake"
    VOTING = "voting"
    SHOWING_RESULTS = "showing_results"
    FINAL_TEST = "final_test"
    GAME_OVER = "game_over"


@dataclass
class Player:
    """Player data class"""
    socket_id: str
    name: str
    score: int = 0
    is_host: bool = False
    submitted_answer: Optional[str] = None
    voted_answer: Optional[str] = None
    final_answers: Dict[int, str] = field(default_factory=dict)
    submit_time: Optional[float] = None  # Time when submitted fake answer
    vote_time: Optional[float] = None  # Time when voted


@dataclass
class Round:
    """Game round data class"""
    question_id: int
    question_text: str
    correct_answer: str
    acceptable_answers: Optional[str] = None
    fake_answers: Dict[str, str] = field(default_factory=dict)  # player_id -> fake_answer
    votes: Dict[str, str] = field(default_factory=dict)  # player_id -> chosen_answer
    all_options: List[str] = field(default_factory=list)
    start_time: Optional[float] = None  # Round start time
    voting_start_time: Optional[float] = None  # Voting phase start time


class GameRoom:
    """Game room management class"""

    def __init__(self, room_code: str, max_players: int = 4):
        self.room_code = room_code
        self.max_players = max_players
        self.players: Dict[str, Player] = {}
        self.phase = GamePhase.WAITING
        self.current_round = 0
        self.max_rounds = 10
        self.rounds: List[Round] = []
        self.questions: List[Dict] = []
        self.created_at = time.time()
        self.final_test_start_time: Optional[float] = None
        self.final_test_duration = 120  # 120 seconds for final test

    def add_player(self, socket_id: str, name: str) -> bool:
        """Add player"""
        if len(self.players) >= self.max_players:
            return False

        is_host = len(self.players) == 0
        self.players[socket_id] = Player(
            socket_id=socket_id,
            name=name,
            is_host=is_host
        )
        return True

    def remove_player(self, socket_id: str):
        """Remove player"""
        if socket_id in self.players:
            was_host = self.players[socket_id].is_host
            del self.players[socket_id]

            # If host left, assign new host
            if was_host and self.players:
                next_player = next(iter(self.players.values()))
                next_player.is_host = True

    def start_game(self, questions: List[Dict]):
        """Start game"""
        if len(self.players) < 2:
            return False

        self.questions = random.sample(questions, min(self.max_rounds, len(questions)))
        self.phase = GamePhase.SUBMITTING_FAKE
        self.current_round = 0
        self._start_new_round()
        return True

    def _start_new_round(self):
        """Start new round"""
        if self.current_round >= len(self.questions):
            self.phase = GamePhase.FINAL_TEST
            self.final_test_start_time = time.time()
            return

        question = self.questions[self.current_round]
        self.rounds.append(Round(
            question_id=question['id'],
            question_text=question['question_text'],
            correct_answer=question['correct_answer'],
            acceptable_answers=question.get('acceptable_answers'),
            start_time=time.time()
        ))

        # Reset player answers and times
        for player in self.players.values():
            player.submitted_answer = None
            player.voted_answer = None
            player.submit_time = None
            player.vote_time = None

        self.phase = GamePhase.SUBMITTING_FAKE

    def submit_fake_answer(self, socket_id: str, fake_answer: str) -> bool:
        """Submit fake answer"""
        if self.phase != GamePhase.SUBMITTING_FAKE:
            return False

        if socket_id not in self.players:
            return False

        current_round = self.rounds[self.current_round]
        normalized_answer = normalize_answer(fake_answer)

        # If answer is empty (timeout penalty), accept it but don't add to options
        if not normalized_answer:
            submit_time = time.time()
            time_taken = submit_time - current_round.start_time

            player = self.players[socket_id]
            player.submitted_answer = ""
            player.submit_time = submit_time
            player.score -= 100  # Penalty for not submitting

            # Mark as submitted by adding empty string
            current_round.fake_answers[socket_id] = ""

            # If all players submitted, move to voting
            if len(current_round.fake_answers) == len(self.players):
                self._prepare_voting()

            return True

        # Normalize and check if answer is correct (prevent submitting correct answer)
        if check_answer(fake_answer, current_round.correct_answer, current_round.acceptable_answers):
            return False  # Cannot submit correct answer as fake

        # Check if answer already submitted by another player (exclude empty strings)
        existing_answers = [normalize_answer(ans) for ans in current_round.fake_answers.values() if ans]
        if normalized_answer in existing_answers:
            return False  # Cannot submit duplicate answer

        # Check time limit (20 seconds)
        submit_time = time.time()
        time_taken = submit_time - current_round.start_time

        current_round.fake_answers[socket_id] = normalized_answer
        player = self.players[socket_id]
        player.submitted_answer = normalize_answer(fake_answer)
        player.submit_time = submit_time

        # Penalty for taking too long (more than 20 seconds)
        if time_taken > 20:
            player.score -= 100  # -100 points for timeout

        # If all players submitted, move to voting
        if len(current_round.fake_answers) == len(self.players):
            self._prepare_voting()

        return True

    def _prepare_voting(self):
        """Prepare voting options"""
        current_round = self.rounds[self.current_round]

        # Mix all fake answers with correct answer (exclude empty strings)
        fake_answers_list = [ans for ans in current_round.fake_answers.values() if ans]
        all_options = fake_answers_list + [normalize_answer(current_round.correct_answer)]
        random.shuffle(all_options)

        current_round.all_options = all_options
        current_round.voting_start_time = time.time()
        self.phase = GamePhase.VOTING

    def submit_vote(self, socket_id: str, chosen_answer: str) -> bool:
        """Submit vote"""
        if self.phase != GamePhase.VOTING:
            return False

        if socket_id not in self.players:
            return False

        current_round = self.rounds[self.current_round]
        normalized_choice = normalize_answer(chosen_answer)

        # If vote is empty (timeout penalty), accept it
        if not normalized_choice:
            vote_time = time.time()

            current_round.votes[socket_id] = ""
            player = self.players[socket_id]
            player.voted_answer = ""
            player.vote_time = vote_time
            player.score -= 100  # Penalty for not voting

            # If all players voted, show results
            if len(current_round.votes) == len(self.players):
                self._calculate_scores()
                self.phase = GamePhase.SHOWING_RESULTS

            return True

        # Prevent voting for own fake answer
        player_fake_answer = current_round.fake_answers.get(socket_id)
        if player_fake_answer and normalized_choice == player_fake_answer:
            return False  # Cannot vote for own fake answer

        # Check time limit (10 seconds)
        vote_time = time.time()
        time_taken = vote_time - current_round.voting_start_time

        current_round.votes[socket_id] = normalized_choice
        player = self.players[socket_id]
        player.voted_answer = normalized_choice
        player.vote_time = vote_time

        # Penalty for taking too long (more than 10 seconds)
        if time_taken > 10:
            player.score -= 100  # -100 points for timeout

        # If all players voted, show results
        if len(current_round.votes) == len(self.players):
            self._calculate_scores()
            self.phase = GamePhase.SHOWING_RESULTS

        return True

    def _calculate_scores(self):
        """Calculate scores"""
        current_round = self.rounds[self.current_round]
        normalized_correct = normalize_answer(current_round.correct_answer)

        for player_id, player in self.players.items():
            voted = player.voted_answer

            if voted:
                # Correct answer: 1000 points
                if voted == normalized_correct:
                    player.score += 1000
                else:
                    # Wrong answer: -500 points
                    player.score -= 500

            # Others choosing your fake answer: 500 points each
            fake_answer = current_round.fake_answers.get(player_id)
            if fake_answer:
                votes_for_fake = sum(1 for v in current_round.votes.values() if v == fake_answer)
                player.score += votes_for_fake * 500

    def next_round(self):
        """Move to next round"""
        self.current_round += 1

        if self.current_round >= len(self.questions):
            self.phase = GamePhase.FINAL_TEST
        else:
            self._start_new_round()

    def submit_final_answer(self, socket_id: str, question_index: int, answer: str):
        """Submit final test answer"""
        if self.phase != GamePhase.FINAL_TEST:
            return False

        if socket_id not in self.players:
            return False

        self.players[socket_id].final_answers[question_index] = answer
        return True

    def calculate_final_scores(self) -> Dict[str, int]:
        """Calculate final test scores"""
        scores = {}

        for player_id, player in self.players.items():
            correct_count = 0
            for i, question in enumerate(self.questions):
                user_answer = player.final_answers.get(i, "")

                if check_answer(user_answer, question['correct_answer'], question.get('acceptable_answers')):
                    correct_count += 1

            # 500 points per correct answer
            bonus_score = correct_count * 500
            player.score += bonus_score
            scores[player_id] = {
                'correct_count': correct_count,
                'bonus_score': bonus_score,
                'total_score': player.score
            }

        self.phase = GamePhase.GAME_OVER
        return scores

    def get_leaderboard(self) -> List[Dict]:
        """Get leaderboard"""
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: p.score,
            reverse=True
        )

        return [
            {
                'name': player.name,
                'score': player.score,
                'socket_id': player.socket_id
            }
            for player in sorted_players
        ]

    def to_dict(self) -> Dict:
        """Convert room info to dict"""
        return {
            'room_code': self.room_code,
            'phase': self.phase.value,
            'current_round': self.current_round,
            'max_rounds': self.max_rounds,
            'player_count': len(self.players),
            'max_players': self.max_players,
            'players': [
                {
                    'socket_id': p.socket_id,
                    'name': p.name,
                    'score': p.score,
                    'is_host': p.is_host
                }
                for p in self.players.values()
            ]
        }


class GameManager:
    """Manager for multiple fixed game rooms"""

    # 8 fixed rooms with scientist names
    FIXED_ROOMS = [
        {"code": "ALI_KUSCU", "name": "Ali Kuşçu", "description": "Şerhu'r-risâletil-vazi'yye (Arapça dil felsefesi ve mantık bilimleri üzerine önemli bir şerh)"},
        {"code": "KARAMANOGLU", "name": "Karamanoğlu Mehmed Bey", "description": "Ferman (1277'de Türkçeyi resmî devlet dili ilan eden tarihî ferman)"},
        {"code": "KASGARLI", "name": "Kâşgarlı Mahmud", "description": "Dîvânu Lugâti't-Türk (Türk dillerinin ilk sözlüğü ve ansiklopedik eseri)"},
        {"code": "YUSUF_HACIB", "name": "Yusuf Has Hâcib", "description": "Kutadgu Bilig (Türkçe yazılmış ilk siyasetname ve didaktik eser)"},
        {"code": "YUKNEKI", "name": "Edib Ahmed Yüknekî", "description": "Atebetü'l-Hakayık (Ahlak ve öğüt içerikli didaktik eser)"},
        {"code": "YUNUS_EMRE", "name": "Yunus Emre", "description": "Dîvân (Anadolu'da halk diliyle yazılan tasavvuf şiirlerinin zirvesi)"},
        {"code": "YESEVI", "name": "Hoca Ahmed Yesevî", "description": "Dîvân-ı Hikmet (Türk tasavvuf edebiyatının temel eserlerinden)"},
        {"code": "NEVAYI", "name": "Ali Şîr Nevâyî", "description": "Muhâkemetü'l-Lügateyn (Türkçenin Farsçadan üstünlüğünü savunan karşılaştırmalı dil eseri)"},
    ]

    def __init__(self):
        # Create 8 fixed rooms
        self.rooms: Dict[str, GameRoom] = {}
        for room_info in self.FIXED_ROOMS:
            self.rooms[room_info["code"]] = GameRoom(room_info["code"], max_players=4)

    def get_room(self, room_code: str = None) -> GameRoom:
        """Get a specific room by code, or the first room if not specified"""
        if room_code is None:
            # Return first room for backwards compatibility
            return list(self.rooms.values())[0]
        return self.rooms.get(room_code)

    def get_all_rooms(self) -> List[Dict]:
        """Get all rooms with their status"""
        rooms_status = []
        for room_info in self.FIXED_ROOMS:
            room = self.rooms[room_info["code"]]
            rooms_status.append({
                "code": room_info["code"],
                "name": room_info["name"],
                "description": room_info["description"],
                "players": len(room.players),
                "max_players": room.max_players,
                "phase": room.phase.value,
                "available": len(room.players) < room.max_players and room.phase == GamePhase.WAITING
            })
        return rooms_status

    def reset_room(self, room_code: str):
        """Reset a specific room for new game"""
        if room_code in self.rooms:
            self.rooms[room_code] = GameRoom(room_code, max_players=4)


# Global game manager instance
game_manager = GameManager()
