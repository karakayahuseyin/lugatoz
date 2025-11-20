# -*- coding: utf-8 -*-
import socketio
import asyncio
from typing import Dict
from .game_manager import game_manager, GamePhase, check_answer, Player, GameManager
from .database import SessionLocal
from .models import Question, GameStats, QuestionStats, User, UserStats
from .auth import create_user, get_user_by_id, get_user_by_username, update_username, update_last_login, get_leaderboard, update_user_stats_after_game
from datetime import datetime

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
    # Cancel existing task if any
    cancel_room_task(room_code, task_name)

    # Initialize room tasks dict if needed
    if room_code not in room_tasks:
        room_tasks[room_code] = {}

    # Create and track new task
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

        # Track user
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

        # Update last login
        update_last_login(db, user.user_id)

        # Track user
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


async def remove_disconnected_player(sid: str, room_code: str):
    """Remove player after disconnect timeout"""
    await asyncio.sleep(15)  # Wait 15 seconds for reconnection

    room = game_manager.get_room(room_code)
    if room and sid in room.players:
        # Check if still disconnected
        if not room.players[sid].is_connected:
            player_name = room.players[sid].name
            room.remove_player(sid)

            # Notify other players
            await sio.emit('player_left', {
                'player_id': sid,
                'player_name': player_name,
                'room_state': room.to_dict()
            }, room=room_code)

            # Reset room if empty
            if len(room.players) == 0:
                game_manager.reset_room(room_code)


@sio.event
async def disconnect(sid):
    """When client disconnects"""

    # Remove user tracking (but keep user account active)
    if sid in socket_users:
        del socket_users[sid]

    # Get the room this socket was in
    room_code = socket_rooms.get(sid)
    if room_code:
        room = game_manager.get_room(room_code)
        if room and sid in room.players:
            player_name = room.players[sid].name

            # If in lobby (WAITING phase), remove immediately
            if room.phase == GamePhase.WAITING:
                room.remove_player(sid)

                # Notify other players
                await sio.emit('player_left', {
                    'player_id': sid,
                    'player_name': player_name,
                    'room_state': room.to_dict()
                }, room=room.room_code)

                # Reset room if empty
                if len(room.players) == 0:
                    game_manager.reset_room(room_code)
            else:
                # In game - allow reconnection, mark as disconnected
                room.players[sid].is_connected = False

                # Notify other players about disconnection
                await sio.emit('player_disconnected', {
                    'player_id': sid,
                    'player_name': player_name,
                    'room_state': room.to_dict()
                }, room=room.room_code)

                # Schedule removal after 15 seconds if not reconnected
                create_room_task(room_code, f'remove_player_{sid}', remove_disconnected_player(sid, room_code))

        # Remove from socket tracking
        if sid in socket_rooms:
            del socket_rooms[sid]


@sio.on('join_game')
async def handle_join_game(sid, data):
    """Join a specific game room"""
    player_name = data.get('player_name', 'Anonymous')
    room_code = data.get('room_code', 'ALI_KUSCU')  # Default to first room

    room = game_manager.get_room(room_code)

    if not room:
        await sio.emit('error', {'message': 'Oda bulunamadı!'}, room=sid)
        return

    if room.phase != GamePhase.WAITING:
        await sio.emit('error', {'message': 'Oyun zaten başladı!'}, room=sid)
        return

    # Check if name already exists
    existing_names = [p.name.lower() for p in room.players.values()]
    if player_name.lower() in existing_names:
        await sio.emit('name_taken', {
            'message': 'Bu isim zaten kullanılıyor! Lütfen farklı bir isim seçin.',
            'suggested_name': f"{player_name}{len(room.players) + 1}"
        }, room=sid)
        return

    success = room.add_player(sid, player_name)

    if not success:
        await sio.emit('error', {'message': 'Oda dolu! (Maksimum 4 oyuncu)'}, room=sid)
        return

    # Link user_id to player if logged in
    if sid in socket_users:
        room.players[sid].user_id = socket_users[sid]

    # Track which room this socket is in
    socket_rooms[sid] = room_code

    # Add to Socket.IO room
    await sio.enter_room(sid, room.room_code)

    # Notify all players
    await sio.emit('player_joined', {
        'player': {
            'socket_id': sid,
            'name': player_name,
            'is_host': room.players[sid].is_host
        },
        'room_state': room.to_dict()
    }, room=room.room_code)


@sio.on('start_game')
async def handle_start_game(sid, data):
    """Start game"""
    room = get_player_room(sid)

    # Only host can start
    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yöneticisi oyunu başlatabilir!'}, room=sid)
        return

    # Get questions from database
    db = SessionLocal()
    try:
        questions_db = db.query(Question).filter(Question.is_active == True).all()
        questions = [
            {
                'id': q.id,
                'question_text': q.question_text,
                'correct_answer': q.correct_answer,
                'acceptable_answers': q.acceptable_answers
            }
            for q in questions_db
        ]
    finally:
        db.close()

    success = room.start_game(questions)

    if not success:
        await sio.emit('error', {'message': 'Oyun başlatılamadı! En az 2 oyuncu gerekli.'}, room=sid)
        return

    # Update game statistics and question statistics
    db = SessionLocal()
    try:
        # Update global stats
        stats = db.query(GameStats).first()
        if stats:
            stats.total_sessions += 1
            db.commit()

        # Update question statistics for selected questions
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
                db.flush()  # Flush to get default values

            question_stat.games_used = (question_stat.games_used or 0) + 1
            question_stat.total_players_seen = (question_stat.total_players_seen or 0) + len(room.players)
            question_stat.last_used = datetime.utcnow()

        db.commit()
    finally:
        db.close()

    # Notify all players
    current_round = room.rounds[room.current_round]
    await sio.emit('game_started', {
        'room_state': room.to_dict(),
        'question': {
            'round': room.current_round + 1,
            'total_rounds': room.max_rounds,
            'text': current_round.question_text
        }
    }, room=room.room_code)


@sio.on('submit_fake_answer')
async def handle_submit_fake_answer(sid, data):
    """Submit fake answer"""
    fake_answer = data.get('answer', '').strip()
    room = get_player_room(sid)

    # Allow empty answers (for timeout penalty)
    success = room.submit_fake_answer(sid, fake_answer)

    if not success:
        # Check if it was because answer is correct
        current_round = room.rounds[room.current_round]
        from .game_manager import normalize_answer

        if check_answer(fake_answer, current_round.correct_answer, current_round.acceptable_answers):
            await sio.emit('answer_rejected', {
                'reason': 'correct_answer',
                'message': 'Doğru cevabı giremezsiniz!'
            }, room=sid)
        # Check if duplicate
        elif normalize_answer(fake_answer) in [normalize_answer(ans) for ans in current_round.fake_answers.values()]:
            await sio.emit('answer_rejected', {
                'reason': 'duplicate_answer',
                'message': 'Bu cevap zaten başka bir oyuncu tarafından girildi!'
            }, room=sid)
        else:
            await sio.emit('error', {'message': 'Cevap gönderilemedi!'}, room=sid)
        return

    # Confirm to player
    await sio.emit('fake_answer_submitted', {'success': True}, room=sid)

    # Check if all players submitted
    current_round = room.rounds[room.current_round]
    await sio.emit('submission_progress', {
        'submitted': len(current_round.fake_answers),
        'total': len(room.players)
    }, room=room.room_code)

    # If everyone submitted, move to voting
    if room.phase == GamePhase.VOTING:
        await sio.emit('voting_phase', {
            'options': current_round.all_options,
            'question': current_round.question_text
        }, room=room.room_code)


@sio.on('submit_vote')
async def handle_submit_vote(sid, data):
    """Submit vote"""
    chosen_answer = data.get('answer', '')
    room = get_player_room(sid)

    success = room.submit_vote(sid, chosen_answer)

    if not success:
        # Check if trying to vote for own answer
        current_round = room.rounds[room.current_round]
        player_fake = current_round.fake_answers.get(sid)
        if player_fake and chosen_answer.strip().lower() == player_fake:
            await sio.emit('vote_rejected', {
                'reason': 'own_answer',
                'message': 'Kendi yanlış cevabınızı seçemezsiniz!'
            }, room=sid)
        else:
            await sio.emit('error', {'message': 'Oy gönderilemedi!'}, room=sid)
        return

    # Confirm to player
    await sio.emit('vote_submitted', {'success': True}, room=sid)

    # Update progress
    current_round = room.rounds[room.current_round]
    await sio.emit('voting_progress', {
        'voted': len(current_round.votes),
        'total': len(room.players)
    }, room=room.room_code)

    # If everyone voted, show results
    if room.phase == GamePhase.SHOWING_RESULTS:
        # Prepare results
        from .game_manager import normalize_answer

        results = {
            'correct_answer': normalize_answer(current_round.correct_answer),  # Küçük harf
            'acceptable_answers': current_round.acceptable_answers if current_round.acceptable_answers else None,
            'player_votes': [],
            'leaderboard': room.get_leaderboard()
        }

        for player_id, player in room.players.items():
            vote_info = {
                'player_name': player.name,
                'voted_for': player.voted_answer if player.voted_answer else "",
                'was_correct': player.voted_answer == normalize_answer(current_round.correct_answer) if player.voted_answer else False,
                'fake_answer': current_round.fake_answers.get(player_id, ""),
                'votes_received': sum(1 for v in current_round.votes.values()
                                     if v == current_round.fake_answers.get(player_id))
            }
            results['player_votes'].append(vote_info)

        await sio.emit('round_results', results, room=room.room_code)

        # Auto proceed to next round after 10 seconds
        create_room_task(room.room_code, 'auto_next_round', auto_next_round(room.room_code))


@sio.on('add_reaction')
async def handle_add_reaction(sid, data):
    """Add emoji reaction to an answer"""
    answer = data.get('answer', '').strip()
    emoji = data.get('emoji', '')
    room = get_player_room(sid)

    if not answer or not emoji:
        return

    success = room.add_reaction(sid, answer, emoji)

    if success:
        # Broadcast reaction to all players
        current_round = room.rounds[room.current_round]
        await sio.emit('reaction_added', {
            'player_id': sid,
            'player_name': room.players[sid].name,
            'answer': answer,
            'emoji': emoji,
            'all_reactions': current_round.reactions
        }, room=room.room_code)



async def auto_next_round(room_code):
    """Automatically proceed to next round after 10 seconds"""
    await asyncio.sleep(10)  # Wait 10 seconds

    room = game_manager.get_room(room_code)

    # Check if we're still in showing results (in case manually advanced)
    if room.phase != GamePhase.SHOWING_RESULTS:
        return

    # Move to next round
    room.next_round()

    if room.phase == GamePhase.FINAL_TEST:
        # Send the same questions that were played during the game
        await sio.emit('final_test_phase', {
            'questions': [
                {
                    'index': i,
                    'question_text': room.questions[i]['question_text']
                }
                for i in range(len(room.questions))
            ]
        }, room=room_code)

        # Start timeout for final test (120 seconds)
        create_room_task(room_code, 'auto_finish_final_test', auto_finish_final_test(room_code))
    else:
        # New round
        current_round = room.rounds[room.current_round]
        await sio.emit('new_round', {
            'room_state': room.to_dict(),
            'question': {
                'round': room.current_round + 1,
                'total_rounds': room.max_rounds,
                'text': current_round.question_text
            }
        }, room=room_code)


async def auto_finish_final_test(room_code):
    """Automatically finish final test after 120 seconds"""
    await asyncio.sleep(120)  # Wait 120 seconds

    room = game_manager.get_room(room_code)

    # Check if we're still in final test (in case already finished)
    if room.phase != GamePhase.FINAL_TEST:
        return

    # Show final results to all players
    await show_final_results(room)


async def auto_reset_room(room_code):
    """Reset room to waiting state after game over"""
    await asyncio.sleep(30)  # Wait 30 seconds

    room = game_manager.get_room(room_code)

    # Only reset if still in game over state
    if room and room.phase == GamePhase.GAME_OVER:
        # Reset room but keep players
        room = game_manager.reset_room_keep_players(room_code)

        # Notify all players
        await sio.emit('room_ready_for_new_game', {
            'message': 'Oda yeni oyun icin hazir!',
            'room_state': room.to_dict()
        }, room=room_code)



@sio.on('next_round')
async def handle_next_round(sid, data):
    """Move to next round - DISABLED: Now handled automatically by auto_next_round"""
    # This event is ignored - round progression is automatic after 10 seconds
    pass


@sio.on('submit_final_answer')
async def handle_submit_final_answer(sid, data):
    """Submit final test answer"""
    question_index = data.get('question_index', 0)
    answer = data.get('answer', '').strip()
    room = get_player_room(sid)

    success = room.submit_final_answer(sid, question_index, answer)

    if not success:
        await sio.emit('error', {'message': 'Cevap gönderilemedi!'}, room=sid)
        return

    await sio.emit('final_answer_submitted', {
        'question_index': question_index,
        'success': True
    }, room=sid)

    # Check if all players have answered all questions
    all_completed = True
    for player in room.players.values():
        if len(player.final_answers) < len(room.questions):
            all_completed = False
            break

    # If all players completed, show results
    if all_completed:
        await show_final_results(room)


async def show_final_results(room):
    """Calculate and show final results to all players"""
    final_scores = {}
    player_answers = {}

    # Calculate scores for all players using room.questions (same list used throughout game)
    for player_id, player in room.players.items():
        correct_count = 0
        answers_detail = []

        for i, question in enumerate(room.questions):
            user_answer = player.final_answers.get(i, "")
            is_correct = check_answer(user_answer, question['correct_answer'], question.get('acceptable_answers'))

            if is_correct:
                correct_count += 1

            answers_detail.append({
                'question_index': i,
                'user_answer': user_answer,
                'is_correct': is_correct
            })

        # Add bonus points
        bonus_score = correct_count * 500
        player.score += bonus_score

        final_scores[player_id] = {
            'correct_count': correct_count,
            'bonus_score': bonus_score,
            'total_score': player.score
        }

        player_answers[player_id] = answers_detail

    room.phase = GamePhase.GAME_OVER

    # Determine winner
    leaderboard = room.get_leaderboard()
    winner_id = leaderboard[0]['socket_id'] if leaderboard else None

    # Update game statistics and question statistics
    db = SessionLocal()
    try:
        stats = db.query(GameStats).first()
        if stats:
            stats.completed_sessions += 1
            stats.total_players += len(room.players)

            # Count total questions answered and correct/wrong per player
            for player_id in room.players:
                answers = player_answers[player_id]
                stats.total_questions_answered += len(answers)

                # Count correct/wrong answers
                correct_count = sum(1 for a in answers if a['is_correct'])
                wrong_count = len(answers) - correct_count

                for i, answer in enumerate(answers):
                    if answer['is_correct']:
                        stats.total_correct_answers += 1
                    else:
                        stats.total_wrong_answers += 1

                    # Update question-specific stats
                    question_id = room.questions[i]['id']
                    question_stat = db.query(QuestionStats).filter(
                        QuestionStats.question_id == question_id
                    ).first()

                    if question_stat:
                        # times_asked increases per player (not per game)
                        question_stat.times_asked = (question_stat.times_asked or 0) + 1
                        if answer['is_correct']:
                            question_stat.times_correct = (question_stat.times_correct or 0) + 1
                        else:
                            question_stat.times_wrong = (question_stat.times_wrong or 0) + 1

                # Update user statistics if player is logged in
                player = room.players[player_id]
                if player.user_id:
                    # Calculate deception stats
                    players_deceived = 0
                    times_deceived = 0

                    for round_data in room.rounds:
                        # Count how many players voted for this player's fake answer
                        fake_answer = round_data.fake_answers.get(player_id)
                        if fake_answer:
                            votes_for_fake = sum(1 for vote in round_data.votes.values() if vote == fake_answer)
                            players_deceived += votes_for_fake

                        # Count if this player was deceived (voted for wrong answer)
                        player_vote = round_data.votes.get(player_id)
                        if player_vote and player_vote != normalize_answer(round_data.correct_answer):
                            times_deceived += 1

                    # Update user stats
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

    # Send results with the same questions list
    await sio.emit('game_over', {
        'final_scores': final_scores,
        'player_answers': player_answers,
        'leaderboard': room.get_leaderboard(),
        'players': room.to_dict()['players'],
        'questions_summary': [
            {
                'question': q['question_text'],
                'correct_answer': q['correct_answer'],
                'acceptable_answers': q.get('acceptable_answers')
            }
            for q in room.questions
        ]
    }, room=room.room_code)

    # After 30 seconds, reset the room to WAITING state for new game
    create_room_task(room.room_code, 'auto_reset_room', auto_reset_room(room.room_code))


@sio.on('finish_game')
async def handle_finish_game(sid, data):
    """Finish game - deprecated, now handled automatically"""
    # This is now handled automatically when all players submit or timeout
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

            # Notify other players
            await sio.emit('player_left', {
                'player_id': sid,
                'player_name': player_name,
                'room_state': room.to_dict()
            }, room=room.room_code)

            # Reset room if empty
            if len(room.players) == 0:
                game_manager.reset_room(room_code)

        # Leave Socket.IO room
        await sio.leave_room(sid, room_code)

        # Remove from tracking
        if sid in socket_rooms:
            del socket_rooms[sid]



@sio.on('reset_room')
async def handle_reset_room(sid, data):
    """Reset room for new game (only host can do this)"""
    room_code = socket_rooms.get(sid)
    if not room_code:
        await sio.emit('error', {'message': 'Bir odada degilisiniz!'}, room=sid)
        return

    room = game_manager.get_room(room_code)
    if not room:
        return

    # Only host can reset
    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yoneticisi odayi sifirlayabilir!'}, room=sid)
        return

    # Remove all players from socket tracking
    players_to_remove = list(socket_rooms.keys())
    for player_sid in players_to_remove:
        if socket_rooms.get(player_sid) == room_code:
            await sio.leave_room(player_sid, room_code)
            del socket_rooms[player_sid]

    # Reset the room
    game_manager.reset_room(room_code)

    # Notify everyone that room was reset
    await sio.emit('room_reset', {
        'message': 'Oda sifirlandi. Ana sayfaya yonlendiriliyorsunuz...'
    }, room=room_code)



@sio.on('return_to_lobby')
async def handle_return_to_lobby(sid, data):
    """Return to lobby with same players (only host can do this)"""
    room_code = socket_rooms.get(sid)
    if not room_code:
        await sio.emit('error', {'message': 'Bir odada degilisiniz!'}, room=sid)
        return

    room = game_manager.get_room(room_code)
    if not room:
        return

    # Only host can return to lobby
    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yoneticisi lobiye donebilir!'}, room=sid)
        return

    # Cancel all pending tasks for this room
    cancel_all_room_tasks(room_code)

    # Reset room but keep players
    room = game_manager.reset_room_keep_players(room_code)

    # Notify all players
    await sio.emit('returned_to_lobby', {
        'message': 'Lobiye donuldu!',
        'room_state': room.to_dict()
    }, room=room_code)



@sio.on('restart_game')
async def handle_restart_game(sid, data):
    """Restart game with same players (only host can do this)"""
    room_code = socket_rooms.get(sid)
    if not room_code:
        await sio.emit('error', {'message': 'Bir odada degilisiniz!'}, room=sid)
        return

    room = game_manager.get_room(room_code)
    if not room:
        return

    # Only host can restart
    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yoneticisi yeni oyun baslayabilir!'}, room=sid)
        return

    # Need at least 2 players
    if len(room.players) < 2:
        await sio.emit('error', {'message': 'Yeni oyun icin en az 2 oyuncu gerekli!'}, room=sid)
        return

    # Cancel all pending tasks for this room
    cancel_all_room_tasks(room_code)

    # Reset room but keep players
    room = game_manager.reset_room_keep_players(room_code)

    # Get questions from database
    db = SessionLocal()
    try:
        questions = db.query(Question).all()
        questions_list = [
            {
                'id': q.id,
                'question_text': q.question_text,
                'correct_answer': q.correct_answer,
                'acceptable_answers': q.acceptable_answers
            }
            for q in questions
        ]
    finally:
        db.close()

    if len(questions_list) < room.max_rounds:
        await sio.emit('error', {'message': f'Yeterli soru yok! En az {room.max_rounds} soru gerekli.'}, room=sid)
        return

    # Start the game
    room.start_game(questions_list)

    # Track stats
    db = SessionLocal()
    try:
        stats = db.query(GameStats).first()
        if stats:
            stats.total_sessions = (stats.total_sessions or 0) + 1
            stats.total_players = (stats.total_players or 0) + len(room.players)
            db.commit()

        # Update question stats
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
        db.commit()
    finally:
        db.close()

    # Notify all players
    current_round = room.rounds[0]
    await sio.emit('game_restarted', {
        'message': 'Yeni oyun basladi!',
        'room_state': room.to_dict(),
        'current_question': {
            'round': 1,
            'total_rounds': room.max_rounds,
            'text': current_round.question_text
        }
    }, room=room_code)



# Create ASGI application
socket_app = socketio.ASGIApp(sio)
