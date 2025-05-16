import ChatInput from "./components/ChatInput"
import TodoList from "./components/TodoList"
import VoiceInput from "./components/VoiceInput"
import ChatFeed from "./components/ChatFeed"
import { useState, useRef } from "react"

const startingTodos = [
  { id: 1, text: "Buy groceries", status: "pending" },
  { id: 2, text: "Walk the dog", status: "pending" },
  { id: 3, text: "Finish project", status: "pending" },
]

function App() {
  const [messages, setMessages] = useState([])
  const [todos, setTodos] = useState(startingTodos)
  const audioRef = useRef(null)

  const handleSendMessage = (message) => {
    setMessages((prevMessages) => [...prevMessages, message])
    fetch("http://localhost:8000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        todo_list: todos,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        setMessages((prevMessages) => [...prevMessages, data.response]);
        setTodos(prev => [
          ...prev,
          ...data.updated_todo_list
            .filter(item => !prev.some(t => t.text === item.text))
            .map(item => ({ ...item, id: crypto.randomUUID() }))
        ]);
        handlePlayAudio(data.response);
      })
      .catch((error) => {
        console.error("Error sending message:", error)
      })
  }
  // Play audio for a specific message
  const handlePlayAudio = (text) => {
    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
    }
    fetch("http://localhost:8000/api/chat/audio", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text })
    })
      .then((response) => response.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audioRef.current = audio
        audio.play()
      })
  }

  // Stop audio playback
  const handleStopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
    }
  }

  // Transcribe voice input
  const handleVoiceMessage = async (audioBlob) => {
    const formData = new FormData()
    formData.append("audio", audioBlob, "audio.webm")
    const response = await fetch("http://localhost:8000/api/chat/transcribe", {
      method: "POST",
      body: formData,
    })
    const data = await response.json()
    if (data.text) {
      handleSendMessage(data.text)
    }
  }

  return (
    <div className="container justify-self-center mt-4">
      <div className="flex bg-gray-100">
        <div className="min-w-[500px] mr-4">
          <TodoList todos={todos} setTodos={setTodos} />
        </div>
        <div className="flex-1">
          <div className="flex">
            <ChatInput onSendMessage={handleSendMessage} />
            <VoiceInput onVoiceMessage={handleVoiceMessage} />
          </div>
          <ChatFeed
            messages={messages}
            onPlayAudio={handlePlayAudio}
            onStopAudio={handleStopAudio}
          />
        </div>
      </div>
    </div>
  )
}

export default App
