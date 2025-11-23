/**
 * Custom hook for Server-Sent Events (SSE)
 * Handles streaming story generation from the backend
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { GraphData } from '@/types';

export interface UseSSEResult {
  streamingText: string;
  graphData: GraphData | null;
  isStreaming: boolean;
  error: Error | null;
  closeStream: () => void;
}

/**
 * Hook for handling SSE connections
 * 
 * @param url - The SSE endpoint URL (null to not connect)
 * @returns Stream state and control functions
 */
export function useSSE(url: string | null): UseSSEResult {
  const [streamingText, setStreamingText] = useState<string>('');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  
  // Function to close the stream manually
  const closeStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsStreaming(false);
    }
  }, []);
  
  useEffect(() => {
    // If no URL provided, don't connect
    if (!url) {
      return;
    }
    
    // Reset state
    setStreamingText('');
    setGraphData(null);
    setError(null);
    setIsStreaming(true);
    
    // Create EventSource
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;
    
    // Handle story chunks
    const handleChunk = (event: MessageEvent) => {
      setStreamingText((prev) => prev + event.data);
    };
    
    // Handle complete graph data
    const handleGraph = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setGraphData(data);
      } catch (err) {
        console.error('Failed to parse graph data:', err);
        setError(new Error('Failed to parse graph data'));
      }
    };
    
    // Handle errors
    const handleError = (event: Event) => {
      console.error('SSE error:', event);
      setError(new Error('Stream connection failed'));
      eventSource.close();
      setIsStreaming(false);
    };
    
    // Handle stream end
    const handleEnd = () => {
      eventSource.close();
      setIsStreaming(false);
    };
    
    // Register event listeners
    eventSource.addEventListener('story_chunk', handleChunk);
    eventSource.addEventListener('graph_data', handleGraph);
    eventSource.addEventListener('end', handleEnd);
    eventSource.addEventListener('error', handleError);
    
    // Cleanup on unmount or URL change
    return () => {
      eventSource.close();
      setIsStreaming(false);
    };
  }, [url]);
  
  return {
    streamingText,
    graphData,
    isStreaming,
    error,
    closeStream,
  };
}

