"use client"

import { useState } from "react"

export default function ChatInput({ onSendMessage }) {
    const [inputValue, setInputValue] = useState("")
    
    const handleInputChange = (event) => {
        setInputValue(event.target.value)
    }
    
    const handleSendMessage = () => {
        if (inputValue.trim() !== "") {
        onSendMessage(inputValue)
        setInputValue("")
        }
    }
    
    const handleKeyDown = (event) => {
        if (event.key === "Enter") {
        handleSendMessage()
        }
    }
    
    return (
        <div className="flex items-center flex-grow p-4">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="flex-grow w-0 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSendMessage}
            className="ml-2 p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 cursor-pointer transition-colors"
          >
            Send
          </button>
        </div>
    )
}
