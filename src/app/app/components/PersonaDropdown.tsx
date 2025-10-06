'use client';

import { useState, useRef, useEffect } from 'react';

interface Persona {
  name: string;
  short_description: string;
  color_theme: {
    background: string;
    button: string;
    button_hover: string;
    input: string;
    ring: string;
  };
}

interface PersonaDropdownProps {
  personas: Persona[];
  selectedPersona: string;
  onPersonaChange: (personaName: string) => void;
  disabled?: boolean;
  theme: Persona['color_theme'] | null;
}

export const PersonaDropdown = ({
  personas,
  selectedPersona,
  onPersonaChange,
  disabled,
  theme,
}: PersonaDropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (personaName: string) => {
    onPersonaChange(personaName);
    setIsOpen(false);
  };

  return (
    <div className="relative w-48" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full border border-gray-700 rounded-md p-2 flex justify-between items-center focus:outline-none focus:ring-2 disabled:cursor-not-allowed ${
          theme ? `${theme.input} ${theme.ring}` : 'bg-gray-800 focus:ring-blue-500'
        }`}
      >
        <span>{selectedPersona || 'Select Persona'}</span>
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
            {personas.map((persona) => (
              <li key={persona.name} className="group relative">
                <button
                  onClick={() => handleSelect(persona.name)}
                  className={`w-full text-left px-4 py-2 ${
                    theme ? theme.button_hover : 'hover:bg-gray-700'
                  }`}
                >
                  {persona.name}
                </button>
                {/* Tooltip on hover */}
                <div
                  className={`absolute left-full top-0 ml-2 w-64 p-2 border border-gray-700 rounded-md text-sm text-gray-300 opacity-0 group-hover:opacity-100 invisible group-hover:visible transition-opacity pointer-events-none ${
                    theme ? theme.input : 'bg-gray-900'
                  }`}
                >
                  <p className="font-bold">{persona.name}</p>
                  <p>{persona.short_description}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}; 