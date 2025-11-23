/**
 * Username selector dropdown
 * Uses BaseDropdown to eliminate code duplication
 * Supports adding new usernames via input
 */

import React, { useState } from 'react';
import { BaseDropdown } from './BaseDropdown';
import { useApp } from '@/context/AppContext';
import { useLocalStorage } from '@/hooks/useLocalStorage';

interface UsernameItem {
  value: string;
  isNew?: boolean;
}

export function UsernameDropdown() {
  const { username, setUsername, theme } = useApp();
  const [savedUsernames, setSavedUsernames] = useLocalStorage<string[]>('storyteller_usernames', []);
  const [showInput, setShowInput] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  
  // Build items list with existing usernames + "Add New" option
  const items: UsernameItem[] = [
    ...savedUsernames.map((u) => ({ value: u, isNew: false })),
    { value: '+ Add New', isNew: true },
  ];
  
  const selectedItem = username ? { value: username, isNew: false } : null;
  
  const handleSelect = (item: UsernameItem) => {
    console.log('[UsernameDropdown] handleSelect called with:', item);
    if (item.isNew) {
      console.log('[UsernameDropdown] Showing input for new username');
      setShowInput(true);
    } else {
      console.log('[UsernameDropdown] Setting username to:', item.value);
      setUsername(item.value);
    }
  };
  
  const handleAddUsername = () => {
    const trimmed = newUsername.trim();
    if (trimmed && !savedUsernames.includes(trimmed)) {
      setSavedUsernames([...savedUsernames, trimmed]);
      setUsername(trimmed);
    }
    setShowInput(false);
    setNewUsername('');
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddUsername();
    } else if (e.key === 'Escape') {
      setShowInput(false);
      setNewUsername('');
    }
  };
  
  if (showInput) {
    return (
      <div className="w-48 relative">
        <input
          type="text"
          value={newUsername}
          onChange={(e) => setNewUsername(e.target.value)}
          onKeyDown={handleKeyPress}
          onBlur={handleAddUsername}
          autoFocus
          placeholder="Enter username"
          className={`w-full border border-gray-700 rounded-md p-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${
            theme ? `${theme.input} ${theme.ring}` : 'bg-gray-800 focus:ring-blue-500'
          }`}
        />
      </div>
    );
  }
  
  return (
    <BaseDropdown<UsernameItem>
      items={items}
      selectedItem={selectedItem}
      onSelect={handleSelect}
      getLabel={(item) => item.value}
      getKey={(item) => item.value}
      theme={theme}
      placeholder="Select Username"
      width="w-48"
    />
  );
}

