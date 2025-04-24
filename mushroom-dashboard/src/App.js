import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer
} from "recharts";
import Chat from "./Chat";
import "./App.css";

const WEBSOCKET_URL = "ws://localhost:8000/ws";
const HISTORY_URL = "http://localhost:8000/history";
const INSIGHT_URL = "http://localhost:8000/insight";
const RUN_INSIGHT_URL = "http://localhost:8000/run_insight";

// Reusable GraphCard component.
const GraphCard = ({ title, dataKey, data }) => {
  const [localRange, setLocalRange] = useState("all");
  const rangeOptions = {
    "1h": 3600000,
    "6h": 6 * 3600000,
    "12h": 12 * 3600000,
    "1d": 24 * 3600000,
    "1w": 7 * 24 * 3600000,
    "1m": 30 * 24 * 3600000
  };

  let filteredData = data;
  if (localRange !== "all" && data.length > 0) {
    const latestTimestamp = new Date(data[data.length - 1].timestamp).getTime();
    const lowerBound = latestTimestamp - rangeOptions[localRange];
    filteredData = data.filter(
      (d) => new Date(d.timestamp).getTime() >= lowerBound
    );
  }

  const formatXAxis = (timeStr) => {
    const date = new Date(timeStr);
    if (localRange === "all") {
      return (
        date.toLocaleDateString([], {
          month: "2-digit",
          day: "2-digit",
          year: "numeric"
        }) +
        " " +
        date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      );
    }
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const formatTooltipLabel = (timeStr) => {
    const date = new Date(timeStr);
    return (
      date.toLocaleDateString([], {
        month: "2-digit",
        day: "2-digit",
        year: "numeric"
      }) +
      " " +
      date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      })
    );
  };

  const strokeColor =
    dataKey === "temperature"
      ? "#f44336"
      : dataKey === "humidity"
      ? "#2196f3"
      : "#4caf50";

  return (
    <div className="graph-card">
      <div className="graph-header">
        <h3>{title} Chart</h3>
        <div className="local-range-selector">
          {["all", "1h", "6h", "12h", "1d", "1w", "1m"].map((range) => (
            <button
              key={range}
              onClick={() => setLocalRange(range)}
              className={localRange === range ? "active" : ""}
            >
              {range}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={filteredData}>
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatXAxis}
            minTickGap={20}
            interval="preserveStartEnd"
          />
          <YAxis
            tickFormatter={(value) =>
              dataKey === "temperature"
                ? `${value}°F`
                : dataKey === "humidity"
                ? `${value}%`
                : `${value} ppm`
            }
          />
          <Tooltip
            labelFormatter={formatTooltipLabel}
            formatter={(value) =>
              dataKey === "temperature"
                ? `${value}°F`
                : dataKey === "humidity"
                ? `${value}%`
                : `${value} ppm`
            }
          />
          <CartesianGrid strokeDasharray="3 3" />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={strokeColor}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const typeWriter = (fullText, delay, callback) => {
  return new Promise((resolve) => {
    let currentText = "";
    let index = 0;
    const intervalId = setInterval(() => {
      if (index < fullText.length) {
        currentText += fullText[index];
        index++;
        callback(currentText);
      } else {
        clearInterval(intervalId);
        resolve(currentText);
      }
    }, delay);
  });
};

const App = () => {
  const [sensorData, setSensorData] = useState([]);
  const [insight, setInsight] = useState({
    historicalSummary: "",
    currentReading: "",
    insight: ""
  });
  const [openGraphs, setOpenGraphs] = useState({
    temperature: false,
    humidity: false,
    CO2: false
  });
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isInsightUpdating, setIsInsightUpdating] = useState(false);

  useEffect(() => {
    fetch(HISTORY_URL)
      .then((res) => res.json())
      .then((data) => setSensorData(data))
      .catch((err) => console.error("Error fetching history:", err));
  }, []);

  useEffect(() => {
    const ws = new WebSocket(WEBSOCKET_URL);
    ws.onopen = () => {
      console.log("✅ WebSocket connected.");
    };
    ws.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      const parsedData = {
        ...newData,
        temperature: Number(newData.temperature),
        humidity: Number(newData.humidity),
        CO2: Number(newData.CO2)
      };
      setSensorData((prevData) => [...prevData, parsedData]);
    };
    ws.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
    };
    ws.onclose = () => {
      console.warn("⚠️ WebSocket closed, attempting to reconnect...");
    };
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 5000);
    return () => {
      clearInterval(pingInterval);
      if (ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, []);

  useEffect(() => {
    fetch(INSIGHT_URL)
      .then((res) => res.json())
      .then((data) => setInsight(data.insight))
      .catch((err) => console.error("Error fetching insight:", err));
  }, []);

  const updateInsightManual = () => {
    setIsInsightUpdating(true);
    fetch(RUN_INSIGHT_URL)
      .then((res) => res.json())
      .then((data) => {
        const newInsight = data.insight;
        Promise.all([
          typeWriter(newInsight.historicalSummary || "", 60, (txt) =>
            setInsight((prev) => ({ ...prev, historicalSummary: txt }))
          ),
          typeWriter(newInsight.currentReading || "", 65, (txt) =>
            setInsight((prev) => ({ ...prev, currentReading: txt }))
          ),
          typeWriter(newInsight.insight || "", 25, (txt) =>
            setInsight((prev) => ({ ...prev, insight: txt }))
          )
        ]).then(() => {
          setIsInsightUpdating(false);
        });
      })
      .catch((err) => {
        console.error("Error updating insight manually:", err);
        setIsInsightUpdating(false);
      });
  };

  const toggleGraph = (variable) => {
    setOpenGraphs((prev) => ({ ...prev, [variable]: !prev[variable] }));
  };

  const toggleChatPanel = () => {
    setIsChatOpen(!isChatOpen);
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🍄 Mushroom Environment Monitor</h1>
        <button className="chat-toggle-button" onClick={toggleChatPanel}>
          {isChatOpen ? "Hide Chat" : "Open Chat"}
        </button>
      </header>
      <div className={`dashboard ${isChatOpen ? "with-chat" : ""}`}>
        {isChatOpen && (
          <div className="chat-panel">
            <Chat />
          </div>
        )}
        <div className="content-panel">
          <div className="sensor-cards">
            <div className="sensor-card temp" onClick={() => toggleGraph("temperature")}>
              <h3>Temperature</h3>
              {sensorData.length > 0 && <p>{sensorData[sensorData.length - 1].temperature}°F</p>}
            </div>
            <div className="sensor-card humidity" onClick={() => toggleGraph("humidity")}>
              <h3>Humidity</h3>
              {sensorData.length > 0 && <p>{sensorData[sensorData.length - 1].humidity}%</p>}
            </div>
            <div className="sensor-card co2" onClick={() => toggleGraph("CO2")}>
              <h3>CO₂ Levels</h3>
              {sensorData.length > 0 && <p>{sensorData[sensorData.length - 1].CO2} ppm</p>}
            </div>
          </div>
          {openGraphs.temperature && (
            <GraphCard title="Temperature" dataKey="temperature" data={sensorData} />
          )}
          {openGraphs.humidity && (
            <GraphCard title="Humidity" dataKey="humidity" data={sensorData} />
          )}
          {openGraphs.CO2 && (
            <GraphCard title="CO₂ Levels" dataKey="CO2" data={sensorData} />
          )}
          {/* Insight Section placed below the charts */}
          <div className="insight-container">
            <h2>Insight</h2>
            <div className="insight-box">
              <h3>Historical Summary</h3>
              <p>{insight.historicalSummary || "Loading..."}</p>
            </div>
            <div className="insight-box">
              <h3>Current Reading</h3>
              <p>{insight.currentReading || "Loading..."}</p>
            </div>
            <div className="insight-box">
              <h3>Analysis</h3>
              <p>{insight.insight || "Loading insight..."}</p>
            </div>
            <button
              className="insight-update-button"
              onClick={updateInsightManual}
              disabled={isInsightUpdating}
            >
              {isInsightUpdating ? "Updating..." : "Update Insight Now"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;