# -*- coding: utf-8 -*-
import socketio
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


@sio.event
async def connect(sid, environ):
    """When client connects"""
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    """When client disconnects"""
    print(f"Client disconnected: {sid}")

    # Remove player from room
    room = game_manager.get_room()
    if sid in room.players:
        room.remove_player(sid)

        # Notify other players
        await sio.emit('player_left', {
            'player_id': sid,
            'room_state': room.to_dict()
        }, room=room.room_code)

        # Reset room if empty
        if len(room.players) == 0:
            game_manager.reset_room()


@sio.on('join_game')
async def handle_join_game(sid, data):
    """Join the fixed game room"""
    player_name = data.get('player_name', 'Anonymous')

    room = game_manager.get_room()

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
    room = game_manager.get_room()

    # Only host can start
    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece host oyunu başlatabilir!'}, room=sid)
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
                'acceptable_answers': q.acceptable_answers,
                'category': q.category
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
    room = game_manager.get_room()

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
    room = game_manager.get_room()

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
        results = {
            'correct_answer': current_round.correct_answer,
            'player_votes': [],
            'leaderboard': room.get_leaderboard()
        }

        for player_id, player in room.players.items():
            vote_info = {
                'player_name': player.name,
                'voted_for': player.voted_answer,
                'was_correct': player.voted_answer == current_round.correct_answer,
                'fake_answer': current_round.fake_answers.get(player_id),
                'votes_received': sum(1 for v in current_round.votes.values()
                                     if v == current_round.fake_answers.get(player_id))
            }
            results['player_votes'].append(vote_info)

        await sio.emit('round_results', results, room=room.room_code)


@sio.on('next_round')
async def handle_next_round(sid, data):
    """Move to next round"""
    room = game_manager.get_room()

    # Only host can proceed
    if not room.players.get(sid) or not room.players[sid].is_host:
        await sio.emit('error', {'message': 'Sadece host devam edebilir!'}, room=sid)
        return

    room.next_round()

    if room.phase == GamePhase.FINAL_TEST:
        # Move to final test
        await sio.emit('final_test_phase', {
            'questions': [
                {
                    'index': i,
                    'question_text': q['question_text'],
                    'category': q.get('category', '')
                }
                for i, q in enumerate(room.questions)
            ]
        }, room=room.room_code)
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
    room = game_manager.get_room()

    success = room.submit_final_answer(sid, question_index, answer)

    if not success:
        await sio.emit('error', {'message': 'Cevap gönderilemedi!'}, room=sid)
        return

    await sio.emit('final_answer_submitted', {
        'question_index': question_index,
        'success': True
    }, room=sid)


@sio.on('finish_game')
async def handle_finish_game(sid, data):
    """Finish game and calculate final scores for individual player"""
    room = game_manager.get_room()

    # Calculate only this player's final score
    player = room.players.get(sid)
    if not player:
        await sio.emit('error', {'message': 'Oyuncu bulunamadı!'}, room=sid)
        return

    # Calculate this player's final test score using check_answer
    correct_count = 0
    for i, question in enumerate(room.questions):
        user_answer = player.final_answers.get(i, "")
        if check_answer(user_answer, question['correct_answer'], question.get('acceptable_answers')):
            correct_count += 1

    # Add bonus points
    bonus_score = correct_count * 500
    player.score += bonus_score

    # Send results only to this player
    await sio.emit('game_over', {
        'final_scores': {
            sid: {
                'correct_count': correct_count,
                'bonus_score': bonus_score,
                'total_score': player.score
            }
        },
        'leaderboard': room.get_leaderboard(),
        'questions_summary': [
            {
                'question': q['question_text'],
                'correct_answer': q['correct_answer']
            }
            for q in room.questions
        ]
    }, room=sid)


# Create ASGI application
socket_app = socketio.ASGIApp(sio)
