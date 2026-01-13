import { useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import AuthContext from '../context/AuthContext';

const ClientDashboard = () => {
    // Extragem funcția logout și userul din context
    const { user, logout } = useContext(AuthContext);

    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const navigate = useNavigate();

    // Încărcăm dispozitivele la pornirea paginii
    useEffect(() => {
        const fetchDevices = async () => {
            try {
                // Backend-ul returnează automat doar dispozitivele userului logat
                // bazat pe ID-ul din token
                const response = await api.get('/devices/');
                setDevices(response.data);
            } catch (err) {
                console.error(err);
                setError('Could not load devices.');
            } finally {
                setLoading(false);
            }
        };

        fetchDevices();
    }, []);

    if (loading) return <div style={{ padding: '20px' }}>Loading your devices...</div>;
    if (error) return <div style={{ padding: '20px', color: 'red' }}>{error}</div>;

    return (
        <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>

            {/* Header cu Titlu și Buton de Logout */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1>My Devices</h1>
                <button
                    onClick={logout}
                    style={{
                        background: '#333',
                        color: 'white',
                        padding: '10px 20px',
                        border: 'none',
                        cursor: 'pointer',
                        borderRadius: '4px',
                        fontWeight: 'bold'
                    }}
                >
                    Logout
                </button>
            </div>

            {/* Mesaj de bun venit opțional */}
            <p>Welcome back, <strong>{user?.sub}</strong>!</p>

            {devices.length === 0 ? (
                <p style={{ marginTop: '20px', fontStyle: 'italic' }}>No devices assigned to your account yet.</p>
            ) : (
                <table border="1" cellPadding="10" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
                    <thead>
                        <tr style={{  textAlign: 'left' }}>
                            <th>Description</th>
                            <th>Address</th>
                            <th>Max Consumption (kWh)</th>
                            <th>Actions</th> {/* Coloană nouă pentru grafic */}
                        </tr>
                    </thead>
                    <tbody>
                        {devices.map(device => (
                            <tr key={device.id}>
                                <td>{device.description}</td>
                                <td>{device.address}</td>
                                <td>{device.max_hourly_consumption}</td>
                                <td>
                                    {/* Butonul care duce la pagina cu Grafic */}
                                    <button
                                        onClick={() => navigate(`/device/${device.id}`)}
                                        style={{
                                            background: '#007BFF',
                                            color: 'white',
                                            border: 'none',
                                            padding: '8px 12px',
                                            cursor: 'pointer',
                                            borderRadius: '4px'
                                        }}
                                    >
                                        View History
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

export default ClientDashboard;