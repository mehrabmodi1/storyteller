/**
 * Custom hook for Server-Sent Events (SSE)
 * Handles streaming story generation from the backend
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { GraphData } from '@/types';

const SSE_EVENT = {
  STORY_CHUNK: 'story_chunk',
  MESSAGE: 'message',
  GRAPH_DATA: 'graph_data',
  END: 'end',
  ERROR: 'error',
  GUARDRAIL_REJECT: 'guardrail_reject',
} as const;

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
    
    setStreamingText('');
    setGraphData(null);
    setError(null);
    setGuardrailMessage(null);
    setIsStreaming(true);
    
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;
    
    const handleChunk = (event: MessageEvent) => {
      setStreamingText((prev) => prev + event.data);
    };
    
    const handleGraph = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setGraphData(data);
      } catch (err) {
        console.error('Failed to parse graph data:', err);
        setError(new Error('Failed to parse graph data'));
      }
    };
    
    const handleBackendError = (event: MessageEvent) => {
      console.error('SSE backend error:', event.data);
      setError(new Error(event.data || 'Stream error'));
      eventSource.close();
      setIsStreaming(false);
    };

    const handleConnectionError = (event: Event) => {
      console.error('SSE connection error:', event);
      setError(new Error('Stream connection failed'));
      eventSource.close();
      setIsStreaming(false);
    };
    
    const handleEnd = () => {
      eventSource.close();
      setIsStreaming(false);
    };

    const handleGuardrailReject = (event: MessageEvent) => {
      setGuardrailMessage(event.data);
      eventSource.close();
      setIsStreaming(false);
    };

    eventSource.addEventListener(SSE_EVENT.STORY_CHUNK, handleChunk);
    eventSource.addEventListener(SSE_EVENT.MESSAGE, handleGraph);
    eventSource.addEventListener(SSE_EVENT.GRAPH_DATA, handleGraph);
    eventSource.addEventListener(SSE_EVENT.END, handleEnd);
    eventSource.addEventListener(SSE_EVENT.ERROR, handleBackendError as EventListener);
    eventSource.addEventListener(SSE_EVENT.GUARDRAIL_REJECT, handleGuardrailReject as EventListener);
    eventSource.onerror = handleConnectionError;

    return () => {
      eventSource.removeEventListener(SSE_EVENT.STORY_CHUNK, handleChunk);
      eventSource.removeEventListener(SSE_EVENT.MESSAGE, handleGraph);
      eventSource.removeEventListener(SSE_EVENT.GRAPH_DATA, handleGraph);
      eventSource.removeEventListener(SSE_EVENT.END, handleEnd);
      eventSource.removeEventListener(SSE_EVENT.ERROR, handleBackendError as EventListener);
      eventSource.removeEventListener(SSE_EVENT.GUARDRAIL_REJECT, handleGuardrailReject as EventListener);
      eventSource.onerror = null;
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

