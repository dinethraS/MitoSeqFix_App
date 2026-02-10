import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [dnaInput, setDnaInput] = useState("");
  const [fileInput, setFileInput] = useState(null);
  const [repaired, setRepaired] = useState("");
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();

    reader.onload = (e) => {
      const text = e.target.result;
      const seq = text.split("\n").slice(1).join("").replace(/\s/g, "");
      setDnaInput(seq);
      setFileInput(file.name);
    };

    reader.readAsText(file);
  };

  const handleRepair = async () => {
    if (!dnaInput) return;

    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8080/api/repair", {
        sequence: dnaInput
      });

      if (res.data.success) {
        setRepaired(res.data.repaired);

        setStats({
          inputLen: res.data.inputLen,
          outputLen: res.data.outputLen,
          changes: res.data.changes,
          confidence: res.data.confidence
        });
      }
    } catch {
      setRepaired("Error connecting to backend");
    }

    setLoading(false);
  };

  const downloadFasta = () => {
    const fasta = `>repaired_${Date.now()}\n${repaired}`;

    const blob = new Blob([fasta], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "repaired_mtdna.fasta";
    a.click();
  };

  return (
    <div className="App">
      <h1>MitoSeqFix</h1>

      <input type="file" accept=".fasta,.fa,.txt" onChange={handleFileUpload} />
      <p>{fileInput || "Or paste sequence below"}</p>

      <textarea
        value={dnaInput}
        onChange={(e) => setDnaInput(e.target.value)}
        rows={6}
        cols={70}
      />

      <br />

      <button onClick={handleRepair} disabled={loading}>
        {loading ? "Repairing..." : "Repair DNA"}
      </button>

      <h3>Results</h3>

      <p>
        Input: {stats.inputLen} | Output: {stats.outputLen} | Changes:{stats.changes}
      </p>

      <textarea value={repaired} readOnly rows={6} cols={70} />

      <br />
      <button onClick={downloadFasta}>Download FASTA</button>
    </div>
  );
}

export default App;
