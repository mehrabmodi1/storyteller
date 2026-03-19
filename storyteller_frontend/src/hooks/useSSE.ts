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
  guardrailMessage: string | null;
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
  const [guardrailMessage, setGuardrailMessage] = useState<string | null>(null);
  
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
    setGuardrailMessage(null);
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
    
    // Handle backend error events (event: error with data)
    const handleBackendError = (event: MessageEvent) => {
      console.error('SSE backend error:', event.data);
      setError(new Error(event.data || 'Stream error'));
      eventSource.close();
      setIsStreaming(false);
    };

    // Handle connection errors (native EventSource error)
    const handleConnectionError = (event: Event) => {
      console.error('SSE connection error:', event);
      setError(new Error('Stream connection failed'));
      eventSource.close();
      setIsStreaming(false);
    };
    
    // Handle stream end
    const handleEnd = () => {
      eventSource.close();
      setIsStreaming(false);
    };

    // Handle guardrail rejection
    const handleGuardrailReject = (event: MessageEvent) => {
      setGuardrailMessage(event.data);
      eventSource.close();
      setIsStreaming(false);
    };

    // Register event listeners
    eventSource.addEventListener('story_chunk', handleChunk);
    // Backend sends final graph on the default 'message' event; keep legacy name as fallback.
    eventSource.addEventListener('message', handleGraph);
    eventSource.addEventListener('graph_data', handleGraph);
    eventSource.addEventListener('end', handleEnd);
    eventSource.addEventListener('error', handleBackendError as EventListener);
    eventSource.addEventListener('guardrail_reject', handleGuardrailReject as EventListener);
    eventSource.onerror = handleConnectionError;

    // Cleanup on unmount or URL change
    return () => {
      eventSource.removeEventListener('guardrail_reject', handleGuardrailReject as EventListener);
      eventSource.close();
      setIsStreaming(false);
    };
  }, [url]);
  
  return {
    streamingText,
    graphData,
    isStreaming,
    error,
    guardrailMessage,
    closeStream,
  };
}

