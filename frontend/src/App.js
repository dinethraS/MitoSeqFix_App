/**
 * ============================================================
 * MitoSeqFix Frontend Application (React UI Layer)
 * ============================================================
 *
 * This component represents the user-facing interface of the
 * MitoSeqFix system.
 *
 * Architectural Role:
 *   - Acts as the Presentation Layer in a 3-tier architecture:
 *       1. React Frontend (this file)
 *       2. Spring Boot REST API
 *       3. Python ML Inference Engine
 *
 * Responsibilities:
 *   - DNA sequence input (manual + file upload)
 *   - Client-side validation
 *   - API communication with backend
 *   - Visualization of repair results
 *   - Interactive comparison of original vs repaired sequence
 */

import React, { useState } from "react";
import axios from "axios";
import "./App.css";

// ─────────────────────────────────────────────────────────────
// Input Validation Utilities
// ─────────────────────────────────────────────────────────────

/**
 * Validates DNA sequence format.
 * Ensures biological correctness before API submission.
 */
const isValidDna = (seq) => {
  if (!seq) return false;
  const clean = seq.trim().replace(/\s/g, "");

  // Minimum length constraint ensures meaningful inference input
  if (clean.length < 70) return false;

  // Only valid nucleotide characters are allowed
  return /^[ATCGNatcgn\-]+$/.test(clean);
};

/**
 * Converts sparsity score into qualitative severity label.
 */
const sparsityLabel = (score) => {
  if (score >= 0.55) return "HIGH";
  if (score >= 0.30) return "MODERATE";
  return "LOW";
};

/**
 * Maps sparsity score to CSS classification class
 * for UI severity highlighting.
 */
const sparsityClass = (score) => {
  if (score >= 0.55) return "sev-high";
  if (score >= 0.30) return "sev-moderate";
  return "sev-low";
};

// ─────────────────────────────────────────────────────────────
// Main Application Component
// ─────────────────────────────────────────────────────────────

function App() {

  // ── Input State ───────────────────────────────────────────
  const [dnaInput, setDnaInput] = useState("");
  const [fileInput, setFileInput] = useState(null);

  // ── Model Output State ─────────────────────────────────────
  const [repaired, setRepaired] = useState("");
  const [stats, setStats] = useState({
    inputLen: 0,
    outputLen: 0,
    changes: 0,
    confidence: 0,      // gate-based repair confidence
    damageType: "",
    sparsityScore: 0,   // proportion of missing bases
    diagConfidence: 0,  // classification confidence
  });

  // ── UI State ──────────────────────────────────────────────
  const [validationError, setValidationError] = useState("");
  const [loading, setLoading] = useState(false);
  const [copyStatus, setCopyStatus] = useState("Copy");
  const [showModal, setShowModal] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [activeTab, setActiveTab] = useState("sequence");

  // ─────────────────────────────────────────────────────────
  // Client-side validation handler
  // Prevents invalid or too-short sequences from reaching backend
  // ─────────────────────────────────────────────────────────
  const handleTextChange = (e) => {
    const value = e.target.value;
    setDnaInput(value);

    const clean = value.trim().replace(/\s/g, "");

    if (clean.length > 0 && !isValidDna(value)) {
      setValidationError(
        clean.length < 70
          ? `Sequence too short (${clean.length}/70 bp).`
          : "Invalid characters detected. Only A, T, C, G, N allowed."
      );
    } else {
      setValidationError("");
    }
  };

  // ─────────────────────────────────────────────────────────
  // File Upload Handler (FASTA input support)
  // ─────────────────────────────────────────────────────────
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = (ev) => {
      const seq = ev.target.result
        .split("\n")
        .filter((l) => !l.startsWith(">")) // remove FASTA headers
        .join("")
        .replace(/\s/g, "");

      setDnaInput(seq);
      setFileInput(file.name);
      setValidationError(seq.length < 70 ? "Uploaded sequence is too short (<70 bp)." : "");
    };

    reader.readAsText(file);
  };

  // ─────────────────────────────────────────────────────────
  // API Call: DNA Repair Request
  // ─────────────────────────────────────────────────────────
  const handleRepair = async () => {
    if (!dnaInput || validationError) return;

    setLoading(true);
    setRepaired("");
    setActiveTab("sequence");

    try {
      const res = await axios.post("http://localhost:8080/api/repair", {
        sequence: dnaInput.trim().replace(/\s/g, ""),
      });

      if (res.data.success) {
        setRepaired(res.data.repairedSequence);

        // Map backend response to UI state model
        setStats({
          inputLen: res.data.inputLen,
          outputLen: res.data.outputLen,
          changes: res.data.changes,
          confidence: res.data.confidence,
          damageType: res.data.damageType,
          sparsityScore: res.data.sparsityScore,
          diagConfidence: res.data.diagConfidence,
        });
      }
    } catch (err) {
      console.error("Repair failed", err);
      alert("Failed to connect to backend.");
    }

    setLoading(false);
  };

  // ─────────────────────────────────────────────────────────
  // Reset Application State
  // ─────────────────────────────────────────────────────────
  const handleClear = () => {
    setDnaInput("");
    setFileInput(null);
    setRepaired("");
    setStats({
      inputLen: 0,
      outputLen: 0,
      changes: 0,
      confidence: 0,
      damageType: "",
      sparsityScore: 0,
      diagConfidence: 0,
    });
    setValidationError("");
    setShowModal(false);
    setShowAll(false);
    setActiveTab("sequence");
  };

  // ─────────────────────────────────────────────────────────
  // Clipboard Utility (result export support)
  // ─────────────────────────────────────────────────────────────
  const copyToClipboard = () => {
    navigator.clipboard.writeText(repaired);
    setCopyStatus("Copied!");
    setTimeout(() => setCopyStatus("Copy"), 2000);
  };

  // ─────────────────────────────────────────────────────────
  // Export repaired sequence as FASTA file
  // ─────────────────────────────────────────────────────────────
  const handleDownload = () => {
    const blob = new Blob([`>MitoSeqFix_Restored\n${repaired}`], {
      type: "text/plain",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "restored_mtDNA.fasta";
    link.click();

    URL.revokeObjectURL(url);
  };

  // UI rendering continues unchanged...
}

export default App;