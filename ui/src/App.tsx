import React, {useEffect} from 'react';
import './App.css';

function App() {
  useEffect(() => {
    const logEventSource = new EventSource('/api/event-log');
    logEventSource.onmessage = (event) => {
        const logEntry = JSON.parse(event.data);
        console.log(logEntry);
    };

    return () => logEventSource.close();
  }, []);
  return (
    <div className="App">
    </div>
  );
}

export default App;
