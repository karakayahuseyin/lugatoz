# -*- coding: utf-8 -*-
import socketio
import asyncio
from typing import Dict
from .game_manager import game_manager, GamePhase, check_answer
from .database import SessionLocal
from .models import Question

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Track which room each socket is in
socket_rooms: Dict[str, str] = {}  # socket_id -> room_code


def get_player_room(sid):
    """Get the room for a given socket ID"""
    room_code = socket_rooms.get(sid)
    if room_code:
        return game_manager.get_room(room_code)
    return None


@sio.event
async def connect(sid, environ):
    """When client connects"""
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    """When client disconnects"""
    print(f"Client disconnected: {sid}")

    # Get the room this socket was in
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
                print(f"Room {room_code} reset (empty after disconnect)")

        # Remove from tracking
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

    print(f"{player_name} joined game (total: {len(room.players)}/4)")


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

    print(f"Game started with {len(room.players)} players")


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

        # Auto-advance to next round after 10 seconds
        asyncio.create_task(auto_next_round(room.room_code, room.current_round))


async def auto_next_round(room_code, round_number):
    """Automatically advance to next round after delay"""
    await asyncio.sleep(10)  # Wait 10 seconds

    room = game_manager.get_room(room_code)

    # Check if we're still on the same round (in case someone manually advanced)
    if room.current_round != round_number or room.phase != GamePhase.SHOWING_RESULTS:
        return

    # Advance to next round
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
        asyncio.create_task(auto_finish_final_test(room_code))
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


@sio.on('next_round')
async def handle_next_round(sid, data):
    """Move to next round"""
    room = get_player_room(sid)

    # Only host can proceed
    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yöneticisi devam edebilir!'}, room=sid)
        return

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
        }, room=room.room_code)

        # Start timeout for final test (120 seconds)
        asyncio.create_task(auto_finish_final_test(room.room_code))
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
        }, room=room.room_code)


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

    # Send results with the same questions list
    await sio.emit('game_over', {
        'final_scores': final_scores,
        'player_answers': player_answers,
        'leaderboard': room.get_leaderboard(),
        'questions_summary': [
            {
                'question': q['question_text'],
                'correct_answer': q['correct_answer']
            }
            for q in room.questions
        ]
    }, room=room.room_code)


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
                print(f"Room {room_code} reset (empty)")

        # Leave Socket.IO room
        await sio.leave_room(sid, room_code)

        # Remove from tracking
        if sid in socket_rooms:
            del socket_rooms[sid]

        print(f"Player left room {room_code}")


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

    # Only host can reset
    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece oyun yöneticisi odayı sıfırlayabilir!'}, room=sid)
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
        'message': 'Oda sıfırlandı. Ana sayfaya yönlendiriliyorsunuz...'
    }, room=room_code)

    print(f"Room {room_code} reset by host")


# Create ASGI application
socket_app = socketio.ASGIApp(sio)
