/**
 * Generic base dropdown component
 * Eliminates code duplication across all dropdown implementations
 * Handles: click-outside, keyboard navigation, theming, tooltips
 */

import React, { useState, useRef, useEffect, ReactNode } from 'react';
import type { ColorTheme } from '@/types';

export interface BaseDropdownProps<T> {
  items: T[];
  selectedItem: T | null;
  onSelect: (item: T) => void;
  getLabel: (item: T) => string;
  getKey: (item: T) => string;
  renderTooltip?: (item: T) => ReactNode;
  disabled?: boolean;
  theme?: ColorTheme | null;
  placeholder?: string;
  width?: string;
}

export function BaseDropdown<T>({
  items,
  selectedItem,
  onSelect,
  getLabel,
  getKey,
  renderTooltip,
  disabled = false,
  theme = null,
  placeholder = 'Select...',
  width = 'w-48',
}: BaseDropdownProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);
  const [hoveredItem, setHoveredItem] = useState<T | null>(null);
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setHighlightedIndex((prev) => (prev < items.length - 1 ? prev + 1 : prev));
          break;
        case 'ArrowUp':
          event.preventDefault();
          setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case 'Enter':
          event.preventDefault();
          if (highlightedIndex >= 0 && highlightedIndex < items.length) {
            handleSelect(items[highlightedIndex]);
          }
          break;
        case 'Escape':
          event.preventDefault();
          setIsOpen(false);
          setHighlightedIndex(-1);
          buttonRef.current?.focus();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, highlightedIndex, items]);

  const handleSelect = (item: T) => {
    onSelect(item);
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const handleToggle = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
      if (!isOpen) {
        // Reset highlighted index when opening
        const selectedIndex = selectedItem ? items.findIndex((item) => getKey(item) === getKey(selectedItem)) : -1;
        setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : 0);
      }
    }
  };

  const selectedLabel = selectedItem ? getLabel(selectedItem) : placeholder;

  return (
    <div className={`relative ${width}`} ref={dropdownRef}>
      {/* Dropdown Button */}
      <button
        ref={buttonRef}
        onClick={handleToggle}
        disabled={disabled}
        className={`w-full border border-gray-700 rounded-md p-2 flex justify-between items-center focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${
          theme ? `${theme.input} ${theme.ring}` : 'bg-gray-800 focus:ring-blue-500'
        }`}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="truncate">{selectedLabel}</span>
        <svg
          className={`w-4 h-4 transition-transform flex-shrink-0 ml-2 ${isOpen ? 'transform rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={`absolute z-20 w-full mt-1 border border-gray-700 rounded-md shadow-lg max-h-60 overflow-y-auto scrollbar-thin ${
            theme ? theme.input : 'bg-gray-800'
          }`}
          role="listbox"
        >
          <ul>
            {items.map((item, index) => {
              const itemKey = getKey(item);
              const itemLabel = getLabel(item);
              const isSelected = selectedItem && getKey(selectedItem) === itemKey;
              const isHighlighted = index === highlightedIndex;

              return (
                <li
                  key={itemKey}
                  className="group relative"
                  onMouseEnter={() => {
                    setHighlightedIndex(index);
                    setHoveredItem(item);
                  }}
                  onMouseLeave={() => setHoveredItem(null)}
                >
                  <button
                    onClick={() => handleSelect(item)}
                    className={`w-full text-left px-4 py-2 transition-colors ${
                      isSelected
                        ? 'bg-blue-600 text-white'
                        : isHighlighted
                        ? 'bg-gray-700'
                        : 'hover:bg-gray-700'
                    }`}
                    role="option"
                    aria-selected={isSelected}
                  >
                    {itemLabel}
                  </button>

                  {/* Tooltip */}
                  {renderTooltip && hoveredItem === item && (
                    <div className="absolute left-full top-0 ml-2 z-30 w-64 bg-gray-900 text-white text-sm p-3 rounded-md shadow-lg pointer-events-none">
                      {renderTooltip(item)}
                      {/* Arrow */}
                      <div className="absolute right-full top-3 w-0 h-0 border-t-4 border-t-transparent border-b-4 border-b-transparent border-r-4 border-r-gray-900" />
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

