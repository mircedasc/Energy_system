import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const ChatComponent = ({ userId, isAdmin }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState("");
    const [targetId, setTargetId] = useState("");
    const ws = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        if (!userId) return;

        const socketUrl = `ws://localhost/ws/connect/${userId}`;
        ws.current = new WebSocket(socketUrl);

        ws.current.onopen = () => console.log("Chat WebSocket Connected ✅");

        ws.current.onmessage = (event) => {
            try {
                // 1. Încercăm să parsăm mesajul primit (din JSON string în Obiect)
                const data = JSON.parse(event.data);

                // 2. Verificăm dacă este un mesaj destinat Chat-ului
                // Ignorăm alertele de senzori care nu au type='chat'
                if (data.type !== 'chat') {
                    return;
                }

                // 3. Extragem textul curat din câmpul 'message'
                // Backend-ul trimite: "[Role]: Mesaj"
                const cleanText = data.message;

                setMessages(prev => [...prev, { sender: 'server', text: cleanText }]);

            } catch (e) {
                // Fallback: Dacă mesajul nu e JSON (caz rar), îl afișăm direct
                // Doar dacă nu conține acolade (ca să nu afișăm JSON-uri stricate)
                if (typeof event.data === 'string' && !event.data.includes('{')) {
                     setMessages(prev => [...prev, { sender: 'server', text: event.data }]);
                }
            }
        };

        ws.current.onclose = () => console.log("Chat WebSocket Disconnected ❌");

        return () => { if (ws.current) ws.current.close(); };
    }, [userId]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async () => {
        if (!inputText.trim()) return;

        setMessages(prev => [...prev, { sender: 'me', text: inputText }]);
        const msgToSend = inputText;
        setInputText("");

        try {
            await axios.post("http://localhost/chat/send", {
                sender_id: isAdmin && targetId ? parseInt(targetId) : userId,
                message: msgToSend,
                is_admin: isAdmin
            });
        } catch (error) {
            console.error("Eroare trimitere:", error);
            setMessages(prev => [...prev, { sender: 'error', text: "Eroare..." }]);
        }
    };

    // --- STILURI ---
    const styles = {
        widget: { position: 'fixed', bottom: '20px', right: '20px', zIndex: 1000 },
        button: { backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '50%', width: '60px', height: '60px', cursor: 'pointer', fontSize: '24px', boxShadow: '0 4px 8px rgba(0,0,0,0.2)' },
        window: { position: 'fixed', bottom: '90px', right: '20px', width: '300px', height: '400px', backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '10px', display: 'flex', flexDirection: 'column', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', zIndex: 1000, overflow: 'hidden' },
        header: { backgroundColor: '#007bff', color: 'white', padding: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
        body: { flex: 1, padding: '10px', overflowY: 'auto', backgroundColor: '#f9f9f9', display: 'flex', flexDirection: 'column', gap: '10px' },
        footer: { padding: '10px', borderTop: '1px solid #eee', display: 'flex', gap: '5px' },
        messageBubble: (sender) => ({ padding: '8px 12px', borderRadius: '15px', maxWidth: '80%', alignSelf: sender === 'me' ? 'flex-end' : 'flex-start', backgroundColor: sender === 'me' ? '#007bff' : '#e9ecef', color: sender === 'me' ? 'white' : 'black', fontSize: '14px' })
    };

    return (
        <>
            {isOpen && (
                <div style={styles.window}>
                    <div style={styles.header}>
                        <span>💬 Support {isAdmin ? "(Admin)" : ""}</span>
                        <button onClick={() => setIsOpen(false)} style={{background:'none', border:'none', color:'white', cursor:'pointer'}}>✖</button>
                    </div>
                    <div style={styles.body}>
                        {messages.map((msg, index) => (
                            <div key={index} style={styles.messageBubble(msg.sender)}>{msg.text}</div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                    <div style={styles.footer}>
                        {isAdmin && <input type="number" placeholder="ID" value={targetId} onChange={e => setTargetId(e.target.value)} style={{width:'50px'}} />}
                        <input type="text" value={inputText} onChange={e => setInputText(e.target.value)} onKeyPress={e => e.key === 'Enter' && handleSend()} placeholder="..." style={{flex: 1}} />
                        <button onClick={handleSend}>➤</button>
                    </div>
                </div>
            )}
            <div style={styles.widget}><button style={styles.button} onClick={() => setIsOpen(!isOpen)}>💬</button></div>
        </>
    );
};

export default ChatComponent;