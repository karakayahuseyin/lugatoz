# -*- coding: utf-8 -*-
import random
import re
import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .curriculum import get_topic_info


def turkish_lower(text: str) -> str:
    """Convert text to lowercase with proper Turkish character handling"""
    turkish_map = {
        'İ': 'i',   # Turkish dotted I
        'I': 'ı',   # Turkish dotless I
        'Ş': 'ş',
        'Ğ': 'ğ',
        'Ü': 'ü',
        'Ö': 'ö',
        'Ç': 'ç',
    }

    result = []
    for char in text:
        if char == '\u0307':  # Strip combining dot above (NFD artifacts)
            continue
        if char in turkish_map:
            result.append(turkish_map[char])
        else:
            result.append(char.lower())

    return ''.join(result)


def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison"""
    if not answer:
        return ""
    collapsed = " ".join(answer.strip().split())
    return turkish_lower(collapsed)


def parse_answer_list(raw_answers: Optional[str]) -> List[str]:
    """Parse comma/semicolon/newline separated answers into normalized non-empty strings"""
    if not raw_answers:
        return []
    parts = re.split(r'[,;\n]+', raw_answers)
    return [normalize_answer(p) for p in parts if p and p.strip()]


def check_fake_answer_disallowed(
    user_answer: str,
    correct_answer: str,
    unacceptable_answers: Optional[str] = None
) -> Optional[str]:
    """Return rejection reason if fake answer matches correct answer or disallowed list."""
    normalized_user = normalize_answer(user_answer)
    if not normalized_user:
        return None

    if normalized_user == normalize_answer(correct_answer):
        return "correct_answer"

    if normalized_user in parse_answer_list(unacceptable_answers):
        return "unacceptable_answer"

    return None


def check_answer(user_answer: str, correct_answer: str, acceptable_answers: Optional[str] = None) -> bool:
    """Check if user answer matches the exact correct answer (or optional alias list)"""
    normalized_user = normalize_answer(user_answer)
    if not normalized_user:
        return False

    if normalized_user == normalize_answer(correct_answer):
        return True

    if acceptable_answers:
        return normalized_user in parse_answer_list(acceptable_answers)

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
    color: str = "blue"  # Player color: blue, red, orange, green
    user_id: Optional[int] = None  # Link to User account
    is_connected: bool = True  # Connection status for reconnection
    submitted_answer: Optional[str] = None
    voted_answer: Optional[str] = None
    final_answers: Dict[int, str] = field(default_factory=dict)
    final_submitted: bool = False
    submit_time: Optional[float] = None  # Time when submitted fake answer
    vote_time: Optional[float] = None  # Time when voted


@dataclass
class Round:
    """Game round data class"""
    question_id: int
    question_text: str
    correct_answer: str
    unacceptable_answers: Optional[str] = None
    fake_answers: Dict[str, str] = field(default_factory=dict)  # player_id -> fake_answer
    votes: Dict[str, str] = field(default_factory=dict)  # player_id -> chosen_answer
    all_options: List[str] = field(default_factory=list)
    start_time: Optional[float] = None  # Round start time
    voting_start_time: Optional[float] = None  # Voting phase start time
    # Emoji reactions: answer -> {player_id -> {emoji, player_name}}
    reactions: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)


class GameRoom:
    """Game room management class"""

    def __init__(self, room_code: str, max_players: int = 4):
        self.room_code = room_code
        self.max_players = max_players
        self.players: Dict[str, Player] = {}
        self.phase = GamePhase.WAITING
        self.current_round = 0
        self.default_max_rounds = 10
        self.max_rounds = 10
        self.rounds: List[Round] = []
        self.questions: List[Dict] = []
        self.grade: Optional[str] = None
        self.theme: Optional[str] = None
        self.created_at = time.time()
        self.final_test_start_time: Optional[float] = None
        self.final_test_duration = 120  # 120 seconds for concept matching activity
        self.final_test_questions: List[Dict] = []
        self.final_test_concepts: List[Dict] = []
        self.final_results_shown: bool = False
        self._lock = threading.Lock()  # Lock for thread-safe operations

    def set_topic(self, grade: Optional[str], theme: Optional[str]):
        """Set grade and theme for this room"""
        self.grade = grade
        self.theme = theme

    def get_topic_info(self) -> Optional[Dict]:
        """Return structured topic metadata for this room"""
        return get_topic_info(self.grade, self.theme)

    def add_player(self, socket_id: str, name: str) -> bool:
        """Add player"""
        if len(self.players) >= self.max_players:
            return False

        # Assign colors cyclically: blue, red, orange, green
        colors = ["blue", "red", "orange", "green"]
        used_colors = {p.color for p in self.players.values()}
        available_colors = [c for c in colors if c not in used_colors]
        player_color = available_colors[0] if available_colors else colors[len(self.players) % len(colors)]

        is_host = len(self.players) == 0
        self.players[socket_id] = Player(
            socket_id=socket_id,
            name=name,
            is_host=is_host,
            color=player_color
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

    def start_game(self, questions: List[Dict]) -> bool:
        """Start game using ONLY the provided topic-filtered questions"""
        if len(self.players) < 2 or not questions:
            return False

        count = min(self.default_max_rounds, len(questions))
        self.questions = random.sample(questions, count)
        self.max_rounds = len(self.questions)
        self.rounds = []
        self.final_test_questions = []
        self.final_test_concepts = []
        self.final_results_shown = False
        self.current_round = 0

        for player in self.players.values():
            player.score = 0
            player.submitted_answer = None
            player.voted_answer = None
            player.final_answers = {}
            player.final_submitted = False
            player.submit_time = None
            player.vote_time = None

        self.phase = GamePhase.SUBMITTING_FAKE
        self._start_new_round()
        return True

    def _start_new_round(self):
        """Start new round"""
        if self.current_round >= len(self.questions):
            self.prepare_final_matching()
            return

        question = self.questions[self.current_round]
        unacceptable = question.get('unacceptable_answers')
        if unacceptable is None:
            unacceptable = question.get('acceptable_answers')

        self.rounds.append(Round(
            question_id=question['id'],
            question_text=question['question_text'],
            correct_answer=question['correct_answer'],
            unacceptable_answers=unacceptable,
            start_time=time.time()
        ))

        # Reset player answers and times
        for player in self.players.values():
            player.submitted_answer = None
            player.voted_answer = None
            player.submit_time = None
            player.vote_time = None

        self.phase = GamePhase.SUBMITTING_FAKE

    def prepare_final_matching(self) -> Dict:
        """Prepare end-of-game concept matching activity from questions played in this game"""
        # Deduplicate by normalized correct_answer so every concept uniquely matches one question
        unique_questions: List[Dict] = []
        seen_answers = set()
        for q in self.questions:
            norm = normalize_answer(q['correct_answer'])
            if norm and norm not in seen_answers:
                seen_answers.add(norm)
                unique_questions.append(q)

        # Fallback if somehow empty
        if not unique_questions:
            unique_questions = list(self.questions)

        # Shuffle question order for the matching activity so players recall rather than memorize order
        matching_questions = list(unique_questions)
        random.shuffle(matching_questions)
        self.final_test_questions = matching_questions

        # Build shuffled concept list (independent order from questions)
        concept_texts = [q['correct_answer'] for q in matching_questions]
        shuffled_texts = list(concept_texts)
        if len(shuffled_texts) > 1:
            for _ in range(10):
                random.shuffle(shuffled_texts)
                if shuffled_texts != concept_texts:
                    break

        # Assign opaque IDs AFTER shuffling so indices cannot be guessed
        self.final_test_concepts = [
            {'id': f'concept_{i}', 'text': text}
            for i, text in enumerate(shuffled_texts)
        ]

        for player in self.players.values():
            player.final_answers = {}
            player.final_submitted = False

        self.final_results_shown = False
        self.final_test_start_time = time.time()
        self.phase = GamePhase.FINAL_TEST

        return self.get_final_matching_payload()

    def get_final_matching_payload(self) -> Dict:
        """Return frontend payload for the concept matching phase"""
        return {
            'questions': [
                {
                    'index': i,
                    'question_text': q['question_text']
                }
                for i, q in enumerate(self.final_test_questions)
            ],
            'concepts': self.final_test_concepts,
            'duration': self.final_test_duration,
            'topic': self.get_topic_info()
        }

    def submit_fake_answer(self, socket_id: str, fake_answer: str) -> Tuple[bool, Optional[str]]:
        """Submit fake answer. Returns (success, rejection_reason)."""
        with self._lock:
            if self.phase != GamePhase.SUBMITTING_FAKE:
                return False, "wrong_phase"

            if socket_id not in self.players:
                return False, "not_in_room"

            current_round = self.rounds[self.current_round]

            # Prevent double submission
            if socket_id in current_round.fake_answers:
                return False, "already_submitted"

            normalized_answer = normalize_answer(fake_answer)

            # Empty answer (timeout penalty)
            if not normalized_answer:
                submit_time = time.time()
                player = self.players[socket_id]
                player.submitted_answer = ""
                player.submit_time = submit_time
                player.score -= 100

                current_round.fake_answers[socket_id] = ""

                if len(current_round.fake_answers) == len(self.players):
                    self._prepare_voting()

                return True, None

            # Reject correct answer or disallowed answers ("Kabul Edilmeyecek Yanıtlar")
            disallowed_reason = check_fake_answer_disallowed(
                fake_answer,
                current_round.correct_answer,
                current_round.unacceptable_answers
            )
            if disallowed_reason:
                return False, disallowed_reason

            # Reject duplicate fake answer
            existing_answers = [normalize_answer(ans) for ans in current_round.fake_answers.values() if ans]
            if normalized_answer in existing_answers:
                return False, "duplicate_answer"

            submit_time = time.time()
            time_taken = submit_time - current_round.start_time

            current_round.fake_answers[socket_id] = normalized_answer
            player = self.players[socket_id]
            player.submitted_answer = normalized_answer
            player.submit_time = submit_time

            if time_taken > 20:
                player.score -= 100

            if len(current_round.fake_answers) == len(self.players):
                self._prepare_voting()

            return True, None

    def _prepare_voting(self):
        """Prepare voting options"""
        current_round = self.rounds[self.current_round]

        fake_answers_list = [ans for ans in current_round.fake_answers.values() if ans]
        all_options = fake_answers_list + [normalize_answer(current_round.correct_answer)]
        random.shuffle(all_options)

        current_round.all_options = all_options
        current_round.voting_start_time = time.time()
        self.phase = GamePhase.VOTING

    def submit_vote(self, socket_id: str, chosen_answer: str) -> bool:
        """Submit vote"""
        with self._lock:
            if self.phase != GamePhase.VOTING:
                return False

            if socket_id not in self.players:
                return False

            current_round = self.rounds[self.current_round]
            if socket_id in current_round.votes:
                return False

            normalized_choice = normalize_answer(chosen_answer)

            # Empty vote (timeout penalty)
            if not normalized_choice:
                vote_time = time.time()
                current_round.votes[socket_id] = ""
                player = self.players[socket_id]
                player.voted_answer = ""
                player.vote_time = vote_time
                player.score -= 100

                if len(current_round.votes) == len(self.players):
                    self._calculate_scores()
                    self.phase = GamePhase.SHOWING_RESULTS

                return True

            # Prevent voting for own fake answer
            player_fake_answer = current_round.fake_answers.get(socket_id)
            if player_fake_answer and normalized_choice == player_fake_answer:
                return False

            vote_time = time.time()
            time_taken = vote_time - current_round.voting_start_time

            current_round.votes[socket_id] = normalized_choice
            player = self.players[socket_id]
            player.voted_answer = normalized_choice
            player.vote_time = vote_time

            if time_taken > 10:
                player.score -= 100

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
                if voted == normalized_correct:
                    player.score += 1000
                else:
                    player.score -= 500

            fake_answer = current_round.fake_answers.get(player_id)
            if fake_answer:
                votes_for_fake = sum(1 for v in current_round.votes.values() if v == fake_answer)
                player.score += votes_for_fake * 500

    def next_round(self):
        """Move to next round or transition to final matching activity"""
        self.current_round += 1

        if self.current_round >= len(self.questions):
            self.prepare_final_matching()
        else:
            self._start_new_round()

    def submit_final_answer(self, socket_id: str, question_index: int, answer: str) -> bool:
        """Submit a single final answer (legacy support)"""
        with self._lock:
            if self.phase != GamePhase.FINAL_TEST:
                return False

            if socket_id not in self.players:
                return False

            self.players[socket_id].final_answers[int(question_index)] = answer
            return True

    def submit_final_matches(self, socket_id: str, matches: Dict) -> bool:
        """Submit all concept-to-question matches atomically for a player"""
        with self._lock:
            if self.phase != GamePhase.FINAL_TEST:
                return False

            if socket_id not in self.players:
                return False

            player = self.players[socket_id]
            if player.final_submitted:
                return True

            cleaned: Dict[int, str] = {}
            total = len(self.final_test_questions)
            if isinstance(matches, dict):
                for raw_idx, concept_text in matches.items():
                    try:
                        idx = int(raw_idx)
                    except (TypeError, ValueError):
                        continue
                    if 0 <= idx < total:
                        cleaned[idx] = str(concept_text).strip() if concept_text is not None else ""

            player.final_answers = cleaned
            player.final_submitted = True
            return True

    def all_players_submitted_final(self) -> bool:
        """Check if every player has completed the final matching activity"""
        if not self.players:
            return False
        return all(player.final_submitted for player in self.players.values())

    def get_final_submission_counts(self) -> Tuple[int, int]:
        """Return (submitted_count, total_players)"""
        submitted = sum(1 for p in self.players.values() if p.final_submitted)
        return submitted, len(self.players)

    def add_reaction(self, player_id: str, answer: str, emoji: str) -> bool:
        """Add emoji reaction to a player"""
        if self.phase != GamePhase.SHOWING_RESULTS:
            return False

        current_round = self.rounds[self.current_round]
        normalized_answer = normalize_answer(answer)

        if normalized_answer not in current_round.reactions:
            current_round.reactions[normalized_answer] = {}

        player_name = self.players[player_id].name if player_id in self.players else "Unknown"

        current_round.reactions[normalized_answer][player_id] = {
            "emoji": emoji,
            "player_name": player_name
        }
        return True

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
                'socket_id': player.socket_id,
                'color': player.color,
                'is_host': player.is_host
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
            'grade': self.grade,
            'theme': self.theme,
            'topic': self.get_topic_info(),
            'players': [
                {
                    'socket_id': p.socket_id,
                    'name': p.name,
                    'score': p.score,
                    'is_host': p.is_host,
                    'color': p.color
                }
                for p in self.players.values()
            ]
        }


class GameManager:
    """Manager for multiple fixed game rooms"""

    # 8 fixed rooms with historical scientist/scholar names
    FIXED_ROOMS = [
        {"code": "ALI_KUSCU", "name": "Ali Kuşçu", "description": "Şerhu'r-risâletil-vazi'yye (Astronomi, matematik ve dil bilimleri üzerine öncü bilgin)"},
        {"code": "KARAMANOGLU", "name": "Karamanoğlu Mehmed Bey", "description": "Ferman (1277'de Türkçeyi resmî devlet dili ilan eden tarihî ferman)"},
        {"code": "KASGARLI", "name": "Kâşgarlı Mahmud", "description": "Dîvânu Lugâti't-Türk (Türk dillerinin ilk sözlüğü ve ansiklopedik eseri)"},
        {"code": "YUSUF_HACIB", "name": "Yusuf Has Hâcib", "description": "Kutadgu Bilig (Türkçe yazılmış ilk siyasetname ve didaktik eser)"},
        {"code": "YUKNEKI", "name": "Edib Ahmed Yüknekî", "description": "Atebetü'l-Hakayık (Ahlak ve öğüt içerikli didaktik eser)"},
        {"code": "YUNUS_EMRE", "name": "Yunus Emre", "description": "Dîvân (Anadolu'da halk diliyle yazılan tasavvuf şiirlerinin zirvesi)"},
        {"code": "YESEVI", "name": "Hoca Ahmed Yesevî", "description": "Dîvân-ı Hikmet (Türk tasavvuf edebiyatının temel eserlerinden)"},
        {"code": "NEVAYI", "name": "Ali Şîr Nevâyî", "description": "Muhâkemetü'l-Lügateyn (Türkçenin Farsçadan üstünlüğünü savunan karşılaştırmalı dil eseri)"},
    ]

    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        for room_info in self.FIXED_ROOMS:
            self.rooms[room_info["code"]] = GameRoom(room_info["code"], max_players=4)

    def get_room(self, room_code: str = None) -> Optional[GameRoom]:
        """Get a specific room by code, or the first room if not specified"""
        if room_code is None:
            return list(self.rooms.values())[0]
        return self.rooms.get(room_code)

    def get_all_rooms(self) -> List[Dict]:
        """Get all rooms with their status and selected topic"""
        rooms_status = []
        for room_info in self.FIXED_ROOMS:
            room = self.rooms[room_info["code"]]
            is_available = (
                room.phase == GamePhase.WAITING and len(room.players) < room.max_players
            )

            current_question = None
            if room.phase in [GamePhase.SUBMITTING_FAKE, GamePhase.VOTING, GamePhase.SHOWING_RESULTS]:
                if room.current_round < len(room.rounds):
                    current_question = room.rounds[room.current_round].question_text

            players_list = []
            for player_id, player in room.players.items():
                players_list.append({
                    "socket_id": player_id,
                    "name": player.name,
                    "score": player.score,
                    "is_host": player.is_host,
                    "is_connected": player.is_connected,
                    "color": player.color
                })

            rooms_status.append({
                "room_code": room_info["code"],
                "name": room_info["name"],
                "description": room_info["description"],
                "players": players_list,
                "max_players": room.max_players,
                "phase": room.phase.value,
                "available": is_available,
                "grade": room.grade,
                "theme": room.theme,
                "topic": room.get_topic_info(),
                "current_round": room.current_round if room.phase != GamePhase.WAITING else None,
                "max_rounds": room.max_rounds if room.phase != GamePhase.WAITING else None,
                "current_question": current_question
            })
        return rooms_status

    def reset_room(self, room_code: str):
        """Reset a specific room for new game (clears topic and players)"""
        if room_code in self.rooms:
            self.rooms[room_code] = GameRoom(room_code, max_players=4)

    def reset_room_keep_players(self, room_code: str) -> Optional[GameRoom]:
        """Reset room but keep the same players, user_ids, colors, host status, and selected topic"""
        if room_code not in self.rooms:
            return None

        room = self.rooms[room_code]

        player_ids = list(room.players.keys())
        player_names = {pid: p.name for pid, p in room.players.items()}
        player_colors = {pid: p.color for pid, p in room.players.items()}
        player_user_ids = {pid: p.user_id for pid, p in room.players.items()}
        host_id = next((pid for pid, p in room.players.items() if p.is_host), None)
        saved_grade = room.grade
        saved_theme = room.theme

        self.reset_room(room_code)

        room = self.rooms[room_code]
        room.set_topic(saved_grade, saved_theme)
        for pid in player_ids:
            room.players[pid] = Player(
                socket_id=pid,
                name=player_names[pid],
                is_host=(pid == host_id),
                color=player_colors[pid],
                user_id=player_user_ids[pid]
            )

        return room


# Global game manager instance
game_manager = GameManager()
