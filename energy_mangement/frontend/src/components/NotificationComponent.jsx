import React, { useEffect, useState } from 'react';
// 1. Sintaxa CORECTĂ (fără "from" în interiorul acoladelor)
import { useAuth } from '../context/AuthContext';

const NotificationComponent = () => {
    const [notifications, setNotifications] = useState([]);

    // 2. Folosim hook-ul creat anterior
    const { user } = useAuth();
    const userId = user?.id;

    useEffect(() => {
        // Dacă nu avem user logat, nu ne conectăm
        if (!userId) return;

        console.log("Connecting WebSocket for User:", userId);
        const ws = new WebSocket(`ws://localhost/ws/connect/${userId}`);

        ws.onopen = () => {
            console.log('Connected to Notification Service');
        };

        ws.onmessage = (event) => {
            console.log("Alert received:", event.data);
            const message = event.data;
            const id = Date.now();

            setNotifications((prev) => [...prev, { id, text: message }]);

            // Ștergem notificarea după 5 secunde
            setTimeout(() => {
                setNotifications((prev) => prev.filter(n => n.id !== id));
            }, 5000);
        };

        ws.onclose = () => {
            console.log('Disconnected from Notification Service');
        };

        return () => {
            ws.close();
        };
    }, [userId]);

    // Dacă nu sunt notificări, nu afișăm nimic
    if (notifications.length === 0) return null;

    // Stiluri inline pentru simplitate
    const containerStyle = {
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
    };

    const alertStyle = {
        backgroundColor: '#ff4444',
        color: 'white',
        padding: '16px',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        fontSize: '14px',
        fontWeight: 'bold',
        minWidth: '300px',
        animation: 'fadeIn 0.5s'
    };

    return (
        <div style={containerStyle}>
            {notifications.map((n) => (
                <div key={n.id} style={alertStyle}>
                    ⚠️ {n.text}
                </div>
            ))}
        </div>
    );
};

export default NotificationComponent;