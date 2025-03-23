import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sun, Moon, Pencil, Check, X, Paperclip, Mic, MicOff, Menu, X as Close } from 'lucide-react';
import { format } from 'date-fns';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  attachments?: File[];
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [chatTitle, setChatTitle] = useState('New Conversation');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [tempTitle, setTempTitle] = useState(chatTitle);
  const [isRecording, setIsRecording] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.style.height = 'auto';
      textAreaRef.current.style.height = `${textAreaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleTitleEdit = () => {
    if (isEditingTitle) {
      if (tempTitle.trim()) {
        setChatTitle(tempTitle);
      }
      setIsEditingTitle(false);
    } else {
      setTempTitle(chatTitle);
      setIsEditingTitle(true);
    }
  };

  const cancelTitleEdit = () => {
    setTempTitle(chatTitle);
    setIsEditingTitle(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && selectedFiles.length === 0) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date(),
      attachments: selectedFiles
    };

    setMessages(prev => [...prev, newMessage]);
    setInput('');
    setSelectedFiles([]);
    setIsLoading(true);
    setIsSidebarOpen(false);

    // Simulate API call
    setTimeout(() => {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        content: 'This is a simulated response from the AI model. In a real implementation, this would be replaced with actual API calls to your LLM backend.',
        role: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, response]);
      setIsLoading(false);
    }, 1000);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'voice-message.wav', { type: 'audio/wav' });
        setSelectedFiles(prev => [...prev, audioFile]);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Unable to access microphone. Please check your permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const UserAvatar = ({ initials }: { initials: string }) => (
    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
      {initials}
    </div>
  );

  const SystemAvatar = () => (
    <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white font-semibold">
      LX
    </div>
  );

  return (
    <div className={`min-h-screen flex ${isDarkMode ? 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-800 via-gray-900 to-black text-white' : 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50 via-gray-50 to-gray-100 text-gray-900'}`}>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-opacity-80 backdrop-blur-sm"
      >
        {isSidebarOpen ? <Close className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Sidebar */}
      <div
        className={`${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 fixed lg:relative w-64 h-full transition-transform duration-300 ease-in-out z-40 ${
          isDarkMode ? 'bg-gray-800/95 backdrop-blur-sm' : 'bg-white/95 backdrop-blur-sm border-r border-gray-200'
        } p-4 flex flex-col`}
      >
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-2">
            <img src="/medicia-logo.png" alt="Medicia Logo" className="w-8 h-8" />
            <h1 className="text-xl font-bold">Medicia - Lab Result Analysis</h1>
          </div>
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className={`p-2 rounded-lg ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
          >
            {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>

        <div className="flex-1">
          <div className="mb-4">
            {isEditingTitle ? (
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={tempTitle}
                  onChange={(e) => setTempTitle(e.target.value)}
                  className={`flex-1 p-2 rounded ${
                    isDarkMode ? 'bg-gray-700' : 'bg-gray-100'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  autoFocus
                />
                <button
                  onClick={() => handleTitleEdit()}
                  className="text-green-500 hover:text-green-400"
                >
                  <Check className="w-4 h-4" />
                </button>
                <button
                  onClick={cancelTitleEdit}
                  className="text-red-500 hover:text-red-400"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <h2 className={`text-lg font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                  {chatTitle}
                </h2>
                <button
                  onClick={() => handleTitleEdit()}
                  className={`${isDarkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-600 hover:text-gray-500'}`}
                >
                  <Pencil className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            {messages.length > 0
              ? `${messages.length} messages in this conversation`
              : 'Start a new conversation'}
          </p>
        </div>
      </div>

      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col w-full lg:w-auto">
        <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start space-x-2 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && <SystemAvatar />}
              <div
                className={`max-w-[85%] md:max-w-2xl p-4 rounded-lg ${
                  message.role === 'user'
                    ? isDarkMode
                      ? 'bg-blue-600/90 backdrop-blur-sm text-white'
                      : 'bg-blue-500/90 backdrop-blur-sm text-white'
                    : isDarkMode
                    ? 'bg-gray-700/90 backdrop-blur-sm text-gray-100'
                    : 'bg-white/90 backdrop-blur-sm text-gray-900'
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
                {message.attachments?.map((file, index) => (
                  <div key={index} className="mt-2 text-sm">
                    📎 {file.name}
                  </div>
                ))}
                <span className="text-xs opacity-75 mt-2 block">
                  {format(message.timestamp, 'PPpp')}
                </span>
              </div>
              {message.role === 'user' && <UserAvatar initials="KM" />}
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start items-start space-x-2">
              <SystemAvatar />
              <div className={`p-4 rounded-lg flex items-center space-x-2 ${
                isDarkMode ? 'bg-gray-700/90 backdrop-blur-sm' : 'bg-white/90 backdrop-blur-sm'
              }`}>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>AI is thinking...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} className={`p-4 border-t ${
          isDarkMode ? 'border-gray-700/50 bg-gray-800/95 backdrop-blur-sm' : 'border-gray-200/50 bg-white/95 backdrop-blur-sm'
        }`}>
          <div className="flex flex-col space-y-2 max-w-5xl mx-auto">
            {selectedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className={`text-sm px-2 py-1 rounded ${
                      isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
                    }`}
                  >
                    📎 {file.name}
                    <button
                      type="button"
                      onClick={() => setSelectedFiles(files => files.filter((_, i) => i !== index))}
                      className="ml-2 text-red-500 hover:text-red-600"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="flex items-end space-x-2">
              <div className="flex-1 flex items-end space-x-2">
                <textarea
                  ref={textAreaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message... (Ctrl+Enter to send)"
                  className={`flex-1 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none min-h-[44px] ${
                    isDarkMode
                      ? 'bg-gray-700/90 backdrop-blur-sm text-white'
                      : 'bg-gray-100/90 backdrop-blur-sm text-gray-900'
                  }`}
                  rows={1}
                />
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  className="hidden"
                  multiple
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className={`p-2 rounded-lg ${
                    isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'
                  }`}
                  title="Attach files"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`p-2 rounded-lg ${
                    isRecording
                      ? 'bg-red-500 hover:bg-red-600'
                      : isDarkMode
                      ? 'hover:bg-gray-700'
                      : 'hover:bg-gray-200'
                  }`}
                  title={isRecording ? 'Stop recording' : 'Start recording'}
                >
                  {isRecording ? (
                    <MicOff className="w-5 h-5" />
                  ) : (
                    <Mic className="w-5 h-5" />
                  )}
                </button>
              </div>
              <button
                type="submit"
                disabled={isLoading || (!input.trim() && selectedFiles.length === 0)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Send message (Ctrl+Enter)"
              >
                <span className="hidden sm:inline">Send</span>
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;