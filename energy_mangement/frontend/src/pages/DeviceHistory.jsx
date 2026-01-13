import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Line } from 'react-chartjs-2';
import api from '../api/axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const DeviceHistory = () => {
    const { deviceId } = useParams();
    const navigate = useNavigate();

    const [rawData, setRawData] = useState([]);
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(true);

    // viewMode: 'recent' (Last 2h), 'hourly' (Last 24h), 'daily' (All time)
    const [viewMode, setViewMode] = useState('recent');

    // 1. Fetch Data
    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await api.get(`/monitoring/consumption/${deviceId}`);
                setRawData(response.data);
            } catch (error) {
                console.error("Error fetching history", error);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, [deviceId]);

    // 2. Procesare Date
    useEffect(() => {
        if (!rawData.length) return;

        let processedLabels = [];
        let processedValues = [];
        let labelText = '';
        let lineColor = '';

        // Luăm ultimul timestamp disponibil ca referință ("Acum")
        const lastRecord = rawData[rawData.length - 1];
        const lastTimestamp = lastRecord.timestamp;

        if (viewMode === 'recent') {
            // --- MODUL RECENT (Last 2 Hours, interval 10 min) ---
            labelText = 'Consumption (Last 2 Hours)';
            lineColor = 'rgb(75, 192, 192)'; // Turcoaz

            const twoHoursAgo = lastTimestamp - (2 * 60 * 60 * 1000);
            const recentData = rawData.filter(r => r.timestamp >= twoHoursAgo);

            processedLabels = recentData.map(record => {
                const date = new Date(record.timestamp);
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            });
            processedValues = recentData.map(record => record.total_consumption);

        } else if (viewMode === 'hourly') {
            // --- MODUL ORAR (Last 24 Hours, agregat pe oră) ---
            labelText = 'Hourly Consumption (Last 24 Hours)';
            lineColor = 'rgb(54, 162, 235)'; // Albastru

            // 1. Calculăm fereastra de 24h
            const twentyFourHoursAgo = lastTimestamp - (24 * 60 * 60 * 1000);

            // 2. Filtrăm doar datele din ultima zi
            const lastDayData = rawData.filter(r => r.timestamp >= twentyFourHoursAgo);

            // 3. Agregăm datele filtrate pe ore
            const hourlyGroups = {};
            lastDayData.forEach(record => {
                const date = new Date(record.timestamp);
                date.setMinutes(0, 0, 0);
                const key = date.getTime();

                if (!hourlyGroups[key]) hourlyGroups[key] = 0;
                hourlyGroups[key] += record.total_consumption;
            });

            const sortedKeys = Object.keys(hourlyGroups).sort();
            processedLabels = sortedKeys.map(timestamp => {
                return new Date(parseInt(timestamp)).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            });
            processedValues = sortedKeys.map(key => hourlyGroups[key]);

        } else if (viewMode === 'daily') {
            // --- MODUL ZILNIC (Tot istoricul, agregat pe zi) ---
            labelText = 'Total Daily Consumption (All Time)';
            lineColor = 'rgb(255, 99, 132)'; // Roșu

            const dailyGroups = {};
            rawData.forEach(record => {
                const date = new Date(record.timestamp);
                date.setHours(0, 0, 0, 0);
                const key = date.getTime();

                if (!dailyGroups[key]) dailyGroups[key] = 0;
                dailyGroups[key] += record.total_consumption;
            });

            const sortedKeys = Object.keys(dailyGroups).sort();
            processedLabels = sortedKeys.map(timestamp => {
                return new Date(parseInt(timestamp)).toLocaleDateString();
            });
            processedValues = sortedKeys.map(key => dailyGroups[key]);
        }

        setChartData({
            labels: processedLabels,
            datasets: [
                {
                    label: labelText,
                    data: processedValues,
                    borderColor: lineColor,
                    backgroundColor: lineColor.replace('rgb', 'rgba').replace(')', ', 0.5)'),
                    tension: 0.3,
                    pointRadius: 5,
                },
            ],
        });

    }, [rawData, viewMode]);

    const btnStyle = (mode) => ({
        padding: '10px 20px',
        marginRight: '10px',
        cursor: 'pointer',
        border: 'none',
        borderRadius: '5px',
        background: viewMode === mode ? '#007BFF' : '#e0e0e0',
        color: viewMode === mode ? 'white' : 'black',
        fontWeight: 'bold',
        transition: 'all 0.3s ease'
    });

    if (loading) return <div style={{ padding: '20px' }}>Loading chart data...</div>;

    return (
        <div style={{ padding: '20px', width: '100%', boxSizing: 'border-box' }}>
            <button
                onClick={() => navigate('/client')}
                style={{ marginBottom: '20px', padding: '8px 15px', cursor: 'pointer', border: '1px solid #ccc', borderRadius: '4px' }}
            >
                &larr; Back to Devices
            </button>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
                <h2 style={{ margin: '0 20px 10px 0' }}>Device History (ID: {deviceId})</h2>

                <div>
                    <button style={btnStyle('recent')} onClick={() => setViewMode('recent')}>
                        Last 2 Hours
                    </button>
                    <button style={btnStyle('hourly')} onClick={() => setViewMode('hourly')}>
                        Last 24 Hours
                    </button>
                    <button style={btnStyle('daily')} onClick={() => setViewMode('daily')}>
                        Daily (All)
                    </button>
                </div>
            </div>

            <div style={{ width: '95%', height: '600px', margin: '0 auto', background: '#fff', padding: '15px', boxShadow: '0 4px 15px rgba(0,0,0,0.1)', borderRadius: '10px' }}>
                {chartData && chartData.labels.length > 0 ? (
                    <Line
                        data={chartData}
                        options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { position: 'top' },
                                title: { display: true, text: 'Energy Consumption Overview' },
                            },
                            scales: {
                                y: { beginAtZero: true, title: { display: true, text: 'kWh' } }
                            }
                        }}
                    />
                ) : (
                    <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#666' }}>
                        <p>No data available. Ensure Simulator is running.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DeviceHistory;