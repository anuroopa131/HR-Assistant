import React, { useState, useEffect, useRef } from 'react';
import { Player } from '@lottiefiles/react-lottie-player';
import Send from '@mui/icons-material/Send';
import Close from '@mui/icons-material/Close';
import Message from './Message';
import TypingIndicator from './TypingIndicator';
import animationData from '../../animations/chatbot-waving.json';
import './Chatbot.css';

const ChatInterface = ({ onClose, hideWidget }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [companyName, setCompanyName] = useState('');
  const [clientName, setClientName] = useState('');

  const messagesEndRef = useRef(null);

  useEffect(() => {
    hideWidget();

    
  const injectedCompany = window.COMPANY_NAME || '';
  const injectedClient = window.CLIENT_NAME || '';
  console.log("Injected company:", injectedCompany);
  console.log("Injected client (window):", injectedClient);

  setCompanyName(injectedCompany);

  if (injectedClient) {
    setClientName(injectedClient);
    localStorage.setItem("clientName", injectedClient);
  } else if (injectedCompany) {
   fetch(`http://localhost:8000/clients/api/clients/${injectedCompany}/`)
      .then(res => res.json())
      .then(data => {
        if (data.clients && data.clients.length > 0) {
          const firstClient = data.clients[0];
          console.log("Fetched client:", firstClient);
          setClientName(firstClient);
          localStorage.setItem("clientName", firstClient);
        } else {
          console.warn("No clients found.");
        }
      })
      .catch(err => {
        console.error("Error fetching client:", err);
      });
  }
}, [hideWidget]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = () => {
    if (inputValue.trim() === '') return;

    if (!companyName || !clientName) {
      alert("Client or Company not identified. Please contact support.");
      return;
    }

    const userMessage = {
      text: inputValue,
      isBot: false,
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    fetch('http://127.0.0.1:8000/query_with_retrieval/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        question: userMessage.text,
        company_name: companyName,
        client_name: clientName,
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error('Network error');
        return response.json();
      })
      .then(data => {
        setMessages(prev => [
          ...prev,
          {
            text: data.answer || "Sorry, I couldn't find an answer.",
            isBot: true,
          },
        ]);
      })
      .catch(() => {
        setMessages(prev => [
          ...prev,
          {
            text: "Oops! Something went wrong. Please try again later.",
            isBot: true,
          },
        ]);
      })
      .finally(() => {
        setIsTyping(false);
      });
  };

  const handleGetStarted = () => {
    setShowWelcome(false);
    setIsTyping(true);

    setTimeout(() => {
      setMessages([{
        text: "Hello! I'm your HR assistant. You can ask me anything related to company policies, benefits, recruitment, onboarding, employee support, or general HR information. How can I assist you today?",

        isBot: true,
      }]);
      setIsTyping(false);
    }, 1000);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="chat-interface-overlay">
      <div className="chat-interface">
        {/* Header */}
        <div className="chat-header">
          <h2 className="chat-title">Company Assistant</h2>
          <button onClick={onClose} className="close-button">
            <Close />
          </button>
        </div>

        {/* Chat Area */}
        <div className="chat-messages scrollable-chat">
          {showWelcome ? (
            <div className="welcome-screen">
              <Player
                autoplay
                loop
                src={animationData}
                style={{ width: '200px', height: '200px' }}
              />
              <h3 className="welcome-title">Hello! I'm your HR Assistant</h3>
<p className="welcome-text">
  I’m here to help with questions about HR policies, benefits, recruitment, onboarding, or any employee-related information.
</p>

              <button
                onClick={handleGetStarted}
                className="get-started-button"
              >
                Get Started
              </button>
            </div>
          ) : (
            <>
              {messages.map((message, index) => (
                <Message key={index} message={message.text} isBot={message.isBot} />
              ))}
              {isTyping && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        {!showWelcome && (
          <div className="chat-input-container">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask something about our company..."
              className="chat-input"
            />
            <button
              onClick={handleSendMessage}
              disabled={inputValue.trim() === ''}
              className={`send-button ${inputValue.trim() === '' ? 'disabled' : ''}`}
            >
              <Send />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
