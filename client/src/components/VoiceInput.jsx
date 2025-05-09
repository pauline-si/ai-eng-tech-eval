import { useState, useRef } from "react"

export default function VoiceInput({ onVoiceMessage }) {
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])

  const handleStartRecording = async () => {
    if (!navigator.mediaDevices) {
      alert("Audio recording not supported in this browser.")
      return
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mediaRecorder = new window.MediaRecorder(stream)
    mediaRecorderRef.current = mediaRecorder
    audioChunksRef.current = []

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data)
      }
    }
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
      onVoiceMessage(audioBlob)
    }
    mediaRecorder.start()
    setIsRecording(true)
  }

  const handleStopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  return (
    <div className="flex items-center p-4 bg-gray-100 rounded-lg">
        <button
        onClick={isRecording ? handleStopRecording : handleStartRecording}
        className={`ml-2 p-2 rounded-lg text-white transition-colors
            ${isRecording
            ? "bg-red-500 hover:bg-red-600"
            : "bg-blue-500 hover:bg-blue-600"}
        `}
        title={isRecording ? "Stop Recording" : "Start Recording"}
        >
        {isRecording ? "⏹️ Stop" : "🎤 Talk"}
        </button>
    </div>
  )
}