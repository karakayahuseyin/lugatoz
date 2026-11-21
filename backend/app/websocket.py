# -*- coding: utf-8 -*-
import socketio
import asyncio
from typing import Dict, List
from datetime import datetime

from .game_manager import game_manager, GamePhase, normalize_answer
from .curriculum import validate_grade_and_theme, grade_has_themes, get_topic_info
from .database import SessionLocal
from .models import Question, GameStats, QuestionStats
from .auth import (
    create_user,
    get_user_by_id,
    get_user_by_username,
    update_username,
    update_last_login,
    get_leaderboard,
    get_user_stats,
    update_user_stats_after_game,
)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

# Track which room each socket is in
socket_rooms: Dict[str, str] = {}  # socket_id -> room_code

# Track user_id for each socket
socket_users: Dict[str, int] = {}  # socket_id -> user_id

# Track active tasks per room to prevent duplicates
room_tasks: Dict[str, Dict[str, asyncio.Task]] = {}  # room_code -> {task_name -> task}


def cancel_room_task(room_code: str, task_name: str):
    """Cancel a specific task for a room if it exists"""
    if room_code in room_tasks and task_name in room_tasks[room_code]:
        task = room_tasks[room_code][task_name]
        if not task.done():
            task.cancel()
        del room_tasks[room_code][task_name]


def create_room_task(room_code: str, task_name: str, coro):
    """Create a tracked task for a room, cancelling any existing task with same name"""
    cancel_room_task(room_code, task_name)

    if room_code not in room_tasks:
        room_tasks[room_code] = {}

    task = asyncio.create_task(coro)
    room_tasks[room_code][task_name] = task
    return task


def cancel_all_room_tasks(room_code: str):
    """Cancel all tasks for a room"""
    if room_code in room_tasks:
        for task_name in list(room_tasks[room_code].keys()):
            cancel_room_task(room_code, task_name)
        del room_tasks[room_code]


def get_player_room(sid):
    """Get the room for a given socket ID"""
    room_code = socket_rooms.get(sid)
    if room_code:
        return game_manager.get_room(room_code)
    return None


def fetch_questions_for_room(room) -> List[Dict]:
    """Fetch ONLY active questions strictly belonging to the room's selected grade and theme."""
    if not room or not room.grade:
        return []

    db = SessionLocal()
    try:
        query = db.query(Question).filter(
            Question.is_active == True,
            Question.grade == room.grade
        )

        if grade_has_themes(room.grade):
            if not room.theme:
                return []
            query = query.filter(Question.theme == room.theme)
        else:
            # Dünyanın Enleri: yalnızca temasız bu bölüme ait sorular
            query = query.filter((Question.theme.is_(None)) | (Question.theme == ""))

        questions_db = query.all()
        return [
            {
                'id': q.id,
                'question_text': q.question_text,
                'correct_answer': q.correct_answer,
                'unacceptable_answers': (
                    q.unacceptable_answers
                    if q.unacceptable_answers is not None
                    else q.acceptable_answers
                )
            }
            for q in questions_db
        ]
    finally:
        db.close()


def _build_round_results(room, current_round) -> Dict:
    """Build consistent round_results payload"""
    normalized_correct = normalize_answer(current_round.correct_answer)
    results = {
        'round': room.current_round + 1,
        'question': current_round.question_text,
        'correct_answer': current_round.correct_answer,
        'player_votes': [],
        'leaderboard': room.get_leaderboard()
    }

    for player_id, player in room.players.items():
        fake_ans = current_round.fake_answers.get(player_id, "")
        vote_info = {
            'player_name': player.name,
            'voted_for': player.voted_answer if player.voted_answer else "",
            'was_correct': (player.voted_answer == normalized_correct) if player.voted_answer else False,
            'fake_answer': fake_ans,
            'votes_received': (
                sum(1 for v in current_round.votes.values() if v == fake_ans)
                if fake_ans else 0
            )
        }
        results['player_votes'].append(vote_info)

    return results


@sio.event
async def connect(sid, environ):
    """When client connects"""
    pass


@sio.on('register_user')
async def handle_register_user(sid, data):
    """Register a new user account"""
    username = data.get('username', '').strip()

    if not username or len(username) < 3:
        await sio.emit('register_error', {
            'message': 'Kullanıcı adı en az 3 karakter olmalıdır!'
        }, room=sid)
        return

    if len(username) > 50:
        await sio.emit('register_error', {
            'message': 'Kullanıcı adı en fazla 50 karakter olabilir!'
        }, room=sid)
        return

    db = SessionLocal()
    try:
        user = create_user(db, username)
        if not user:
            await sio.emit('register_error', {
                'message': 'Bu kullanıcı adı zaten kullanılıyor!'
            }, room=sid)
            return

        socket_users[sid] = user.user_id

        await sio.emit('register_success', {
            'user_id': user.user_id,
            'username': user.username
        }, room=sid)
    finally:
        db.close()


@sio.on('login_user')
async def handle_login_user(sid, data):
    """Login with user_id or username"""
    user_id = data.get('user_id')
    username = data.get('username')

    db = SessionLocal()
    try:
        user = None
        if user_id:
            user = get_user_by_id(db, user_id)
        elif username:
            user = get_user_by_username(db, username)

        if not user:
            await sio.emit('login_error', {
                'message': 'Kullanıcı bulunamadı!'
            }, room=sid)
            return

        update_last_login(db, user.user_id)
        socket_users[sid] = user.user_id

        await sio.emit('login_success', {
            'user_id': user.user_id,
            'username': user.username
        }, room=sid)
    finally:
        db.close()


@sio.on('change_username')
async def handle_change_username(sid, data):
    """Change user's username"""
    new_username = data.get('new_username', '').strip()

    if sid not in socket_users:
        await sio.emit('username_change_error', {
            'message': 'Giriş yapmanız gerekiyor!'
        }, room=sid)
        return

    if not new_username or len(new_username) < 3:
        await sio.emit('username_change_error', {
            'message': 'Kullanıcı adı en az 3 karakter olmalıdır!'
        }, room=sid)
        return

    user_id = socket_users[sid]
    db = SessionLocal()
    try:
        success = update_username(db, user_id, new_username)
        if not success:
            await sio.emit('username_change_error', {
                'message': 'Bu kullanıcı adı zaten kullanılıyor!'
            }, room=sid)
            return

        await sio.emit('username_change_success', {
            'username': new_username
        }, room=sid)
    finally:
        db.close()


@sio.on('get_leaderboard')
async def handle_get_leaderboard(sid, data):
    """Get global leaderboard"""
    limit = data.get('limit', 100)

    db = SessionLocal()
    try:
        leaderboard = get_leaderboard(db, limit)
        await sio.emit('leaderboard_data', {
            'leaderboard': leaderboard
        }, room=sid)
    finally:
        db.close()


@sio.on('get_user_stats')
async def handle_get_user_stats(sid, data):
    """Get stats for a specific user"""
    user_id = data.get('user_id')

    if not user_id:
        await sio.emit('user_stats_error', {'message': 'Kullanıcı ID gerekli!'}, room=sid)
        return

    db = SessionLocal()
    try:
        stats = get_user_stats(db, user_id)
        if not stats:
            await sio.emit('user_stats_error', {'message': 'İstatistik bulunamadı!'}, room=sid)
            return

        await sio.emit('user_stats_data', {
            'stats': {
                'total_games_played': stats.total_games_played,
                'total_games_won': stats.total_games_won,
                'total_score': stats.total_score,
                'highest_score': stats.highest_score,
                'total_questions_answered': stats.total_questions_answered,
                'total_correct_answers': stats.total_correct_answers,
                'total_wrong_answers': stats.total_wrong_answers,
                'total_players_deceived': stats.total_players_deceived,
                'total_times_deceived': stats.total_times_deceived
            }
        }, room=sid)
    finally:
        db.close()


async def remove_disconnected_player(sid: str, room_code: str):
    """Remove player after disconnect timeout"""
    await asyncio.sleep(15)

    room = game_manager.get_room(room_code)
    if room and sid in room.players:
        if not room.players[sid].is_connected:
            player_name = room.players[sid].name
            room.remove_player(sid)

            await sio.emit('player_left', {
                'player_id': sid,
                'player_name': player_name,
                'room_state': room.to_dict()
            }, room=room_code)

            if len(room.players) == 0:
                cancel_all_room_tasks(room_code)
                game_manager.reset_room(room_code)


@sio.event
async def disconnect(sid):
    """When client disconnects"""
    if sid in socket_users:
        del socket_users[sid]

    room_code = socket_rooms.get(sid)
    if room_code:
        room = game_manager.get_room(room_code)
        if room and sid in room.players:
            player_name = room.players[sid].name

            if room.phase == GamePhase.WAITING:
                room.remove_player(sid)

                await sio.emit('player_left', {
                    'player_id': sid,
                    'player_name': player_name,
                    'room_state': room.to_dict()
                }, room=room.room_code)

                if len(room.players) == 0:
                    cancel_all_room_tasks(room_code)
                    game_manager.reset_room(room_code)
            else:
                room.players[sid].is_connected = False

                await sio.emit('player_disconnected', {
                    'player_id': sid,
                    'player_name': player_name,
                    'room_state': room.to_dict()
                }, room=room.room_code)

                create_room_task(room_code, f'remove_player_{sid}', remove_disconnected_player(sid, room_code))

        if sid in socket_rooms:
            del socket_rooms[sid]


@sio.on('join_game')
async def handle_join_game(sid, data):
    """Join a specific game room with selected grade and theme"""
    player_name = data.get('player_name', 'Misafir').strip() or 'Misafir'
    room_code = data.get('room_code', 'ALI_KUSCU')
    grade = data.get('grade')
    theme = data.get('theme')

    room = game_manager.get_room(room_code)

    if not room:
        await sio.emit('error', {'message': 'Oda bulunamadı!'}, room=sid)
        return

    if room.phase != GamePhase.WAITING:
        await sio.emit('error', {'message': 'Oyun zaten başladı!'}, room=sid)
        return

    # Validate selected grade & theme
    validated_grade = None
    validated_theme = None
    if grade:
        try:
            validated_grade, validated_theme = validate_grade_and_theme(grade, theme)
        except ValueError as e:
            await sio.emit('error', {'message': str(e)}, room=sid)
            return

    # If room is empty, a valid grade/theme MUST be selected
    if len(room.players) == 0:
        if not validated_grade:
            await sio.emit('error', {'message': 'Lütfen önce bölüm ve tema seçin!'}, room=sid)
            return
    else:
        # Room already has players -> ensure topic matches if player specified one
        if validated_grade and (room.grade != validated_grade or room.theme != validated_theme):
            room_topic = get_topic_info(room.grade, room.theme)
            topic_label = room_topic['label'] if room_topic else ''
            await sio.emit('error', {
                'message': f'Bu odada farklı bir bölüm/tema oynanıyor ({topic_label}). Lütfen boş bir oda veya aynı temadaki odayı seçin.'
            }, room=sid)
            return

    # Check if player is already in another room
    if sid in socket_rooms:
        old_room_code = socket_rooms[sid]
        if old_room_code != room_code:
            old_room = game_manager.get_room(old_room_code)
            if old_room and sid in old_room.players:
                if old_room.phase != GamePhase.WAITING and old_room.phase != GamePhase.GAME_OVER:
                    await sio.emit('error', {'message': 'Oyun devam ederken oda değiştiremezsiniz!'}, room=sid)
                    return

                old_player_name = old_room.players[sid].name
                old_room.remove_player(sid)
                await sio.leave_room(sid, old_room_code)
                await sio.emit('player_left', {
                    'player_id': sid,
                    'player_name': old_player_name,
                    'room_state': old_room.to_dict()
                }, room=old_room_code)
                if len(old_room.players) == 0:
                    cancel_all_room_tasks(old_room_code)
                    game_manager.reset_room(old_room_code)

    # Check if name already exists in the new room
    existing_names = [p.name.lower() for p in room.players.values()]
    if player_name.lower() in existing_names:
        await sio.emit('name_taken', {
            'message': 'Bu isim zaten kullanılıyor! Lütfen farklı bir isim seçin.',
            'suggested_name': f"{player_name}{len(room.players) + 1}"
        }, room=sid)
        return

    was_empty = len(room.players) == 0
    success = room.add_player(sid, player_name)

    if not success:
        await sio.emit('error', {'message': 'Oda dolu! (Maksimum 4 oyuncu)'}, room=sid)
        return

    if was_empty and validated_grade:
        room.set_topic(validated_grade, validated_theme)

    if sid in socket_users:
        room.players[sid].user_id = socket_users[sid]

    socket_rooms[sid] = room_code
    await sio.enter_room(sid, room.room_code)

    await sio.emit('player_joined', {
        'player': {
            'socket_id': sid,
            'name': player_name,
            'is_host': room.players[sid].is_host
        },
        'room_state': room.to_dict()
    }, room=room.room_code)


@sio.on('set_room_topic')
async def handle_set_room_topic(sid, data):
    """Allow host to update grade and theme while in lobby"""
    room = get_player_room(sid)
    if not room:
        await sio.emit('error', {'message': 'Bir odada değilsiniz!'}, room=sid)
        return

    if room.phase != GamePhase.WAITING:
        await sio.emit('error', {'message': 'Oyun devam ederken bölüm/tema değiştirilemez!'}, room=sid)
        return

    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yöneticisi bölüm/tema değiştirebilir!'}, room=sid)
        return

    try:
        valid_grade, valid_theme = validate_grade_and_theme(data.get('grade'), data.get('theme'))
    except ValueError as e:
        await sio.emit('error', {'message': str(e)}, room=sid)
        return

    room.set_topic(valid_grade, valid_theme)
    await sio.emit('room_topic_updated', {
        'room_state': room.to_dict()
    }, room=room.room_code)


@sio.on('start_game')
async def handle_start_game(sid, data):
    """Start game with questions strictly from room's selected grade and theme"""
    room = get_player_room(sid)
    if not room:
        await sio.emit('error', {'message': 'Oda bulunamadı!'}, room=sid)
        return

    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yöneticisi oyunu başlatabilir!'}, room=sid)
        return

    if len(room.players) < 2:
        await sio.emit('error', {'message': 'Oyun başlatılamadı! En az 2 oyuncu gerekli.'}, room=sid)
        return

    if not room.grade:
        await sio.emit('error', {'message': 'Lütfen önce bölüm ve tema seçin!'}, room=sid)
        return

    # Strictly fetch questions ONLY for this grade & theme
    questions = fetch_questions_for_room(room)
    if not questions:
        topic_info = room.get_topic_info()
        label = topic_info['label'] if topic_info else 'seçili bölüm'
        await sio.emit('error', {
            'message': f'"{label}" için henüz aktif soru bulunmuyor! Lütfen admin panelinden soru ekleyin.'
        }, room=sid)
        return

    success = room.start_game(questions)
    if not success:
        await sio.emit('error', {'message': 'Oyun başlatılamadı!'}, room=sid)
        return

    # Update game statistics and question statistics
    db = SessionLocal()
    try:
        stats = db.query(GameStats).first()
        if stats:
            stats.total_sessions += 1
            db.commit()

        for q in room.questions:
            question_stat = db.query(QuestionStats).filter(
                QuestionStats.question_id == q['id']
            ).first()

            if not question_stat:
                question_stat = QuestionStats(
                    question_id=q['id'],
                    times_asked=0,
                    times_correct=0,
                    times_wrong=0,
                    total_players_seen=0,
                    games_used=0
                )
                db.add(question_stat)
                db.flush()

            question_stat.games_used = (question_stat.games_used or 0) + 1
            question_stat.total_players_seen = (question_stat.total_players_seen or 0) + len(room.players)
            question_stat.last_used = datetime.utcnow()

        db.commit()
    finally:
        db.close()

    current_round = room.rounds[room.current_round]
    await sio.emit('game_started', {
        'room_state': room.to_dict(),
        'question': {
            'round': room.current_round + 1,
            'total_rounds': room.max_rounds,
            'text': current_round.question_text
        }
    }, room=room.room_code)

    create_room_task(room.room_code, 'auto_force_fake', auto_force_fake_submissions(room.room_code))


@sio.on('submit_fake_answer')
async def handle_submit_fake_answer(sid, data):
    """Submit fake answer"""
    fake_answer = data.get('answer', '').strip()
    room = get_player_room(sid)

    if not room:
        await sio.emit('error', {'message': 'Oda bulunamadı! Lütfen sayfayı yenileyin.'}, room=sid)
        return

    success, reason = room.submit_fake_answer(sid, fake_answer)

    if not success:
        if reason == 'correct_answer':
            await sio.emit('answer_rejected', {
                'reason': 'correct_answer',
                'message': 'Bu yanıt şıklara zaten eklendi! Farklı bir yanıt deneyin.'
            }, room=sid)
        elif reason == 'unacceptable_answer':
            await sio.emit('answer_rejected', {
                'reason': 'unacceptable_answer',
                'message': 'Bu yanıt kabul edilmiyor! Lütfen farklı bir yanıltıcı cevap yazın.'
            }, room=sid)
        elif reason == 'duplicate_answer':
            await sio.emit('answer_rejected', {
                'reason': 'duplicate_answer',
                'message': 'Bu yanıt zaten başka bir oyuncu tarafından girildi! Farklı bir yanıt deneyin.'
            }, room=sid)
        else:
            await sio.emit('error', {'message': 'Cevap gönderilemedi!'}, room=sid)
        return

    await sio.emit('fake_answer_submitted', {'success': True}, room=sid)

    current_round = room.rounds[room.current_round]
    await sio.emit('submission_progress', {
        'submitted': len(current_round.fake_answers),
        'total': len(room.players)
    }, room=room.room_code)

    if room.phase == GamePhase.VOTING:
        cancel_room_task(room.room_code, 'auto_force_fake')
        await sio.emit('voting_phase', {
            'options': current_round.all_options,
            'question': current_round.question_text
        }, room=room.room_code)

        create_room_task(room.room_code, 'auto_force_votes', auto_force_votes(room.room_code))


@sio.on('submit_vote')
async def handle_submit_vote(sid, data):
    """Submit vote"""
    chosen_answer = data.get('answer', '')
    room = get_player_room(sid)

    if not room:
        await sio.emit('error', {'message': 'Oda bulunamadı! Lütfen sayfayı yenileyin.'}, room=sid)
        return

    success = room.submit_vote(sid, chosen_answer)

    if not success:
        current_round = room.rounds[room.current_round]
        player_fake = current_round.fake_answers.get(sid)
        if player_fake and normalize_answer(chosen_answer) == player_fake:
            await sio.emit('vote_rejected', {
                'reason': 'own_answer',
                'message': 'Kendi yanlış cevabınızı seçemezsiniz!'
            }, room=sid)
        else:
            await sio.emit('error', {'message': 'Oy gönderilemedi!'}, room=sid)
        return

    await sio.emit('vote_submitted', {'success': True}, room=sid)

    current_round = room.rounds[room.current_round]
    await sio.emit('voting_progress', {
        'voted': len(current_round.votes),
        'total': len(room.players)
    }, room=room.room_code)

    if room.phase == GamePhase.SHOWING_RESULTS:
        cancel_room_task(room.room_code, 'auto_force_votes')
        results = _build_round_results(room, current_round)
        await sio.emit('round_results', results, room=room.room_code)
        create_room_task(room.room_code, 'auto_next_round', auto_next_round(room.room_code))


@sio.on('add_reaction')
async def handle_add_reaction(sid, data):
    """Add emoji reaction to a player"""
    answer = data.get('answer', '').strip()
    emoji = data.get('emoji', '')
    room = get_player_room(sid)

    if not room or not answer or not emoji:
        return

    success = room.add_reaction(sid, answer, emoji)

    if success:
        current_round = room.rounds[room.current_round]
        await sio.emit('reaction_added', {
            'player_id': sid,
            'player_name': room.players[sid].name,
            'answer': answer,
            'emoji': emoji,
            'all_reactions': current_round.reactions
        }, room=room.room_code)


async def auto_force_fake_submissions(room_code):
    """Force submit empty answers for players who haven't submitted after timeout"""
    await asyncio.sleep(25)  # 20 seconds + 5 buffer

    room = game_manager.get_room(room_code)
    if not room or room.phase != GamePhase.SUBMITTING_FAKE:
        return

    current_round = room.rounds[room.current_round]

    for player_id in list(room.players.keys()):
        if player_id not in current_round.fake_answers:
            room.submit_fake_answer(player_id, "")

    if room.phase == GamePhase.VOTING:
        current_round = room.rounds[room.current_round]
        await sio.emit('voting_phase', {
            'options': current_round.all_options,
            'question': current_round.question_text
        }, room=room_code)

        create_room_task(room_code, 'auto_force_votes', auto_force_votes(room_code))


async def auto_force_votes(room_code):
    """Force submit empty votes for players who haven't voted after timeout"""
    await asyncio.sleep(15)  # 10 seconds + 5 buffer

    room = game_manager.get_room(room_code)
    if not room or room.phase != GamePhase.VOTING:
        return

    current_round = room.rounds[room.current_round]

    for player_id in list(room.players.keys()):
        if player_id not in current_round.votes:
            room.submit_vote(player_id, "")

    if room.phase == GamePhase.SHOWING_RESULTS:
        results = _build_round_results(room, current_round)
        await sio.emit('round_results', results, room=room_code)
        create_room_task(room_code, 'auto_next_round', auto_next_round(room_code))


async def auto_next_round(room_code):
    """Automatically proceed to next round after 10 seconds"""
    await asyncio.sleep(10)

    room = game_manager.get_room(room_code)
    if not room or room.phase != GamePhase.SHOWING_RESULTS:
        return

    room.next_round()

    if room.phase == GamePhase.FINAL_TEST:
        await sio.emit('final_test_phase', room.get_final_matching_payload(), room=room_code)
        create_room_task(room_code, 'auto_finish_final_test', auto_finish_final_test(room_code))
    else:
        current_round = room.rounds[room.current_round]
        await sio.emit('new_round', {
            'room_state': room.to_dict(),
            'question': {
                'round': room.current_round + 1,
                'total_rounds': room.max_rounds,
                'text': current_round.question_text
            }
        }, room=room_code)

        create_room_task(room_code, 'auto_force_fake', auto_force_fake_submissions(room_code))


async def auto_finish_final_test(room_code):
    """Automatically finish final matching activity after 120 seconds"""
    await asyncio.sleep(125)  # 120s + 5s grace buffer for client auto-submit

    room = game_manager.get_room(room_code)
    if not room or room.phase != GamePhase.FINAL_TEST:
        return

    try:
        await show_final_results(room)
    except Exception as e:
        print(f"[ERROR] auto_finish_final_test failed: {e}")
        room.phase = GamePhase.GAME_OVER
        await sio.emit('error', {'message': 'Sonuçlar hesaplanırken hata oluştu.'}, room=room_code)


async def auto_reset_room(room_code):
    """Reset room to waiting state after game over"""
    await asyncio.sleep(60)

    room = game_manager.get_room(room_code)
    if room and room.phase == GamePhase.GAME_OVER:
        room = game_manager.reset_room_keep_players(room_code)
        await sio.emit('room_ready_for_new_game', {
            'message': 'Oda yeni oyun için hazır!',
            'room_state': room.to_dict()
        }, room=room_code)


@sio.on('next_round')
async def handle_next_round(sid, data):
    """Move to next round - handled automatically by auto_next_round"""
    pass


@sio.on('submit_final_matches')
async def handle_submit_final_matches(sid, data):
    """Submit all concept-to-question matches for a player"""
    room = get_player_room(sid)
    if not room:
        await sio.emit('error', {'message': 'Oda bulunamadı! Lütfen sayfayı yenileyin.'}, room=sid)
        return

    if room.phase != GamePhase.FINAL_TEST:
        return

    matches = data.get('matches', {})
    success = room.submit_final_matches(sid, matches)
    if not success:
        await sio.emit('error', {'message': 'Eşleştirmeler gönderilemedi!'}, room=sid)
        return

    await sio.emit('final_matches_submitted', {'success': True}, room=sid)

    submitted, total = room.get_final_submission_counts()
    await sio.emit('final_test_progress', {
        'submitted': submitted,
        'total': total
    }, room=room.room_code)

    if room.all_players_submitted_final():
        cancel_room_task(room.room_code, 'auto_finish_final_test')
        try:
            await show_final_results(room)
        except Exception as e:
            print(f"[ERROR] show_final_results failed: {e}")
            room.phase = GamePhase.GAME_OVER
            await sio.emit('error', {'message': 'Sonuçlar hesaplanırken hata oluştu.'}, room=room.room_code)


@sio.on('submit_final_answer')
async def handle_submit_final_answer(sid, data):
    """Legacy single final answer submission"""
    question_index = data.get('question_index', 0)
    answer = data.get('answer', '').strip()
    room = get_player_room(sid)

    if not room or room.phase != GamePhase.FINAL_TEST:
        return

    room.submit_final_answer(sid, question_index, answer)
    await sio.emit('final_answer_submitted', {
        'question_index': question_index,
        'success': True
    }, room=sid)


async def show_final_results(room):
    """Calculate and show final matching results to all players (runs at most once)"""
    with room._lock:
        if room.final_results_shown:
            return
        room.final_results_shown = True

    final_scores = {}
    player_answers = {}
    matching_questions = room.final_test_questions or room.questions

    for player_id, player in room.players.items():
        correct_count = 0
        answers_detail = []

        for i, question in enumerate(matching_questions):
            user_answer = player.final_answers.get(i, "")
            is_correct = (
                bool(user_answer)
                and normalize_answer(user_answer) == normalize_answer(question['correct_answer'])
            )

            if is_correct:
                correct_count += 1

            answers_detail.append({
                'question_index': i,
                'user_answer': user_answer,
                'is_correct': is_correct
            })

        bonus_score = correct_count * 500
        player.score += bonus_score

        final_scores[player_id] = {
            'correct_count': correct_count,
            'total_questions': len(matching_questions),
            'bonus_score': bonus_score,
            'total_score': player.score
        }

        player_answers[player_id] = answers_detail

    room.phase = GamePhase.GAME_OVER

    leaderboard = room.get_leaderboard()
    winner_id = leaderboard[0]['socket_id'] if leaderboard else None

    # Update game statistics and question statistics
    try:
        db = SessionLocal()
        try:
            stats = db.query(GameStats).first()
            if stats:
                stats.completed_sessions += 1
                stats.total_players += len(room.players)

            for player_id, player in room.players.items():
                answers = player_answers.get(player_id, [])
                correct_count = sum(1 for a in answers if a.get('is_correct'))
                wrong_count = len(answers) - correct_count

                if stats:
                    stats.total_questions_answered += len(answers)
                    stats.total_correct_answers += correct_count
                    stats.total_wrong_answers += wrong_count

                for i, answer in enumerate(answers):
                    if i < len(matching_questions):
                        question_id = matching_questions[i].get('id')
                        if question_id:
                            question_stat = db.query(QuestionStats).filter(
                                QuestionStats.question_id == question_id
                            ).first()

                            if question_stat:
                                question_stat.times_asked = (question_stat.times_asked or 0) + 1
                                if answer.get('is_correct'):
                                    question_stat.times_correct = (question_stat.times_correct or 0) + 1
                                else:
                                    question_stat.times_wrong = (question_stat.times_wrong or 0) + 1

                if player.user_id:
                    players_deceived = 0
                    times_deceived = 0

                    for round_data in room.rounds:
                        fake_answer = round_data.fake_answers.get(player_id)
                        if fake_answer:
                            votes_for_fake = sum(1 for vote in round_data.votes.values() if vote == fake_answer)
                            players_deceived += votes_for_fake

                        player_vote = round_data.votes.get(player_id)
                        if player_vote and round_data.correct_answer:
                            if player_vote != normalize_answer(round_data.correct_answer):
                                times_deceived += 1

                    update_user_stats_after_game(db, player.user_id, {
                        'won': player_id == winner_id,
                        'score': player.score,
                        'correct_answers': correct_count,
                        'wrong_answers': wrong_count,
                        'players_deceived': players_deceived,
                        'times_deceived': times_deceived
                    })

            db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"[ERROR] Failed to update stats in show_final_results: {e}")

    await sio.emit('game_over', {
        'final_scores': final_scores,
        'player_answers': player_answers,
        'leaderboard': leaderboard,
        'players': room.to_dict()['players'],
        'topic': room.get_topic_info(),
        'questions_summary': [
            {
                'question': q['question_text'],
                'correct_answer': q['correct_answer']
            }
            for q in matching_questions
        ]
    }, room=room.room_code)

    create_room_task(room.room_code, 'auto_reset_room', auto_reset_room(room.room_code))


@sio.on('finish_game')
async def handle_finish_game(sid, data):
    """Deprecated - handled automatically via submit_final_matches"""
    pass


@sio.on('leave_room')
async def handle_leave_room(sid, data):
    """Player leaves room"""
    room_code = socket_rooms.get(sid)
    if room_code:
        room = game_manager.get_room(room_code)
        if room and sid in room.players:
            player_name = room.players[sid].name
            room.remove_player(sid)

            await sio.emit('player_left', {
                'player_id': sid,
                'player_name': player_name,
                'room_state': room.to_dict()
            }, room=room.room_code)

            if len(room.players) == 0:
                cancel_all_room_tasks(room_code)
                game_manager.reset_room(room_code)

        await sio.leave_room(sid, room_code)

        if sid in socket_rooms:
            del socket_rooms[sid]


@sio.on('reset_room')
async def handle_reset_room(sid, data):
    """Reset room for new game (only host can do this)"""
    room_code = socket_rooms.get(sid)
    if not room_code:
        await sio.emit('error', {'message': 'Bir odada değilsiniz!'}, room=sid)
        return

    room = game_manager.get_room(room_code)
    if not room:
        return

    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yöneticisi odayı sıfırlayabilir!'}, room=sid)
        return

    cancel_all_room_tasks(room_code)

    await sio.emit('room_reset', {
        'message': 'Oda sıfırlandı. Ana sayfaya yönlendiriliyorsunuz...'
    }, room=room_code)

    players_to_remove = [p_sid for p_sid, code in socket_rooms.items() if code == room_code]
    for player_sid in players_to_remove:
        await sio.leave_room(player_sid, room_code)
        del socket_rooms[player_sid]

    game_manager.reset_room(room_code)


@sio.on('return_to_lobby')
async def handle_return_to_lobby(sid, data):
    """Return to lobby with same players and topic (only host can do this)"""
    room_code = socket_rooms.get(sid)
    if not room_code:
        await sio.emit('error', {'message': 'Bir odada değilsiniz!'}, room=sid)
        return

    room = game_manager.get_room(room_code)
    if not room:
        return

    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yöneticisi lobiye dönebilir!'}, room=sid)
        return

    cancel_all_room_tasks(room_code)
    room = game_manager.reset_room_keep_players(room_code)

    await sio.emit('returned_to_lobby', {
        'message': 'Lobiye dönüldü!',
        'room_state': room.to_dict()
    }, room=room_code)


@sio.on('restart_game')
async def handle_restart_game(sid, data):
    """Restart game with same players and same selected grade/theme (only host can do this)"""
    room_code = socket_rooms.get(sid)
    if not room_code:
        await sio.emit('error', {'message': 'Bir odada değilsiniz!'}, room=sid)
        return

    room = game_manager.get_room(room_code)
    if not room:
        return

    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yöneticisi yeni oyun başlatabilir!'}, room=sid)
        return

    if len(room.players) < 2:
        await sio.emit('error', {'message': 'Yeni oyun için en az 2 oyuncu gerekli!'}, room=sid)
        return

    cancel_all_room_tasks(room_code)
    room = game_manager.reset_room_keep_players(room_code)

    # Fetch ONLY questions for the room's selected grade & theme
    questions_list = fetch_questions_for_room(room)
    if not questions_list:
        topic_info = room.get_topic_info()
        label = topic_info['label'] if topic_info else 'seçili bölüm'
        await sio.emit('error', {
            'message': f'"{label}" için aktif soru bulunamadı!'
        }, room=sid)
        return

    room.start_game(questions_list)

    db = SessionLocal()
    try:
        stats = db.query(GameStats).first()
        if stats:
            stats.total_sessions = (stats.total_sessions or 0) + 1
            db.commit()

        for q in room.questions:
            question_stat = db.query(QuestionStats).filter(QuestionStats.question_id == q['id']).first()
            if not question_stat:
                question_stat = QuestionStats(
                    question_id=q['id'],
                    times_asked=0,
                    times_correct=0,
                    times_wrong=0,
                    total_players_seen=0,
                    games_used=0
                )
                db.add(question_stat)
                db.flush()
            question_stat.games_used = (question_stat.games_used or 0) + 1
            question_stat.total_players_seen = (question_stat.total_players_seen or 0) + len(room.players)
            question_stat.last_used = datetime.utcnow()
        db.commit()
    finally:
        db.close()

    current_round = room.rounds[0]
    await sio.emit('game_restarted', {
        'message': 'Yeni oyun başladı!',
        'room_state': room.to_dict(),
        'current_question': {
            'round': 1,
            'total_rounds': room.max_rounds,
            'text': current_round.question_text
        }
    }, room=room_code)

    create_room_task(room.room_code, 'auto_force_fake', auto_force_fake_submissions(room.room_code))


# Create ASGI application
socket_app = socketio.ASGIApp(sio)
