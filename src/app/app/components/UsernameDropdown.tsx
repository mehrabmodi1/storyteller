'use client';

import { useState, useRef, useEffect } from 'react';

interface ColorTheme {
  background: string;
  button: string;
  button_hover: string;
  input: string;
  ring: string;
}

interface UsernameDropdownProps {
  currentUsername: string;
  onUsernameChange: (username: string) => void;
  disabled?: boolean;
  theme: ColorTheme | null;
}

export const UsernameDropdown = ({
  currentUsername,
  onUsernameChange,
  disabled,
  theme,
}: UsernameDropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [usernames, setUsernames] = useState<string[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load usernames from localStorage on mount (client-side only)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('storyteller_usernames');
      setUsernames(saved ? JSON.parse(saved) : []);
    }
  }, []);

  const saveUsername = (username: string) => {
    setUsernames((prev) => {
      if (!prev.includes(username)) {
        const updated = [...prev, username];
        if (typeof window !== 'undefined') {
          localStorage.setItem('storyteller_usernames', JSON.stringify(updated));
        }
        return updated;
      }
      return prev;
    });
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setIsAddingNew(false);
        setNewUsername('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (username: string) => {
    onUsernameChange(username);
    setIsOpen(false);
    setIsAddingNew(false);
    setNewUsername('');
  };

  const handleAddNew = () => {
    setIsAddingNew(true);
  };

  const handleSubmitNew = (e: React.FormEvent) => {
    e.preventDefault();
    if (newUsername.trim()) {
      saveUsername(newUsername.trim());
      handleSelect(newUsername.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsAddingNew(false);
      setNewUsername('');
    }
  };

  return (
    <div className="relative w-40" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full border border-gray-700 rounded-md p-2 flex justify-between items-center focus:outline-none focus:ring-2 disabled:cursor-not-allowed text-sm ${
          theme ? `${theme.input} ${theme.ring}` : 'bg-gray-800 focus:ring-blue-500'
        }`}
      >
        <span className="truncate">{currentUsername || 'Select User'}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'transform rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>

      {isOpen && (
        <div
          className={`absolute z-20 w-full mt-1 border border-gray-700 rounded-md shadow-lg ${
            theme ? theme.input : 'bg-gray-800'
          }`}
        >
          <ul>
            {/* Add New Username Option */}
            <li className="border-b border-gray-700">
              <button
                onClick={handleAddNew}
                className={`w-full text-left px-4 py-2 text-sm ${
                  theme ? theme.button_hover : 'hover:bg-gray-700'
                }`}
              >
                + Add New User
              </button>
            </li>
            
            {/* Existing Usernames */}
            {usernames.map((username) => (
              <li key={username}>
                <button
                  onClick={() => handleSelect(username)}
                  className={`w-full text-left px-4 py-2 text-sm ${
                    username === currentUsername ? 'font-semibold' : ''
                  } ${
                    theme ? theme.button_hover : 'hover:bg-gray-700'
                  }`}
                >
                  {username}
                </button>
              </li>
            ))}
          </ul>

          {/* Add New Username Form */}
          {isAddingNew && (
            <div className="p-3 border-t border-gray-700">
              <form onSubmit={handleSubmitNew}>
                <input
                  type="text"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter username..."
                  className={`w-full px-2 py-1 text-sm border border-gray-600 rounded focus:outline-none focus:ring-1 ${
                    theme ? `${theme.input} ${theme.ring}` : 'bg-gray-700 focus:ring-blue-500'
                  }`}
                  autoFocus
                />
                <div className="flex gap-1 mt-2">
                  <button
                    type="submit"
                    className={`px-2 py-1 text-xs rounded ${
                      theme ? `${theme.button} ${theme.button_hover}` : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                  >
                    Add
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsAddingNew(false);
                      setNewUsername('');
                    }}
                    className="px-2 py-1 text-xs rounded bg-gray-600 hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
}; 