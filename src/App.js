import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Configurando ícone personalizado para o marcador
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function App() {
  const [busData, setBusData] = useState([]);
  const [selectedBus, setSelectedBus] = useState(null);

  // Função para buscar os dados de ônibus
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('redis://localhost:6379/0'); // Alterar para a URL da sua API
        setBusData(response.data);
      } catch (error) {
        console.error('Erro ao buscar dados:', error);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="App">
      <h1>Monitoramento de Ônibus</h1>

      {/* Tabela com dados dos ônibus */}
      <table border="1">
        <thead>
          <tr>
            <th>Linha</th>
            <th>Velocidade (km/h)</th>
            <th>Tempo para Ponto</th>
          </tr>
        </thead>
        <tbody>
          {busData.map((bus) => (
            <tr key={bus.id} onClick={() => setSelectedBus(bus)}>
              <td>{bus.line}</td>
              <td>{bus.speed}</td>
              <td>{bus.timeToPoint} min</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Mapa com a posição dos ônibus */}
      <MapContainer center={[-22.9068, -43.1729]} zoom={13} style={{ height: '400px', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />

        {busData.map((bus) => (
          <Marker key={bus.id} position={[bus.latitude, bus.longitude]}>
            <Popup>
              Ônibus {bus.line} - Velocidade: {bus.speed} km/h
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

export default App;
