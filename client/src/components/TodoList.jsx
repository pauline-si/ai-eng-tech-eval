"use client"

import { useState } from "react"
import { Trash2 } from "lucide-react"

export default function TodoList({ todos, setTodos }) {
  const [inputValue, setInputValue] = useState("")

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && inputValue.trim() !== "") {
      setTodos([...todos, { id: Date.now(), text: inputValue, status: "pending" }])
      setInputValue("")
    }
  }

  const toggleTodo = (id) => {
    setTodos(
      todos.map((todo) => {
        if (todo.id === id) {
          return { ...todo, status: todo.status === "done" ? "pending" : "done" }
        }
        return todo
      }),
    )
  }

  const deleteTodo = (id) => {
    setTodos(todos.filter((todo) => todo.id !== id))
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Todo List</h1>

      <div className="mb-4">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add a new task and press Enter"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <ul className="space-y-2">
        {todos.map((todo) => (
          <li
            key={todo.id}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={todo.status === "done"}
                onChange={() => toggleTodo(todo.id)}
                className="h-5 w-5 text-blue-600 rounded mr-3 cursor-pointer"
              />
              <span className={`${todo.status === "done" ? "line-through text-gray-400" : "text-gray-800"}`}>{todo.text}</span>
            </div>
            <button
              onClick={() => deleteTodo(todo.id)}
              className="text-red-500 hover:text-red-700 focus:outline-none"
              aria-label="Delete todo"
            >
              <Trash2 size={18} />
            </button>
          </li>
        ))}
      </ul>

      {todos.length === 0 && <p className="text-center text-gray-500 mt-4">No tasks yet. Add one above!</p>}
    </div>
  )
}
