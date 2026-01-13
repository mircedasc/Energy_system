import { useState, useContext } from 'react';
import api from '../api/axios';
import AuthContext from '../context/AuthContext';
import { toast } from 'react-toastify';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    // Stare pentru a comuta între Login și Register
    const [isRegistering, setIsRegistering] = useState(false);

    const { login } = useContext(AuthContext);

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            if (isRegistering) {
                // --- LOGICA DE REGISTER ---
                // Register așteaptă JSON
                await api.post('/auth/register', {
                    username: username,
                    password: password,
                    role: 'Client' // Public register este mereu Client
                });

                toast.success("Account created! Please log in.");
                setIsRegistering(false); // Trecem înapoi la ecranul de Login
            } else {
                // --- LOGICA DE LOGIN ---
                // Login așteaptă x-www-form-urlencoded
                const response = await api.post('/auth/login',
                    new URLSearchParams({
                        username: username,
                        password: password
                    }),
                    {
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                    }
                );

                login(response.data.access_token);
                toast.success("Login successful!");
            }

        } catch (err) {
            console.error(err);
            // Extragem mesajul de eroare din backend dacă există
            const errorMessage = err.response?.data?.detail || "Operation failed!";
            toast.error(errorMessage);
        }
    };

    return (
        <div style={{
            maxWidth: '400px',
            margin: '50px auto',
            padding: '30px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            fontFamily: 'Arial, sans-serif'
        }}>
            <h2 style={{ textAlign: 'center' }}>
                {isRegistering ? 'Create Account' : 'Login'}
            </h2>

            <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', color: '#666' }}>Username:</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                        required
                    />
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', color: '#666' }}>Password:</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                        required
                    />
                </div>

                <button
                    type="submit"
                    style={{
                        width: '100%',
                        padding: '12px',
                        background: isRegistering ? '#28a745' : '#007BFF', // Verde pt Register, Albastru pt Login
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }}
                >
                    {isRegistering ? 'Sign Up' : 'Sign In'}
                </button>
            </form>

            <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '14px' }}>
                {isRegistering ? (
                    <p>
                        Already have an account?{' '}
                        <span
                            onClick={() => setIsRegistering(false)}
                            style={{ color: '#007BFF', cursor: 'pointer', textDecoration: 'underline' }}
                        >
                            Login here
                        </span>
                    </p>
                ) : (
                    <p>
                        Don't have an account?{' '}
                        <span
                            onClick={() => setIsRegistering(true)}
                            style={{ color: '#007BFF', cursor: 'pointer', textDecoration: 'underline' }}
                        >
                            Register here
                        </span>
                    </p>
                )}
            </div>
        </div>
    );
};

export default Login;