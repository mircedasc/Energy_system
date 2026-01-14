import { useEffect, useState, useContext } from 'react';
import api from '../api/axios';
import { toast } from 'react-toastify';
import AuthContext from '../context/AuthContext';
import ChatComponent from '../components/ChatComponent';
import { useAuth } from '../context/AuthContext'; // Asigură-te că ai acces la user

const AdminDashboard = () => {
    const { user, logout } = useAuth();
    const [users, setUsers] = useState([]);
    const [devices, setDevices] = useState([]);
    const [activeTab, setActiveTab] = useState('users');

    // Formulare
    const [userForm, setUserForm] = useState({ id: null, username: '', password: '', role: 'Client' });
    const [deviceForm, setDeviceForm] = useState({ id: null, description: '', address: '', max_hourly_consumption: 0, owner_id: '' });

    // Mod editare
    const [isEditing, setIsEditing] = useState(false);

    const fetchData = async () => {
        try {
            const [usersRes, devicesRes] = await Promise.all([
                api.get('/users/'),
                api.get('/devices/')
            ]);
            setUsers(usersRes.data);
            setDevices(devicesRes.data);
        } catch (error) {
            console.error(error);
        }
    };

    useEffect(() => { fetchData(); }, []);

    // --- USER HANDLERS ---
    const handleEditUserClick = (user) => {
        setUserForm({ ...user, password: '' }); // Parola o lăsăm goală la edit
        setIsEditing(true);
    };

    const handleUserSubmit = async (e) => {
        e.preventDefault();
        try {
            if (isEditing) {
                // UPDATE (Put)
                // Backend-ul User Service are endpoint PUT /users/{id}
                const payload = {
                    username: userForm.username,
                    role: userForm.role
                };
                if (userForm.password) payload.password = userForm.password;

                await api.put(`/users/${userForm.id}`, payload);
                toast.success("User updated!");
            } else {
                // CREATE (Post via Auth)
                await api.post('/auth/register', userForm);
                toast.success("User created!");
            }
            setUserForm({ id: null, username: '', password: '', role: 'Client' });
            setIsEditing(false);
            fetchData();
        } catch (error) {
            toast.error("Operation failed: " + (error.response?.data?.detail || error.message));
        }
    };

    // --- DEVICE HANDLERS ---
    const handleEditDeviceClick = (device) => {
        setDeviceForm(device);
        setIsEditing(true);
    };

    const handleDeviceSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = { ...deviceForm, owner_id: deviceForm.owner_id || null };
            if (isEditing) {
                // UPDATE
                await api.put(`/devices/${deviceForm.id}`, payload);
                toast.success("Device updated!");
            } else {
                // CREATE
                await api.post('/devices/', payload);
                toast.success("Device created!");
            }
            setDeviceForm({ id: null, description: '', address: '', max_hourly_consumption: 0, owner_id: '' });
            setIsEditing(false);
            fetchData();
        } catch (error) {
            toast.error("Operation failed.");
        }
    };

    // Helper pt Delete (rămâne la fel)
    const deleteItem = async (type, id) => {
        if(!window.confirm("Delete?")) return;
        try {
            await api.delete(`/${type}/${id}`);
            toast.success("Deleted!");
            fetchData();
        } catch(e) { toast.error("Failed."); }
    }

    return (
        <div style={{ padding: '20px', fontFamily: 'Arial' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <h1>Admin Dashboard</h1>
                <button onClick={logout} style={{background:'#333', color:'white', padding:'5px 15px'}}>Logout</button>
            </div>

            {/* Navigare Tab-uri */}
            <div style={{ marginBottom: '20px' }}>
                <button onClick={() => {setActiveTab('users'); setIsEditing(false);}} style={{ marginRight: '10px', fontWeight: activeTab==='users'?'bold':'normal' }}>Manage Users</button>
                <button onClick={() => {setActiveTab('devices'); setIsEditing(false);}} style={{ fontWeight: activeTab==='devices'?'bold':'normal' }}>Manage Devices</button>
            </div>

            {/* --- SECȚIUNEA USERS --- */}
            {activeTab === 'users' && (
                <>
                    <form onSubmit={handleUserSubmit} style={{ padding: '15px', marginBottom: '20px' }}>
                        <h3>{isEditing ? 'Edit User' : 'Add New User'}</h3>
                        <input placeholder="Username" value={userForm.username} onChange={e=>setUserForm({...userForm, username:e.target.value})} required style={{marginRight:5}} />
                        <input placeholder={isEditing ? "New Password (Optional)" : "Password"} value={userForm.password} onChange={e=>setUserForm({...userForm, password:e.target.value})} style={{marginRight:5}} />
                        <select value={userForm.role} onChange={e=>setUserForm({...userForm, role:e.target.value})} style={{marginRight:5}}>
                            <option value="Client">Client</option>
                            <option value="Administrator">Administrator</option>
                        </select>
                        <button type="submit" style={{ background: 'green', color: 'white' }}>{isEditing ? 'Update' : 'Create'}</button>
                        {isEditing && <button type="button" onClick={()=>{setIsEditing(false); setUserForm({id:null, username:'', password:'', role:'Client'})}} style={{marginLeft:10}}>Cancel</button>}
                    </form>

                    <table border="1" cellPadding="5" style={{width:'100%', borderCollapse:'collapse'}}>
                        <thead><tr><th>ID</th><th>Username</th><th>Role</th><th>Actions</th></tr></thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id}>
                                    <td>{u.auth_id}</td><td>{u.username}</td><td>{u.role}</td>
                                    <td>
                                        <button onClick={()=>handleEditUserClick(u)} style={{marginRight:5}}>Edit</button>
                                        <button onClick={()=>deleteItem('users', u.id)} style={{background:'red', color:'white'}}>Delete</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}

            {/* --- SECȚIUNEA DEVICES --- */}
            {activeTab === 'devices' && (
                <>
                     <form onSubmit={handleDeviceSubmit} style={{ padding: '15px', marginBottom: '20px' }}>
                        <h3>{isEditing ? 'Edit Device' : 'Add New Device'}</h3>
                        <input placeholder="Description" value={deviceForm.description} onChange={e=>setDeviceForm({...deviceForm, description:e.target.value})} required style={{marginRight:5}} />
                        <input placeholder="Address" value={deviceForm.address} onChange={e=>setDeviceForm({...deviceForm, address:e.target.value})} required style={{marginRight:5}} />
                        <input type="number" placeholder="Max Cons." value={deviceForm.max_hourly_consumption} onChange={e=>setDeviceForm({...deviceForm, max_hourly_consumption:e.target.value})} required style={{marginRight:5}} />
                        <input type="number" placeholder="Owner ID" value={deviceForm.owner_id || ''} onChange={e=>setDeviceForm({...deviceForm, owner_id:e.target.value})} style={{marginRight:5}} />

                        <button type="submit" style={{ background: 'green', color: 'white' }}>{isEditing ? 'Update' : 'Create'}</button>
                        {isEditing && <button type="button" onClick={()=>{setIsEditing(false); setDeviceForm({id:null, description:'', address:'', max_hourly_consumption:0, owner_id:''})}} style={{marginLeft:10}}>Cancel</button>}
                    </form>

                    <table border="1" cellPadding="5" style={{width:'100%', borderCollapse:'collapse'}}>
                        <thead><tr><th>ID</th><th>Desc</th><th>Addr</th><th>Max</th><th>Owner</th><th>Actions</th></tr></thead>
                        <tbody>
                            {devices.map(d => (
                                <tr key={d.id}>
                                    <td>{d.id}</td><td>{d.description}</td><td>{d.address}</td><td>{d.max_hourly_consumption}</td><td>{d.owner_id}</td>
                                    <td>
                                        <button onClick={()=>handleEditDeviceClick(d)} style={{marginRight:5}}>Edit</button>
                                        <button onClick={()=>deleteItem('devices', d.id)} style={{background:'red', color:'white'}}>Delete</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}
            <ChatComponent userId={user?.id} isAdmin={true} />
        </div>
    );
};
export default AdminDashboard;