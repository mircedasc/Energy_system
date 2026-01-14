import React, { useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { useAuth } from '../context/AuthContext'; // Importăm Auth Context

const NotificationComponent = () => {
    // Luăm user-ul direct din Context, nu mai așteptăm props
    const { user } = useAuth();
    const userId = user?.id; // Extragem ID-ul sigur

    useEffect(() => {
        // Dacă nu suntem logați, nu facem nimic
        if (!userId) return;

        console.log(` [Notif] Connecting for User ${userId}...`);
        const socketUrl = `ws://localhost/ws/connect/${userId}`;
        const ws = new WebSocket(socketUrl);

        ws.onopen = () => console.log(" [Notif] WebSocket Connected ✅");

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // 1. IGNORĂM CHAT-UL (acesta e treaba ChatComponent)
                if (data.type === 'chat') {
                    return;
                }

                // 2. AFIȘĂM ALERTA
                // Extragem doar textul din câmpul "message"
                if (data.message) {
                    toast.error(`⚠️ ${data.message}`, {
                        position: "top-right",
                        autoClose: 5000,
                        hideProgressBar: false,
                        closeOnClick: true,
                        pauseOnHover: true,
                        draggable: true,
                    });
                }
            } catch (error) {
                // Ignorăm erorile de parsare
            }
        };

        ws.onclose = () => console.log(" [Notif] WebSocket Disconnected ❌");

        return () => {
            if (ws.readyState === 1) ws.close();
        };
    }, [userId]); // Se reactivează automat când te loghezi (se schimbă userId)

    // Randăm containerul de toast aici, ca să fie disponibil în toată aplicația
    return (
        <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
        />
    );
};

export default NotificationComponent;