package com.example;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/**
 * ============================================================
 * RepairResponse DTO (ML Output Contract)
 * ============================================================
 *
 * This class represents the structured output returned by
 * the Python-based DNA repair model.
 *
 * It acts as a cross-language data contract between:
 *   - Python inference pipeline (JSON output)
 *   - Java Spring Boot backend (REST response)
 *
 * Design Purpose:
 *   - Ensures consistent serialization/deserialization
 *   - Decouples ML output format from API response model
 *   - Provides structured representation of repair results
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class RepairResponse {

    // --------------------------------------------------------
    // Core ML Output Fields
    // --------------------------------------------------------
    private String  repairedSequence;
    private boolean success;

    private int     inputLen;
    private int     outputLen;
    private int     changes;

    private double  confidence;
    private String  damageType;

    private double  sparsityScore;
    private double  diagConfidence;

    /**
     * Default constructor required for Jackson deserialization.
     * Enables automatic JSON → Java object mapping.
     */
    public RepairResponse() {}

    /**
     * Error-state constructor used when inference fails.
     * Encodes failure as a structured API response.
     */
    public RepairResponse(String errorMsg) {
        this.repairedSequence = errorMsg;
        this.success          = false;
    }

    /**
     * Full success constructor representing a complete model output.
     */
    public RepairResponse(String repairedSequence, boolean success,
                          int inputLen, int outputLen, int changes,
                          double confidence, String damageType,
                          double sparsityScore, double diagConfidence) {

        this.repairedSequence = repairedSequence;
        this.success          = success;
        this.inputLen         = inputLen;
        this.outputLen        = outputLen;
        this.changes          = changes;
        this.confidence       = confidence;
        this.damageType       = damageType;
        this.sparsityScore    = sparsityScore;
        this.diagConfidence   = diagConfidence;
    }

    // --------------------------------------------------------
    // Getters (used by Spring Boot for JSON serialization)
    // --------------------------------------------------------
    public String  getRepairedSequence() { return repairedSequence; }
    public boolean isSuccess()           { return success; }
    public int     getInputLen()         { return inputLen; }
    public int     getOutputLen()        { return outputLen; }
    public int     getChanges()          { return changes; }
    public double  getConfidence()       { return confidence; }
    public String  getDamageType()       { return damageType; }
    public double  getSparsityScore()    { return sparsityScore; }
    public double  getDiagConfidence()   { return diagConfidence; }

    // --------------------------------------------------------
    // Setters (required for Jackson deserialization)
    // --------------------------------------------------------
    public void setRepairedSequence(String v) { this.repairedSequence = v; }
    public void setSuccess(boolean v)         { this.success = v; }
    public void setInputLen(int v)            { this.inputLen = v; }
    public void setOutputLen(int v)           { this.outputLen = v; }
    public void setChanges(int v)             { this.changes = v; }
    public void setConfidence(double v)       { this.confidence = v; }
    public void setDamageType(String v)       { this.damageType = v; }
    public void setSparsityScore(double v)    { this.sparsityScore = v; }
    public void setDiagConfidence(double v)   { this.diagConfidence = v; }
}