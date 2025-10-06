'use client';

import { useState, useCallback, useEffect, createContext, useContext } from 'react';
import ReactFlow, {
  Controls,
  Background,
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  NodeMouseHandler,
} from 'reactflow';
import ELK, { ElkNode, LayoutOptions } from 'elkjs/lib/elk.bundled.js';
import TextareaAutosize from 'react-textarea-autosize';
import { PersonaDropdown } from './components/PersonaDropdown';
import { UsernameDropdown } from './components/UsernameDropdown';
import { JourneyDropdown } from './components/JourneyDropdown';
import { CorpusDropdown } from './components/CorpusDropdown';

import 'reactflow/dist/style.css';

// --- Theme and Persona Definitions ---
interface ColorTheme {
  background: string;
  button: string;
  button_hover: string;
  input: string;
  ring: string;
}
interface Persona {
  name: string;
  short_description: string;
  color_theme: ColorTheme;
}

interface Corpus {
  name: string;
  display_name: string;
  description: string;
  is_active: boolean;
  chunk_count: number;
  last_processed: string | null;
  needs_rebuild: boolean;
  missing_components: string[];
}

const elk = new ELK();

const elkLayoutOptions: LayoutOptions = {
  'elk.algorithm': 'layered',
  'elk.direction': 'DOWN',
  'elk.spacing.nodeNode': '150',
  'elk.layered.spacing.nodeNodeBetweenLayers': '200',
  'elk.alignment': 'CENTER',
};

// --- New Context for In-Place Editing ---
interface EditingContextType {
  editingNodeId: string | null;
  setEditingNodeId: (id: string | null) => void;
  handleLabelChange: (nodeId: string, newLabel: string) => void;
  handleEditSubmit: (nodeId: string, prompt: string) => void;
  activeTheme: ColorTheme | null;
}
const EditingContext = createContext<EditingContextType | null>(null);

// Define the shape of the data associated with each node
interface CustomNodeData {
  label: string;
  story?: string;
  isChoice?: boolean;
  image_url?: string;
}

// --- Custom Node Components ---

const StoryNode = ({ data }: { data: CustomNodeData }) => {
  const { activeTheme } = useContext(EditingContext)!;
  return (
    <div className={`p-4 rounded-lg shadow-lg ring-1 ${activeTheme ? 'ring-white/20' : 'ring-white/10'} ${activeTheme?.input || 'bg-gray-800'}`} style={{ width: 400 }}>
      <Handle type="target" position={Position.Top} isConnectable={false} />
      {data.image_url && (
        <img 
          src={data.image_url} 
          alt={data.label} 
          className="w-full h-auto rounded-md mb-4"
        />
      )}
      <div style={{maxHeight: 200, overflowY: 'auto'}}>
        <h3 className="text-lg font-bold mb-2 text-gray-100">{data.label}</h3>
        <p className="text-sm text-gray-300 whitespace-pre-wrap">{data.story}</p>
      </div>
      <Handle type="source" position={Position.Bottom} isConnectable={false} />
    </div>
  );
};

const ChoiceNode = ({ id, data }: { id: string, data: CustomNodeData }) => {
  const context = useContext(EditingContext);
  if (!context) return null; // Should not happen within the provider

  const { editingNodeId, setEditingNodeId, handleLabelChange, handleEditSubmit, activeTheme } = context;
  const isEditing = editingNodeId === id;

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleEditSubmit(id, data.label);
      setEditingNodeId(null);
    }
  };

  // Render an input field if the node is in editing mode
  if (isEditing) {
    return (
      <div className={`p-4 rounded-lg shadow-lg flex justify-center items-center ring-2 ${activeTheme?.ring || 'ring-blue-500'}`} style={{ width: 250 }}>
        <Handle type="target" position={Position.Top} isConnectable={false} />
        <TextareaAutosize
          value={data.label}
          onChange={(e) => handleLabelChange(id, e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={() => setEditingNodeId(null)}
          className={`w-full text-center bg-transparent outline-none nodrag resize-none ${
            activeTheme ? 'text-white' : 'text-gray-900'
          }`}
          autoFocus
          maxRows={5} // Prevents the node from becoming excessively large
        />
        <Handle type="source" position={Position.Bottom} isConnectable={false} />
      </div>
    );
  }

  // Otherwise, render the standard display node
  return (
    <div className={`p-4 rounded-lg shadow-lg cursor-pointer ring-1 ${activeTheme ? `${activeTheme.button} ${activeTheme.button_hover}` : 'bg-white ring-gray-900/10 hover:ring-blue-500'}`} style={{ width: 250 }}>
      <Handle type="target" position={Position.Top} isConnectable={false} />
      <p className="text-center text-white font-semibold">{data.label}</p>
      <Handle type="source" position={Position.Bottom} isConnectable={false} />
    </div>
  );
};

const nodeTypes = { story: StoryNode, choice: ChoiceNode };

// Suggestion Cards Component
const SuggestionCards = ({ 
  onSuggestionClick, 
  activeTheme 
}: { 
  onSuggestionClick: (suggestion: string) => void;
  activeTheme: ColorTheme | null;
}) => {
  const suggestions = [
    "Read a story about an interesting character with complex motivations.",
    "Start tracing one of the many timelines in the Mahabharata, from its origin at the beginning of the story.",
    "Explore what it means to be human with a story about a core human emotion."
  ];

  return (
    <div className="w-full max-w-2xl flex flex-row gap-3 justify-center flex-wrap mt-2">
      {suggestions.map((suggestion, index) => (
        <div
          key={index}
          onClick={() => onSuggestionClick(suggestion)}
          className={`px-3 py-2 rounded-md shadow cursor-pointer transition-colors duration-150 border text-xs max-w-xs flex-1 min-w-[180px] text-center select-none
            ${activeTheme ? `${activeTheme.input} ${activeTheme.ring} ${activeTheme.button_hover}` : 'bg-gray-800 border-gray-700 hover:bg-gray-700'}
            ${activeTheme ? 'text-white' : 'text-gray-100'}
          `}
          style={{ minHeight: 48 }}
        >
          {suggestion}
        </div>
      ))}
    </div>
  );
};

function StorytellerInterface() {
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingStory, setStreamingStory] = useState('');
  const [showStreamingModal, setShowStreamingModal] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState<CustomNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);
  const [storyLength, setStoryLength] = useState(1500);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<string>('');
  const [activeTheme, setActiveTheme] = useState<ColorTheme | null>(null);
  const [isLayouting, setIsLayouting] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  
  // Username and journey management
  const [currentUsername, setCurrentUsername] = useState<string>('');
  
  // Corpus management
  const [corpuses, setCorpuses] = useState<Corpus[]>([]);
  const [selectedCorpus, setSelectedCorpus] = useState<string>('mahabharata'); // Default to mahabharata
  
  // Load username and corpus from localStorage on mount
  useEffect(() => {
    const savedUsername = localStorage.getItem('storyteller_current_username');
    if (savedUsername) {
      setCurrentUsername(savedUsername);
    }
    
    const savedCorpus = localStorage.getItem('storyteller_current_corpus');
    if (savedCorpus) {
      setSelectedCorpus(savedCorpus);
    }
  }, []);

  // Save username and corpus to localStorage when they change
  useEffect(() => {
    if (currentUsername) {
      localStorage.setItem('storyteller_current_username', currentUsername);
    }
  }, [currentUsername]);

  useEffect(() => {
    if (selectedCorpus) {
      localStorage.setItem('storyteller_current_corpus', selectedCorpus);
    }
  }, [selectedCorpus]);

  // Fetch personas and corpuses from the backend on component mount
  useEffect(() => {
    // Fetch personas
    fetch('http://localhost:8000/api/personas')
      .then((res) => res.json())
      .then((data: Persona[]) => {
        setPersonas(data);
        if (data.length > 0) {
          // Set a default persona and theme
          setSelectedPersona(data[0].name);
          setActiveTheme(data[0].color_theme);
        }
      })
      .catch(console.error);
    
    // Fetch corpuses
    fetch('http://localhost:8000/api/corpuses')
      .then((res) => res.json())
      .then((data: Corpus[]) => {
        setCorpuses(data);
        // If no corpus is selected or the selected corpus is not available, select the first active one
        if (!selectedCorpus || !data.find(c => c.name === selectedCorpus)) {
          const firstActiveCorpus = data.find(c => c.is_active);
          if (firstActiveCorpus) {
            setSelectedCorpus(firstActiveCorpus.name);
          }
        }
      })
      .catch(console.error);
  }, []);

  // Update theme when persona changes
  useEffect(() => {
    const newPersona = personas.find(p => p.name === selectedPersona);
    if (newPersona) {
      setActiveTheme(newPersona.color_theme);
    }
  }, [selectedPersona, personas]);

  const getLayoutedElements = useCallback(
    async (nodesToLayout: Node<CustomNodeData>[], edgesToLayout: Edge[], forceUpdate = false) => {
      console.log('getLayoutedElements called with', nodesToLayout.length, 'nodes and', edgesToLayout.length, 'edges');
      if (nodesToLayout.length === 0 || isLayouting) {
        console.log('Skipping layout - no nodes or already layouting');
        return;
      }
      setIsLayouting(true);
      console.log('Starting layout process...');
      
      const nodeElements = document.querySelectorAll('.react-flow__node');
      const nodeMap = new Map(Array.from(nodeElements).map(el => [el.getAttribute('data-id'), el]));

      const graph: ElkNode = {
        id: 'root',
        layoutOptions: elkLayoutOptions,
        children: nodesToLayout.map((node) => {
          const nodeEl = nodeMap.get(node.id);
          const width = nodeEl ? nodeEl.clientWidth : (node.type === 'story' ? 400 : 250);
          const height = nodeEl ? nodeEl.clientHeight : (node.type === 'story' ? 300 : 60);
          return {
            ...node,
            width: width,
            height: height,
          };
        }),
        edges: edgesToLayout.map((edge) => ({
          id: edge.id,
          sources: [edge.source],
          targets: [edge.target],
        })),
      };

      try {
        console.log('Calling ELK layout...');
        const layoutedGraph = await elk.layout(graph);
        console.log('ELK layout completed');
        const layoutedNodes = (layoutedGraph.children || []).map((elkNode) => {
          const originalNode = nodesToLayout.find(n => n.id === elkNode.id);
          if (!originalNode) return null;
          return {
            ...originalNode,
            position: { x: elkNode.x, y: elkNode.y },
          };
        }).filter(Boolean) as Node<CustomNodeData>[];

        console.log('Setting layouted nodes:', layoutedNodes);
        setNodes(layoutedNodes);
        setEdges(edgesToLayout);
      } catch (e) {
        console.error("Layouting failed:", e);
      } finally {
        setIsLoading(false);
        setIsLayouting(false);
        console.log('Layout process completed');
      }
    },
    [setNodes, setEdges, isLayouting]
  );
  
  useEffect(() => {
    // This effect will run once after the initial nodes are rendered,
    // and whenever the `nodes` array is updated with new content.
    // A small timeout allows the DOM to update before we measure node sizes.
    console.log('Layout useEffect triggered - nodes:', nodes.length, 'edges:', edges.length);
    const timer = setTimeout(() => {
      console.log('Calling getLayoutedElements with', nodes.length, 'nodes and', edges.length, 'edges');
      getLayoutedElements(nodes, edges);
    }, 100);

    return () => clearTimeout(timer);
  }, [nodes.length, edges.length]); // Rerun only when number of nodes/edges changes

  const fetchGraph = (promptValue: string, choiceId?: string, newJourney?: boolean, randomizeRetrieval?: boolean) => {
    setIsLoading(true);
    setStreamingStory('');
    setShowStreamingModal(true);
    let url = `http://localhost:8000/api/story?prompt=${encodeURIComponent(
      promptValue
    )}&story_length=${storyLength}`;
    if (choiceId) {
      url += `&choice_id=${encodeURIComponent(choiceId)}`;
    }
    if (newJourney) {
      url += `&new_journey=true`;
    }
    if (selectedPersona) {
      url += `&persona_name=${encodeURIComponent(selectedPersona)}`;
    }
    if (randomizeRetrieval) {
      url += `&randomize_retrieval=true`;
    }
    if (currentUsername) {
      url += `&username=${encodeURIComponent(currentUsername)}`;
    }
    if (selectedCorpus) {
      url += `&corpus_name=${encodeURIComponent(selectedCorpus)}`;
    }

    const eventSource = new EventSource(url);

    eventSource.addEventListener('story_chunk', (event) => {
      setStreamingStory((prev) => prev + event.data);
    });

    eventSource.onmessage = (event) => {
      console.log('Received event data:', event.data);
      if (event.data.startsWith('{')) {
        try {
          const graphData = JSON.parse(event.data);
          console.log('Parsed graph data:', graphData);
          console.log('Number of nodes:', graphData.nodes?.length);
          console.log('Number of links:', graphData.links?.length);
          
          // Preload all images before rendering the nodes
          const imageNodes = graphData.nodes.filter((n: any) => n.image_url);
          console.log('Found image nodes:', imageNodes.length);
          imageNodes.forEach((node: any) => {
            console.log('Image URL:', node.image_url);
            if (isImageUrlExpired(node.image_url)) {
              console.warn(`Image URL appears to be expired for node ${node.id}:`, node.image_url);
            }
          });
          
          const imagePromises = imageNodes.map((node: any) => {
            return new Promise<void>((resolve) => {
              // Skip loading if URL is expired
              if (isImageUrlExpired(node.image_url)) {
                console.warn(`Skipping expired image for node ${node.id}`);
                resolve();
                return;
              }
              
              const img = new Image();
              img.src = node.image_url;
              img.onload = () => {
                console.log(`Successfully loaded image: ${node.image_url}`);
                resolve();
              };
              img.onerror = () => {
                console.error(`Failed to load image: ${node.image_url}`);
                console.error('Image error details:', {
                  nodeId: node.id,
                  nodeLabel: node.label,
                  imageUrl: node.image_url,
                  isExpired: isImageUrlExpired(node.image_url)
                });
                resolve(); // Resolve even on error to not block rendering
              };
            });
          });

          Promise.all(imagePromises).then(() => {
            const newNodes = graphData.nodes.map((node: any) => ({
              id: node.id,
              type: node.type || 'choice', // default to choice
              data: {
                label: node.label || 'Untitled',
                story: node.story || '',
                isChoice: node.isChoice || false,
                image_url: node.image_url && !isImageUrlExpired(node.image_url) ? node.image_url : null,
              },
              position: { x: 0, y: 0 }, // Elk will set this
            }));

            const newEdges = graphData.links.map((edge: any) => ({
              id: `e-${edge.source}-${edge.target}`,
              source: edge.source,
              target: edge.target,
            }));
            
            console.log('Setting new nodes:', newNodes);
            console.log('Setting new edges:', newEdges);
            
            // This state update triggers the layouting useEffect
            setNodes(newNodes);
            setEdges(newEdges);
          });

        } catch (error) {
          console.error("Failed to parse event data:", error);
        }
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      eventSource.close();
      setIsLoading(false);
      setShowStreamingModal(false);
    };

    eventSource.addEventListener('end', () => {
      console.log('Stream ended.');
      eventSource.close();
      // Layout might still be running, isLoading is set to false in getLayoutedElements
    });
  };

  const handleNodeClick: NodeMouseHandler = (_event, node) => {
    if (isLoading || !node.data.isChoice) return;
    setEditingNodeId(node.id);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt || isLoading) return;
    setShowSuggestions(false);
    fetchGraph(prompt, undefined, true);
  };
  
  const handleLabelChange = (nodeId: string, newLabel: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          // it's important to create a new object here to trigger a re-render
          return { ...node, data: { ...node.data, label: newLabel } };
        }
        return node;
      })
    );
  };

  const handleEditSubmit = (nodeId: string, prompt: string) => {
    if (!prompt) return;
    setShowSuggestions(false);
    fetchGraph(prompt, nodeId);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setShowSuggestions(false);
    fetchGraph(suggestion, undefined, true, true); // Pass randomizeRetrieval=true
  };

  // Username and journey handlers
  const handleUsernameChange = (username: string) => {
    setCurrentUsername(username);
    // Clear current story when switching users
    setNodes([]);
    setEdges([]);
    setShowSuggestions(true);
  };

  const handleCorpusChange = (corpusName: string) => {
    setSelectedCorpus(corpusName);
    // Clear current story when switching corpuses (as corpus is a property of the graph)
    setNodes([]);
    setEdges([]);
    setShowSuggestions(true);
  };

  // Helper function to check if an image URL is likely expired
  const isImageUrlExpired = (url: string): boolean => {
    if (!url) return true;
    
    // Check if it's an Azure Blob Storage URL with SAS token
    if (url.includes('blob.core.windows.net') && url.includes('se=')) {
      try {
        // Extract expiry time from URL
        const expiryMatch = url.match(/se=([^&]+)/);
        if (expiryMatch) {
          const expiryTime = decodeURIComponent(expiryMatch[1]);
          const expiryDate = new Date(expiryTime);
          const now = new Date();
          return expiryDate < now;
        }
      } catch (error) {
        console.error('Error parsing image URL expiry:', error);
      }
    }
    return false;
  };

  const handleJourneySelect = async (graphId: string) => {
    if (!currentUsername) return;
    
    setIsLoading(true);
    try {
      // First, load the graph on the backend
      const loadResponse = await fetch('http://localhost:8000/api/load_graph', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: currentUsername,
          graph_id: graphId,
        }),
      });

      if (loadResponse.ok) {
        const loadData = await loadResponse.json();
        const graphMeta = loadData.meta;
        
        // Update corpus if the loaded graph has corpus information
        if (graphMeta && graphMeta.corpus_name) {
          setSelectedCorpus(graphMeta.corpus_name);
        }
        
        // Now fetch the loaded graph data directly
        const graphResponse = await fetch('http://localhost:8000/api/get_loaded_graph', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (graphResponse.ok) {
          const data = await graphResponse.json();
          const graphData = data.graph;
          
          console.log('Loaded graph data:', graphData);
          console.log('Number of nodes:', graphData.nodes?.length);
          console.log('Number of links:', graphData.links?.length);
          
          // Debug: Log each node's structure
          if (graphData.nodes) {
            console.log('=== NODE STRUCTURE ANALYSIS ===');
            graphData.nodes.forEach((node: any, index: number) => {
              console.log(`Node ${index}:`, {
                id: node.id,
                type: node.type,
                label: node.label,
                story: node.story ? `${node.story.substring(0, 50)}...` : 'NO STORY',
                isChoice: node.isChoice,
                image_url: node.image_url ? 'HAS IMAGE' : 'NO IMAGE',
                allProps: Object.keys(node)
              });
            });
            console.log('=== END NODE ANALYSIS ===');
          }
          
          // Debug: Log each link's structure
          if (graphData.links) {
            console.log('=== LINK STRUCTURE ANALYSIS ===');
            graphData.links.forEach((link: any, index: number) => {
              console.log(`Link ${index}:`, {
                source: link.source,
                target: link.target,
                allProps: Object.keys(link)
              });
            });
            console.log('=== END LINK ANALYSIS ===');
          }

          // Preload all images before rendering the nodes
          const imageNodes = graphData.nodes.filter((n: any) => n.image_url);
          console.log('Found image nodes:', imageNodes.length);
          imageNodes.forEach((node: any) => {
            console.log('Image URL:', node.image_url);
            if (isImageUrlExpired(node.image_url)) {
              console.warn(`Image URL appears to be expired for node ${node.id}:`, node.image_url);
            }
          });
          
          const imagePromises = imageNodes.map((node: any) => {
            return new Promise<void>((resolve) => {
              // Skip loading if URL is expired
              if (isImageUrlExpired(node.image_url)) {
                console.warn(`Skipping expired image for node ${node.id}`);
                resolve();
                return;
              }
              
              const img = new Image();
              img.src = node.image_url;
              img.onload = () => {
                console.log(`Successfully loaded image: ${node.image_url}`);
                resolve();
              };
              img.onerror = () => {
                console.error(`Failed to load image: ${node.image_url}`);
                console.error('Image error details:', {
                  nodeId: node.id,
                  nodeLabel: node.label,
                  imageUrl: node.image_url,
                  isExpired: isImageUrlExpired(node.image_url)
                });
                resolve(); // Resolve even on error to not block rendering
              };
            });
          });

          Promise.all(imagePromises).then(() => {
            const newNodes = graphData.nodes.map((node: any) => ({
              id: node.id,
              type: node.type || 'choice', // default to choice
              data: {
                label: node.label || 'Untitled',
                story: node.story || '',
                isChoice: node.isChoice || false,
                image_url: node.image_url && !isImageUrlExpired(node.image_url) ? node.image_url : null,
              },
              position: { x: 0, y: 0 }, // Elk will set this
            }));

            const newEdges = graphData.links.map((edge: any) => ({
              id: `e-${edge.source}-${edge.target}`,
              source: edge.source,
              target: edge.target,
            }));
            
            console.log('Processed nodes:', newNodes);
            console.log('Processed edges:', newEdges);
            
            // This state update triggers the layouting useEffect
            setNodes(newNodes);
            setEdges(newEdges);
          });
        } else {
          console.error('Failed to get loaded graph data');
        }
      } else {
        console.error('Failed to load journey');
      }
    } catch (error) {
      console.error('Error loading journey:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Hide suggestions when there are nodes (story has started)
  useEffect(() => {
    if (nodes.length > 0) {
      setShowSuggestions(false);
    }
  }, [nodes.length]);

  return (
    <EditingContext.Provider value={{ editingNodeId, setEditingNodeId, handleLabelChange, handleEditSubmit, activeTheme }}>
      <div className={`w-full h-screen text-stone-200 flex flex-col relative bg-stone-900`}>
        {/* Top-right dropdowns */}
        <div className="absolute top-4 right-4 z-30 flex gap-2">
          <UsernameDropdown
            currentUsername={currentUsername}
            onUsernameChange={handleUsernameChange}
            disabled={isLoading}
            theme={activeTheme}
          />
          <CorpusDropdown
            corpuses={corpuses}
            selectedCorpus={selectedCorpus}
            onCorpusChange={handleCorpusChange}
            disabled={isLoading}
            theme={activeTheme}
          />
          <JourneyDropdown
            username={currentUsername}
            onJourneySelect={handleJourneySelect}
            disabled={isLoading}
            theme={activeTheme}
          />
        </div>

        {/* Main content */}
        <div className="flex flex-col items-center p-4 pt-16">
          <div className="w-full max-w-2xl z-10 space-y-4">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Tell me a story about..."
                className={`flex-grow border border-gray-700 rounded-md p-2 focus:outline-none focus:ring-2 ${activeTheme ? `${activeTheme.input} ${activeTheme.ring}` : 'bg-gray-800 focus:ring-blue-500'}`}
                disabled={isLoading}
              />
              <button
                type="submit"
                className={`rounded-md px-4 py-2 font-semibold disabled:opacity-50 ${activeTheme ? `${activeTheme.button} ${activeTheme.button_hover}` : 'bg-blue-600 hover:bg-blue-700'}`}
                disabled={isLoading || !prompt}
              >
                {isLoading ? 'Weaving...' : 'Start New Journey'}
              </button>
            </form>
            
            {showSuggestions && (
              <SuggestionCards 
                onSuggestionClick={handleSuggestionClick}
                activeTheme={activeTheme}
              />
            )}
            
            <div className="flex items-center justify-end gap-4 text-sm">
              <div className="flex items-center gap-2">
                <label htmlFor="story-length">Quick read</label>
                <input
                  id="story-length"
                  type="range"
                  min="500"
                  max="3000"
                  step="100"
                  value={storyLength}
                  onChange={(e) => setStoryLength(parseInt(e.target.value, 10))}
                  className="w-48"
                  disabled={isLoading}
                />
                <span>Richer detail</span>
              </div>
              <div className="flex items-center gap-2">
                <label htmlFor="persona-select">Persona:</label>
                <PersonaDropdown
                  personas={personas}
                  selectedPersona={selectedPersona}
                  onPersonaChange={setSelectedPersona}
                  disabled={isLoading}
                  theme={activeTheme}
                />
              </div>
            </div>
          </div>

          <div className="w-full min-h-[300px] h-[60vh] max-h-[90vh] mt-4 rounded-lg overflow-hidden">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={handleNodeClick}
              nodeTypes={nodeTypes}
              fitView
            >
              <Controls />
            </ReactFlow>
          </div>
        </div>

        {showStreamingModal && (
          <div
            className="fixed inset-0 bg-black/60 z-20 flex justify-center items-center"
            onClick={() => setShowStreamingModal(false)}
          >
            <div
              className={`p-6 rounded-lg shadow-xl max-w-2xl w-full ${activeTheme?.input || 'bg-gray-800'}`}
              onClick={(e) => e.stopPropagation()} // Prevents closing when clicking inside the modal
            >
              <h3 className="text-lg font-bold mb-2 text-gray-100">
                {isLoading ? 'Generating your story...' : 'Story Complete'}
              </h3>
              <div className={`max-h-96 overflow-y-auto p-4 rounded bg-black/20`}>
                <p className="text-sm text-gray-300 whitespace-pre-wrap">
                  {streamingStory}
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* --- Persistent loading indicator --- */}
        {isLoading && (
          <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-20">
            <p className="text-lg text-gray-400 animate-pulse">
              Weaving your next story...
            </p>
          </div>
        )}
      </div>
    </EditingContext.Provider>
  );
}

export default function Home() {
  return <StorytellerInterface />;
}
