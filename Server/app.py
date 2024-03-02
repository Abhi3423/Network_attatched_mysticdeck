from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
from flask_cors import CORS, cross_origin
import json
import re


app = Flask(__name__,template_folder='templates')
app.debug = True
app.config['SECRET_KEY'] = 'secretkey'
app.config['SESSION_TYPE'] = 'filesystem'
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
Session(app)

socketio = SocketIO(app, manage_session=False)


@app.route('/')
def index():
      return {'user_created':'true'}

@app.route('/create_room', methods=['GET','POST'])
def create_room():
    if(request.method=='POST'):
      creator_id = request.form['creator_id']
      room_id = request.form['room_id']
      print(room_id)
      with open('database/rooms.json', 'r') as f:
        rooms_data = json.load(f)
        
      # Create a new room
      if room_id not in rooms_data:
        session['room_id'] = room_id
        session['creator_id'] = creator_id
        print(session)
        rooms_data[room_id] = {'creator_id': [creator_id], 'users': []}
        with open('database/rooms.json','w') as y:
            json.dump(rooms_data, y)
        return {"session":session,"room_id": session.get('room_id')}
      else: 
        return f"Room {room_id} already exists."
    else:
        # Return specific data from the session
        return {"room_id": session.get('room_id'), "creator_id": session.get('creator_id')}


@app.route('/score_update', methods=['POST'])
def score_update():
    room_id = request.form['room_id']
    # Load data from the JSON file
    with open('database/game.json', 'r') as f:
        rooms_data = json.load(f)

    # Assuming you have room_id, username, and score defined
    if room_id in rooms_data:
        # Access the parameter_values for the specific room
        parameter_values = rooms_data[room_id]['current_values']['parameter_values']
        
        # Find the user with the highest score
        highest_score = max(parameter_values.values())
        winner = None
        for user, score in parameter_values.items():
            print(score)
            print(highest_score)
            if score == highest_score:
                winner = user
            print(winner)
        # Add 5 to the score of the winner
        rooms_data[room_id]['scores'][winner] += 5
        
    # Save the updated data back to the JSON file
    with open('database/game.json', 'w') as f:
        json.dump(rooms_data, f, indent=4)
        
    return {'scores':rooms_data[room_id]['scores'],'winner':winner}


@socketio.on('connect',namespace='/create_room')
def test_connect():
  print('Client connected')
  emit('message', {'data': 'Connected'})


@socketio.on('join_room', namespace='/create_room')
def handle_join_room(data):
    print('join room')
    username = data['username']
    room_id = data['room_id']
    print(room_id)
    with open('database/rooms.json', 'r') as f:
        rooms_data = json.load(f)
        
    # print(room_id)
    if room_id in rooms_data:
         # Initialize the 'users' list if it's not already present
        if 'users' not in rooms_data[room_id]:
           rooms_data[room_id]['users'] = []
    
        # Add the user to the room
        rooms_data[room_id]['users'].append(username)
        join_room(room_id)
        # session.sessionid['username'] = username
        # # Create a session for the user
        # session['username'] = username
        
        # Save the updated rooms_data back to the JSON file
        with open('database/rooms.json', 'w') as f:
          json.dump(rooms_data, f, indent=4)
           
        # Emit a message to the room
        message = f"{username} has joined the room."
        emit('status', {'users': rooms_data[room_id]['users'],message:message}, room=room_id)
    else:
        print('room does not exist')
        # Emit a message to the room
        message = "Room does not exist."
        emit('status', {message:message})


@socketio.on('leave_room', namespace='/create_room')
def handle_leave_room(data):
    username = data['username']
    room_id = data['room_id']
    print(data)
    with open('database/rooms.json', 'r') as f:
        rooms_data = json.load(f)
    with open('database/game.json', 'r') as f:
        game_data = json.load(f)
        
    # Remove the user from the room
    if room_id in rooms_data and username in rooms_data[room_id]['users']:
        rooms_data[room_id]['users'].remove(username)
        game_data[room_id]['scores'].pop(username, None)
        # If the room is empty, remove it
        if not rooms_data[room_id]['users']:
            del rooms_data[room_id]
            del game_data[room_id]
            
            # Delete the session for the user
            if 'username' in session and session['username'] == username:
                session.pop('username', None)
                session.pop('room_id', None)

        with open('database/rooms.json', 'w') as f:
            json.dump(rooms_data, f, indent=4)
        
        with open('database/game.json', 'w') as f:
            json.dump(game_data, f, indent=4)

        message = f"{username} has left the room."
        emit('status', {'message': message}, room=room_id)
        
        
@socketio.on('play_call', namespace='/create_room')
def play_call(message):
    room = message['room_id']
    emit('call', {'parameter_name': message['parameter_name'],'parameter_value': message['parameter_value']}, room=room)


@socketio.on('members_play_call', namespace='/create_room')
def members_play_call(message):
    room_id = message['room_id']
    score = message['score']
    username = message['username']
    with open('database/game.json', 'r') as f:
        rooms_data = json.load(f)

    if room_id in rooms_data:
        # Access the scores dictionary for the specific room
        scores = rooms_data[room_id]['scores']

        # Check if the username is already present in the scores dictionary
        if username not in scores:
          # If the username is not present, append it with the corresponding score
          scores[username] = score

        rooms_data[room_id]['current_values']['parameter_name'] = message['parameter_name']
        
        # Extract only the numeric portion from parameter_value
        numeric_value = re.sub(r'\D', '', message['parameter_value'])
        
        # Convert the numeric value to an integer (assuming it represents an integer)
        numeric_value = int(numeric_value)
        
        rooms_data[room_id]['current_values']['parameter_values'][message['username']] = numeric_value

 
    with open('database/game.json', 'w') as f:
        json.dump(rooms_data, f, indent=4)

@socketio.on('theme_selection',namespace='/create_room')
def theme_selection(data):
    themeselected = data['theme_selected']
    topicselected = data['topic_selected']
    room_id = data['room_id']
    print(themeselected)
    print(topicselected)
    # room = session.get('room_id')
    with open('database/game.json', 'r') as f:
        game_data = json.load(f)
    game_data[room_id] = {'chance': "",'current_values':{'parameter_name':"",'parameter_values':{}}, 'scores': {},'theme_selected':themeselected,'topic_selected':topicselected}
    with open('database/game.json','w') as y:
        json.dump(game_data, y)
    emit('theme_sent',{'theme_selected':themeselected,'topic_selected':topicselected},room=room_id)







@app.route('/chat')
def chat():
    return render_template('chat.html')

@socketio.on('join', namespace='/chat')
def join(message):
    room = session.get('room')
    join_room(room)
    emit('status', {'msg':  session.get('username') + ' has entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    room = session.get('room')
    emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)


if __name__ == '__main__':

    socketio.run(app, port=8000)