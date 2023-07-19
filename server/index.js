require('dotenv').config();
const express = require('express');
const axios = require('axios');
const app = express();
const http = require('http');
const cors = require('cors');
const { Server } = require('socket.io');
// const harperSaveMessage = require('./services/harper-save-message');
// const harperGetMessages = require('./services/harper-get-messages');
const leaveRoom = require('./utils/leave-room'); 
const { spawn } = require('child_process');


app.use(cors());
const server = http.createServer(app);

const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST'],
  },
});

const CHAT_BOT = 'ChatBot';
let chatRoom = ''; 
let allUsers = []; 

io.on('connection', (socket) => {
  console.log(`User connected ${socket.id}`);


  socket.on('join_room', (data) => {
    const { username, room } = data; 
    socket.join(room);

    let __createdtime__ = Date.now(); 
    console.log( __createdtime__)
    socket.to(room).emit('receive_message', {
      message: `${username} has joined the chat room`,
      username: CHAT_BOT,
      __createdtime__,
    });
 
    socket.emit('receive_message', {
      message: `Welcome ${username}`,
      username: CHAT_BOT,
      __createdtime__,
    });

    chatRoom = room;
    allUsers.push({ id: socket.id, username, room });
    chatRoomUsers = allUsers.filter((user) => user.room === room);
    socket.to(room).emit('chatroom_users', chatRoomUsers);
    socket.emit('chatroom_users', chatRoomUsers);
  });

  socket.on('send_message', (data) => {
    const { message, username, room, __createdtime__ } = data;
    console.log(data)
    const newData={
      message:message,
      username:username,
      room:room,
      __createdtime__:__createdtime__,
      own_message:true
    }
    io.in(room).emit('receive_message', newData); 
    //will save the data


    // Call the chatbot
     //runPythonScript(message,room);

     //call the api
     chatRoomUsers = allUsers.filter((user) => user.room === room);
     if(chatRoomUsers.length<2){
      runPythonApi(message,room);
     }
     

  });

  function runPythonScript(message,room) {
    const pythonScript = spawn('python', ['-u', '../python/main.py', message]);
  
    // Print the output of the Python script
    let output = '';
    pythonScript.stdout.on('data', (data) => {
      output += data.toString();
    });
  
    // Handle any error that occurs while running the script
    pythonScript.stderr.on('data', (data) => {
      console.error(`Error: ${data}`);
    });
  
    // Print the final output when the script finishes
    pythonScript.on('close', () => {
      const lines = output.trim().split('\n');
      const finalOutput = lines[lines.length - 1];
      console.log(finalOutput);
      let __createdtime__ = Date.now(); 
      io.in(room).emit('receive_message', {
        message: finalOutput,
        username: CHAT_BOT,
        __createdtime__,
      });

    });
  }


function runPythonApi(message,room) {

 axios.post('http://127.0.0.1:5000/redsam/api/v1.0/classify', {
  sentence: message
})
  .then(response => {
    console.log(response.data);
    // Access the response data and handle it accordingly
    const intent = response.data.intent;
    const probability = response.data.probability;
    const botResponse = response.data.response;
    // Do something with the intent, probability, and botResponse
    let __createdtime__ = Date.now(); 
    io.in(room).emit('receive_message', {
      message: botResponse,
      username: CHAT_BOT,
      __createdtime__,
    });
  })
  .catch(error => {
    console.error(error);
    // Handle the error
  });

  }
  

  socket.on('leave_room', (data) => {
    const { username, room } = data;
    socket.leave(room);
    const __createdtime__ = Date.now();
    allUsers = leaveRoom(socket.id, allUsers);
    socket.to(room).emit('chatroom_users', allUsers);
    socket.to(room).emit('receive_message', {
      username: CHAT_BOT,
      message: `${username} has left the chat`,
      __createdtime__,
    });
    console.log(`${username} has left the chat`);
  });

  socket.on('disconnect', () => {
    console.log('User disconnected from the chat');
    const user = allUsers.find((user) => user.id == socket.id);
    if (user?.username) {
      allUsers = leaveRoom(socket.id, allUsers);
      socket.leave(chatRoom);
      socket.to(chatRoom).emit('chatroom_users', allUsers);
      socket.to(chatRoom).emit('receive_message', {
        message: `${user.username} has disconnected from the chat.`,
      });
    }
  });
});

server.listen(4000, () => 'Server is running on port 4000');
