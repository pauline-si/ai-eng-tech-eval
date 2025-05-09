"use client"
import { Volume2, Square } from "lucide-react"

export default function ChatFeed({ messages, onPlayAudio, onStopAudio }) {
    return (
        <div className="flex flex-col h-full p-4">
            <div className="flex-grow overflow-y-auto">
                {messages.map((message, index) => (
                    <div key={index} className="mb-2 items-center space-x-2">
                        <div className="p-2 bg-white rounded-lg shadow-md flex-1">
                            {message}
                        </div>
                        <button
                            onClick={() => onPlayAudio(message)}
                            className="px-2 py-1 text-gray-400 cursor-pointer rounded transition-colors duration-150 hover:text-blue-600 active:text-blue-700 focus:outline-none"
                        >
                            <Volume2 className="w-4 h-4" />
                            <span className="sr-only">Play Audio</span>
                        </button>
                        <button
                            onClick={onStopAudio}
                            className="hidden px-2 py-1 text-gray-400 cursor-pointer rounded transition-colors duration-150 hover:text-blue-600 active:text-blue-700 focus:outline-none"
                        >
                            <Square className="w-4 h-4" />
                            <span className="sr-only">Stop Audio</span>
                        </button>
                    </div>
                ))}
            </div>
        </div>
    )
}